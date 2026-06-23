"""Battle board: tokens + teams. (Targeting/inference + resolve land in 3b.)"""

from __future__ import annotations

from dataclasses import asdict

from flask import Blueprint, abort, jsonify, request

from engine.board import GridPosition, Team, distance_ft, is_flanking, ranged_in_melee
from engine.combat import compute_single_attack, resolve_typed_damage, typed_damage_parts
from engine.inference import (
    compute_roll_type_modifiers,
    flanking_to_hit_bonus,
    perceives_invisible,
    roll_type_sources,
)
from engine.models import PlayerData
from server import state as app_state

bp = Blueprint("board", __name__, url_prefix="/api/board")

# Cycled when adding new teams (mirrors the desktop palette).
_TEAM_PALETTE = ["#3a6ea5", "#a53a3a", "#3a8a4a", "#8a6a2a", "#6a3a8a", "#2a8a8a", "#a53a7a", "#555555"]


@bp.get("")
def get_board():
    return jsonify(app_state.board_dict(app_state.STATE))


# ── tokens ───────────────────────────────────────────────────────────────────

@bp.post("/tokens")
def add_token():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    if kind not in ("monster", "player"):
        abort(400, "kind must be 'monster' or 'player'.")
    tok = app_state.add_board_token(s, kind, body.get("ref_id"), body.get("col"), body.get("row"))
    if tok is None:
        abort(404, "Unknown roster entry.")
    return jsonify(app_state.token_dict(tok)), 201


@bp.post("/tokens/add-all")
def add_all_tokens():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    if kind not in ("monster", "player"):
        abort(400, "kind must be 'monster' or 'player'.")
    roster = s.monsters if kind == "monster" else s.players
    added = [app_state.add_board_token(s, kind, rid) for rid in list(roster.keys())]
    return jsonify([app_state.token_dict(t) for t in added if t]), 201


@bp.patch("/tokens/<tid>")
def patch_token(tid: str):
    s = app_state.STATE
    t = app_state.token_by_id(s, tid)
    if t is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    if "col" in body and "row" in body:
        t.pos.col = max(0, min(s.board.width - 1, int(body["col"])))
        t.pos.row = max(0, min(s.board.height - 1, int(body["row"])))
    if "hp" in body:
        t.hp = int(body["hp"])
        if t.max_hp > 0:
            t.hp = max(0, min(t.max_hp, t.hp))
        else:
            t.hp = max(0, t.hp)
        if t.hp == 0 and s.auto_disable_zero_hp:
            t.active = False
    if "active" in body:
        t.active = bool(body["active"])
    if "team" in body:
        t.team = str(body["team"])
    if "conditions" in body:
        t.conditions = app_state.conditions_from_values(body["conditions"])
    return jsonify(app_state.token_dict(t))


@bp.delete("/tokens/<tid>")
def delete_token(tid: str):
    s = app_state.STATE
    before = len(s.board.tokens)
    s.board.tokens = [t for t in s.board.tokens if t.id != tid]
    if len(s.board.tokens) == before:
        abort(404)
    return "", 204


@bp.post("/clear")
def clear_board():
    s = app_state.STATE
    s.board.tokens.clear()
    s.target_overrides.clear()
    return jsonify(app_state.board_dict(s))


@bp.post("/clear-deactivated")
def clear_deactivated():
    s = app_state.STATE
    s.board.tokens = [t for t in s.board.tokens if t.active]
    return jsonify(app_state.board_dict(app_state.STATE))


# ── teams ────────────────────────────────────────────────────────────────────

@bp.post("/teams")
def add_team():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name or any(tm.name == name for tm in s.board.teams):
        abort(400, "Team name must be non-empty and unique.")
    color = body.get("color") or _TEAM_PALETTE[len(s.board.teams) % len(_TEAM_PALETTE)]
    s.board.teams.append(Team(name, color))
    return jsonify(app_state.board_dict(s))


@bp.patch("/teams/<name>")
def update_team(name: str):
    s = app_state.STATE
    team = next((tm for tm in s.board.teams if tm.name == name), None)
    if team is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    if "color" in body:
        team.color = body["color"]
    if "new_name" in body:
        new = (body["new_name"] or "").strip()
        if not new or any(tm.name == new for tm in s.board.teams if tm is not team):
            abort(400, "New team name must be non-empty and unique.")
        for t in s.board.tokens:
            if t.team == team.name:
                t.team = new
        team.name = new
    return jsonify(app_state.board_dict(s))


