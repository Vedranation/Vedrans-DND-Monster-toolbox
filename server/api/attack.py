"""Single-attack roll endpoint — mirrors the desktop Attack tab."""

from __future__ import annotations

from dataclasses import asdict, replace

from flask import Blueprint, abort, jsonify, request

from engine.combat import compute_single_attack, format_damage_breakdown, typed_damage_parts
from engine.models import PlayerData
from server import state as app_state

bp = Blueprint("attack", __name__, url_prefix="/api")


def _defender_data(s, defender_id) -> PlayerData:
    """Player → own data; monster → adapted defense view; else AC-0 dummy.

    imposed_roll_type is always Normal because "Roll with" (override) is the sole
    authority over the roll type on this screen.
    """
    if defender_id and defender_id in s.players:
        return replace(s.players[defender_id], imposed_roll_type="Normal")
    if defender_id and defender_id in s.monsters:
        md = s.monsters[defender_id]
        return PlayerData(name=md.name, ac=md.ac, max_hp=md.max_hp, imposed_roll_type="Normal")
    return PlayerData(ac=0)


@bp.post("/roll-attack")
def roll_attack():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}

    attacker_id = body.get("attacker_id")
    if attacker_id not in s.monsters:
        abort(404, "Unknown attacker.")
    monster = s.monsters[attacker_id]

    override = body.get("override_roll_type", "Normal")
    indices = body.get("attack_indices")
    if indices is None:
        indices = list(range(len(monster.attacks)))
    chosen = [replace(monster.attacks[i], roll_type=override)
              for i in indices if 0 <= i < len(monster.attacks)]

    if not chosen:
        return jsonify({"rolls": [], "breakdown": "0", "breakdown_parts": [], "total": 0})

    single = replace(monster, attacks=chosen)
    defender = _defender_data(s, body.get("defender_id"))

    result = compute_single_attack(single, defender, s.combat)
    total = sum(r.dmg1 + r.dmg2 for r in result.rolls if r.is_hit)
    return jsonify({
        "attacker": monster.name,
        "defender": defender.name,
        "override_roll_type": override,
        "rolls": [asdict(r) for r in result.rolls],
        "breakdown": format_damage_breakdown(result.rolls),
        "breakdown_parts": typed_damage_parts(result.rolls),  # raw (no resistances on this screen)
        "total": total,
    })
