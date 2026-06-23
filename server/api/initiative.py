"""Initiative tracker — manual entries + quick-add from rosters + roll-all."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from engine.initiative import roll_initiative
from server import state as app_state

bp = Blueprint("initiative", __name__, url_prefix="/api/initiative")


def _sorted(s):
    return sorted(s.initiative, key=lambda e: e["initiative"], reverse=True)


def _payload(s):
    return jsonify({"entries": _sorted(s)})


def _add(s, name, initiative, mod, is_player):
    s._init_seq += 1
    s.initiative.append({
        "id": f"i{s._init_seq}", "name": name, "initiative": int(initiative),
        "mod": int(mod), "is_player": bool(is_player), "is_active": True,
    })


@bp.get("")
def list_entries():
    return _payload(app_state.STATE)


@bp.post("/entry")
def add_entry():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip() or "Combatant"
    _add(s, name, body.get("initiative", 0), body.get("mod", 0), body.get("is_player", False))
    return _payload(s)


@bp.patch("/entry/<eid>")
def update_entry(eid: str):
    s = app_state.STATE
    e = next((x for x in s.initiative if x["id"] == eid), None)
    if e is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    if "name" in body:
        e["name"] = body["name"]
    if "initiative" in body:
        e["initiative"] = int(body["initiative"])
    if "is_active" in body:
        e["is_active"] = bool(body["is_active"])
    return _payload(s)


@bp.delete("/entry/<eid>")
def delete_entry(eid: str):
    s = app_state.STATE
    s.initiative = [x for x in s.initiative if x["id"] != eid]
    return _payload(s)


@bp.post("/quick-add")
def quick_add():
    """Add every monster and player from the rosters, rolling initiative for each."""
    s = app_state.STATE
    for p in s.players.values():
        _add(s, p.name, roll_initiative(p.initiative_mod), p.initiative_mod, True)
    for m in s.monsters.values():
        _add(s, m.name, roll_initiative(m.initiative_mod), m.initiative_mod, False)
    return _payload(s)


@bp.post("/roll-all")
def roll_all():
    """Re-roll initiative (d20 + stored mod) for every entry."""
    s = app_state.STATE
    for e in s.initiative:
        e["initiative"] = roll_initiative(e["mod"])
    return _payload(s)


@bp.post("/clear")
def clear():
    app_state.STATE.initiative.clear()
    return _payload(app_state.STATE)