@bp.delete("/teams/<name>")
def delete_team(name: str):
    s = app_state.STATE
    if len(s.board.teams) <= 1:
        abort(400, "Can't delete the last team.")
    if not any(tm.name == name for tm in s.board.teams):
        abort(404)
    fallback = next(tm.name for tm in s.board.teams if tm.name != name)
    for t in s.board.tokens:
        if t.team == name:
            t.team = fallback
    s.board.teams = [tm for tm in s.board.teams if tm.name != name]
    return jsonify(app_state.board_dict(s))


# ── targeting / inference / resolve ───────────────────────────────────────────

def _monster_data(s, name):
    return next((m for m in s.monsters.values() if m.name == name), None)


def _player_data(s, name):
    return next((p for p in s.players.values() if p.name == name), None)


def _auto_target(board, m_token):
    """Nearest active enemy-team token, honoring block range mode (mirrors the desktop)."""
    enemies = [t for t in board.tokens if t.team != m_token.team and t.active]
    if not enemies:
        return None
    enemies.sort(key=lambda t: distance_ft(m_token.pos, t.pos, board.diagonal_mode))
    if board.range_mode == "block":
        in_range = [t for t in enemies
                    if distance_ft(m_token.pos, t.pos, board.diagonal_mode) <= m_token.attack_range_ft]
        return in_range[0] if in_range else None
    return enemies[0]


def _resolve_target(s, m_token):
    """Manual override if still valid (active enemy), else the auto-target."""
    over_id = s.target_overrides.get(m_token.id)
    if over_id:
        ot = app_state.token_by_id(s, over_id)
        if ot and ot.active and ot.team != m_token.team:
            return ot
    return _auto_target(s.board, m_token)


# Conditions that make a creature helpless → attacks from within 5 ft auto-crit (5e).
_HELPLESS = {"paralyzed", "unconscious"}


def _auto_crit(attacker, target, board) -> bool:
    """True if attacker is within 5 ft of a paralyzed/unconscious target (auto-crit)."""
    if target is None:
        return False
    tconds = {c.value for c in target.conditions}
    return bool(_HELPLESS & tconds) and \
        distance_ft(attacker.pos, target.pos, board.diagonal_mode) <= 5


def _nearest_enemy(t, board):
    """Nearest active enemy-team token (for the inspector's roll-type explanation)."""
    enemies = [e for e in board.tokens if e.team != t.team and e.active and e is not t]
    if not enemies:
        return None
    return min(enemies, key=lambda e: distance_ft(t.pos, e.pos, board.diagonal_mode))


def _defender_view(s, token):
    """(PlayerData for the combat engine, resistances, immunities, vulnerabilities)."""
    if token.kind == "player":
        pd = _player_data(s, token.data_ref)
        return (pd or PlayerData(ac=13)), [], [], []
    md = _monster_data(s, token.data_ref)
    if md is None:
        return PlayerData(ac=13), [], [], []
    view = PlayerData(name=md.name, ac=md.ac, max_hp=md.max_hp)
    return view, md.damage_resistances, md.damage_immunities, md.damage_vulnerabilities


@bp.get("/targets")
def targets():
    """Target lines for all active monsters → their auto-target (for drawing arrows)."""
    s = app_state.STATE
    b = s.board
    lines = []
    for mt in b.tokens:
        if not mt.active or mt.kind != "monster":
            continue
        tgt = _resolve_target(s, mt)
        if tgt is None:
            continue
        dist = distance_ft(mt.pos, tgt.pos, b.diagonal_mode)
        lines.append({"from_id": mt.id, "to_id": tgt.id, "in_range": dist <= mt.attack_range_ft})
    return jsonify({"lines": lines})


def _attack_dict(atk) -> dict:
    """Structured attack for the inspector: counts, to-hit, and the two damage parts."""
    def part(n_die, die, flat, dtype):
        if n_die <= 0 and flat == 0:
            return None
        if dtype in ("", "None"):
            return None
        return {"n_die": n_die, "die": die, "flat": flat, "type": dtype}
    return {
        "n": atk.n_attacks, "name": atk.name, "to_hit": atk.to_hit_mod,
        "dmg1": part(atk.dmg_n_die_1, atk.dmg_die_type_1, atk.dmg_flat_1, atk.dmg_type_1),
        "dmg2": part(atk.dmg_n_die_2, atk.dmg_die_type_2, atk.dmg_flat_2, atk.dmg_type_2),
    }


