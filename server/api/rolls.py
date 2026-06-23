"""Bulk dice rolls: mass monster saves, quick save, party skill check, fumble."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from engine import dice
from engine.combat import roll_to_hit
from engine.constants import DICE_TYPES
from engine.tables import FUMBLE_TABLE
from server import state as app_state

bp = Blueprint("rolls", __name__, url_prefix="/api/rolls")


def _d20(roll_type: str) -> int:
    return roll_to_hit(roll_type)[0]  # the kept die


@bp.post("/mass-saves")
def mass_saves():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    save = body.get("save", "STR")
    dc = int(body.get("dc", 10))
    override = body.get("roll_type", "Monster default")
    results, total_pass, total = [], 0, 0
    for g in body.get("groups", []):
        m = s.monsters.get(g.get("monster_id"))
        count = int(g.get("count", 0))
        if m is None or count <= 0:
            continue
        mod, monster_rt = m.saving_throws.get(save, (0, "Normal"))
        rt = monster_rt if override == "Monster default" else override
        rolls, passes = [], 0
        for _ in range(count):
            d = _d20(rt)
            ok = d + mod >= dc
            rolls.append({"d20": d, "total": d + mod, "pass": ok})
            passes += ok
        results.append({"name": m.name, "count": count, "modifier": mod, "roll_type": rt,
                        "passes": passes, "fails": count - passes, "rolls": rolls})
        total_pass += passes
        total += count
    return jsonify({"results": results, "total_pass": total_pass, "total": total, "dc": dc})


@bp.post("/quick-save")
def quick_save():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    m = s.monsters.get(body.get("monster_id"))
    if m is None:
        abort(404, "Unknown monster.")
    save = body.get("save", "STR")
    override = body.get("roll_type", "Monster default")
    mod, monster_rt = m.saving_throws.get(save, (0, "Normal"))
    rt = monster_rt if override == "Monster default" else override
    d, all_d20s = roll_to_hit(rt)
    return jsonify({"monster": m.name, "save": save, "roll_type": rt,
                    "d20": d, "d20s": all_d20s, "modifier": mod, "total": d + mod,
                    "is_nat1": d == 1, "is_nat20": d == 20})


@bp.post("/monster-skill-check")
def monster_skill_check():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    m = s.monsters.get(body.get("monster_id"))
    if m is None:
        abort(404, "Unknown monster.")
    skill = (body.get("skill") or "perception").lower()
    override = body.get("roll_type", "Monster default")
    mod, monster_rt = m.skills.get(skill, (0, "Normal"))
    rt = monster_rt if override == "Monster default" else override
    d, all_d20s = roll_to_hit(rt)
    return jsonify({"monster": m.name, "skill": skill, "roll_type": rt,
                    "d20": d, "d20s": all_d20s, "modifier": mod, "total": d + mod,
                    "is_nat1": d == 1, "is_nat20": d == 20})


@bp.post("/mass-skill-check")
def mass_skill_check():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    skill = (body.get("skill") or "perception").lower()
    dc = int(body.get("dc", 10))
    override = body.get("roll_type", "Monster default")
    results, total_pass, total = [], 0, 0
    for g in body.get("groups", []):
        m = s.monsters.get(g.get("monster_id"))
        count = int(g.get("count", 0))
        if m is None or count <= 0:
            continue
        mod, monster_rt = m.skills.get(skill, (0, "Normal"))
        rt = monster_rt if override == "Monster default" else override
        rolls, passes = [], 0
        for _ in range(count):
            d = _d20(rt)
            ok = d + mod >= dc
            rolls.append({"d20": d, "total": d + mod, "pass": ok})
            passes += ok
        results.append({"name": m.name, "count": count, "modifier": mod, "roll_type": rt,
                        "passes": passes, "fails": count - passes, "rolls": rolls})
        total_pass += passes
        total += count
    return jsonify({"results": results, "total_pass": total_pass, "total": total, "dc": dc})


@bp.post("/party-skill-check")
def party_skill_check():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    skill = (body.get("skill") or "perception").lower()
    dc = int(body.get("dc", 15))
    results = []
    for p in s.players.values():
        mod, rt = p.skills.get(skill, (0, "Normal"))
        d = _d20(rt)
        total = d + mod
        status = "Nat1" if d == 1 else "Nat20" if d == 20 else ("Passed" if total >= dc else "Failed")
        results.append({"name": p.name, "d20": d, "modifier": mod, "total": total, "status": status})
    return jsonify({"results": results, "skill": skill, "dc": dc})


@bp.post("/fumble")
def fumble():
    return jsonify({"result": dice.choice(FUMBLE_TABLE)})


@bp.post("/dice")
def roll_dice():
    """Generic dice roll. Body: {count, die, modifier}. (Spells will point here later.)"""
    body = request.get_json(silent=True) or {}
    die = body.get("die", "d20")
    if die not in DICE_TYPES:
        die = "d20"
    count = max(1, min(100, int(body.get("count", 1))))
    mod = int(body.get("modifier", 0))
    rolls = [dice.roll_die(die) for _ in range(count)]
    return jsonify({"die": die, "count": count, "modifier": mod,
                    "rolls": rolls, "sum": sum(rolls), "total": sum(rolls) + mod})