def _token_panel(s, t) -> dict:
    """At-a-glance inspector data for a single selected token."""
    b = s.board
    # Roll-type matchup: monsters vs their resolved target, others vs nearest enemy.
    tgt = _resolve_target(s, t) if t.kind == "monster" else _nearest_enemy(t, b)
    adv, dis = roll_type_sources(t, tgt, b) if tgt else ([], [])
    # Does this token perceive an invisible matchup target (blindsight/truesight)?
    sees_invis = bool(tgt) and "invisible" in {c.value for c in tgt.conditions} \
        and perceives_invisible(t, tgt, b)
    panel = {
        "name": t.data_ref, "kind": t.kind, "team": t.team,
        "hp": t.hp, "max_hp": t.max_hp,
        "conditions": sorted(c.value for c in t.conditions),
        "attack_range_ft": t.attack_range_ft,
        "roll_type": compute_roll_type_modifiers(t, tgt, b, s.combat.adv_mode, s.combat.adv_combine) if tgt else "Normal",
        "adv_sources": adv, "disadv_sources": dis,
        "auto_crit": (t.kind == "monster" and _auto_crit(t, tgt, b)),
        "is_helpless": bool(_HELPLESS & {c.value for c in t.conditions}),
        "sees_invisible": sees_invis,
        "ac": None, "speeds": {}, "senses": {}, "attacks": [],
        "resistances": [], "immunities": [], "vulnerabilities": [], "condition_immunities": [],
        "skills": [], "languages": [],
    }
    if t.kind == "monster":
        md = _monster_data(s, t.data_ref)
        if md is not None:
            panel["ac"] = md.ac
            panel["speeds"] = {k: v for k, v in md.speeds.items() if v}
            panel["senses"] = {k: v for k, v in md.senses.items() if v}
            panel["attacks"] = [_attack_dict(a) for a in md.attacks]
            panel["resistances"] = list(md.damage_resistances)
            panel["immunities"] = list(md.damage_immunities)
            panel["vulnerabilities"] = list(md.damage_vulnerabilities)
            panel["condition_immunities"] = sorted(md.condition_immunities)
            panel["skills"] = sorted([name, mod] for name, (mod, _rt) in md.skills.items())
            panel["languages"] = list(md.languages)
    else:
        pd = _player_data(s, t.data_ref)
        if pd is not None:
            panel["ac"] = pd.ac
    return panel


@bp.get("/inference/<tid>")
def inference(tid: str):
    """Highlights + roll info + inspector panel for one selected token."""
    s = app_state.STATE
    b = s.board
    t = app_state.token_by_id(s, tid)
    if t is None:
        abort(404)
    range_cells = [
        [c, r]
        for r in range(b.height) for c in range(b.width)
        if distance_ft(t.pos, GridPosition(c, r), b.diagonal_mode) <= t.highlight_range_ft
    ]
    flanked = [e.id for e in b.tokens
               if e.team != t.team and e.active and is_flanking(t, e, b)]
    tgt = _resolve_target(s, t) if t.kind == "monster" else None
    roll_mod = compute_roll_type_modifiers(t, tgt, b, s.combat.adv_mode, s.combat.adv_combine) if tgt else "Normal"
    return jsonify({
        "range_cells": range_cells,
        "flanked_ids": flanked,
        "target_id": tgt.id if tgt else None,
        "target_in_range": (tgt is not None and
                            distance_ft(t.pos, tgt.pos, b.diagonal_mode) <= t.attack_range_ft),
        "roll_mod": roll_mod,
        "in_melee": ranged_in_melee(t, b),
        "panel": _token_panel(s, t),
    })


@bp.post("/resolve")
def resolve():
    """Resolve every active monster's attack against its auto-target."""
    s = app_state.STATE
    b = s.board
    pairs, skipped = [], []
    for mt in b.tokens:
        if not mt.active or mt.kind != "monster":
            continue
        am = _monster_data(s, mt.data_ref)
        tgt = _resolve_target(s, mt)
        if am is None or tgt is None:
            skipped.append(mt.data_ref)
            continue
        dist = distance_ft(mt.pos, tgt.pos, b.diagonal_mode)
        if b.range_mode == "block" and dist > mt.attack_range_ft:
            skipped.append(mt.data_ref)
            continue
        ddata, resist, immune, vuln = _defender_view(s, tgt)
        board_mod = compute_roll_type_modifiers(mt, tgt, b, s.combat.adv_mode, s.combat.adv_combine)
        tohit_bonus = flanking_to_hit_bonus(mt, tgt, b)
        force_crit = _auto_crit(mt, tgt, b)
        result = compute_single_attack(am, ddata, s.combat,
                                       board_tohit_bonus=tohit_bonus, board_roll_type_mod=board_mod,
                                       force_crit_on_hit=force_crit)
        if s.ignore_resistances:
            resist = immune = vuln = []
        applied, breakdown = resolve_typed_damage(result.rolls, resist, immune, vuln)
        pairs.append({
            "attacker_id": mt.id, "attacker": am.name,
            "defender_id": tgt.id, "defender": ddata.name,
            "roll_mod": board_mod, "tohit_bonus": tohit_bonus, "auto_crit": force_crit,
            "out_of_range": dist > mt.attack_range_ft,
            "rolls": [asdict(r) for r in result.rolls],
            "breakdown": breakdown,
            "breakdown_parts": typed_damage_parts(result.rolls, resist, immune, vuln),
            "applied": applied,
            "defender_hp": tgt.hp, "defender_max_hp": tgt.max_hp,
        })
    return jsonify({"pairs": pairs, "skipped": skipped})


@bp.post("/apply-damage")
def apply_damage():
    """Body: {applies: [{token_id, amount}]} — reduce HP, auto-disable at 0."""
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    for entry in body.get("applies", []):
        t = app_state.token_by_id(s, entry.get("token_id"))
        if t is None:
            continue
        t.hp = max(0, t.hp - int(entry.get("amount", 0)))
        if t.hp == 0 and s.auto_disable_zero_hp:
            t.active = False
    return jsonify(app_state.board_dict(s))


@bp.post("/retarget")
def retarget():
    """Cycle target(s) for the selected monster(s), mirroring the desktop R hotkey.

    Body: {token_ids: [...], primary_id} (or {token_id} for a single token).
    Single selection cycles candidates by distance from the monster, honoring block
    mode (only in-range targets; reports `blocked` if none reachable). Multi-selection
    orders candidates by distance from the group's average position, assigns the SAME
    target to all selected monsters, and in block mode silently skips those that can't
    individually reach it.
    """
    s = app_state.STATE
    b = s.board
    body = request.get_json(silent=True) or {}
    ids = body.get("token_ids") or ([body["token_id"]] if body.get("token_id") else [])
    primary_id = body.get("primary_id") or (ids[-1] if ids else None)
    primary = app_state.token_by_id(s, primary_id)
    if primary is None or primary.kind != "monster":
        abort(400, "Select a monster to retarget.")

    sel = [t for tid in ids
           if (t := app_state.token_by_id(s, tid)) is not None and t.kind == "monster" and t.active]
    is_multi = len(sel) > 1

    enemies = [t for t in b.tokens if t.team != primary.team and t.active]
    if not enemies:
        for t in (sel or [primary]):
            s.target_overrides.pop(t.id, None)
        return jsonify({"target_id": None, "blocked": False})

    if is_multi:
        avg = GridPosition(round(sum(t.pos.col for t in sel) / len(sel)),
                           round(sum(t.pos.row for t in sel) / len(sel)))
        ordered = sorted(enemies, key=lambda t: distance_ft(avg, t.pos, b.diagonal_mode))
    else:
        ordered = sorted(enemies, key=lambda t: distance_ft(primary.pos, t.pos, b.diagonal_mode))
        if b.range_mode == "block":
            ordered = [t for t in ordered
                       if distance_ft(primary.pos, t.pos, b.diagonal_mode) <= primary.attack_range_ft]
            if not ordered:
                return jsonify({"target_id": None, "blocked": True})

    cur = _resolve_target(s, primary)
    order_ids = [t.id for t in ordered]
    idx = order_ids.index(cur.id) if (cur and cur.id in order_ids) else -1
    chosen = ordered[(idx + 1) % len(ordered)]

    if is_multi:
        for t in sel:
            if b.range_mode == "block" and \
               distance_ft(t.pos, chosen.pos, b.diagonal_mode) > t.attack_range_ft:
                continue
            s.target_overrides[t.id] = chosen.id
    else:
        s.target_overrides[primary.id] = chosen.id

    return jsonify({"target_id": chosen.id, "blocked": False})
