"""Spell library CRUD + 5etools import, and spellcasters (level → slots, spells)."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from engine.tables import SPELL_SLOTS_BY_LEVEL
from persistence.import_5etools_spell import parse_5etools_spell
from server import state as app_state

bp = Blueprint("spells", __name__, url_prefix="/api")


# ── spell library ─────────────────────────────────────────────────────────────

@bp.get("/spell-library")
def list_spells():
    return jsonify({"spells": app_state.STATE.spell_library})


@bp.post("/spell-library")
def add_spell():
    s = app_state.STATE
    spell = request.get_json(silent=True) or {}
    if not (spell.get("name") or "").strip():
        abort(400, "Spell name is required.")
    s.spell_library.append(spell)
    return jsonify({"spells": s.spell_library}), 201


@bp.put("/spell-library/<int:idx>")
def update_spell(idx: int):
    s = app_state.STATE
    if not (0 <= idx < len(s.spell_library)):
        abort(404)
    s.spell_library[idx] = request.get_json(silent=True) or {}
    return jsonify({"spells": s.spell_library})


@bp.delete("/spell-library/<int:idx>")
def delete_spell(idx: int):
    s = app_state.STATE
    if not (0 <= idx < len(s.spell_library)):
        abort(404)
    s.spell_library.pop(idx)
    return jsonify({"spells": s.spell_library})


@bp.post("/spell-library/import-5etools")
def import_spell():
    s = app_state.STATE
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        abort(400, "Expected a single 5etools spell JSON object.")
    spell = parse_5etools_spell(body)
    # Update in place if the name already exists, else append.
    for i, existing in enumerate(s.spell_library):
        if existing.get("name") == spell["name"]:
            s.spell_library[i] = spell
            break
    else:
        s.spell_library.append(spell)
    return jsonify({"spells": s.spell_library, "name": spell["name"]}), 201


# ── casters ───────────────────────────────────────────────────────────────────

def _caster_dict(c: dict) -> dict:
    table = SPELL_SLOTS_BY_LEVEL.get(c["level"], [])
    slots = {str(i): {"max": mx, "used": c["slots_used"].get(str(i), 0)}
             for i, mx in enumerate(table, start=1)}
    return {"id": c["id"], "name": c["name"], "level": c["level"],
            "spells": c["spells"], "slots": slots, "token_id": c.get("token_id")}


def _find_caster(s, cid):
    return next((c for c in s.casters if c["id"] == cid), None)


@bp.get("/casters")
def list_casters():
    return jsonify({"casters": [_caster_dict(c) for c in app_state.STATE.casters]})


@bp.post("/casters")
def add_caster():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    s._caster_seq += 1
    c = {"id": f"c{s._caster_seq}", "name": (body.get("name") or "Caster").strip(),
         "level": int(body.get("level", 1)), "spells": {}, "slots_used": {}, "token_id": None}
    s.casters.append(c)
    return jsonify(_caster_dict(c)), 201


@bp.post("/casters/<cid>/duplicate")
def duplicate_caster(cid: str):
    """Spawn a copy of this caster (name/level/spells/slots) but left unlinked."""
    s = app_state.STATE
    src = _find_caster(s, cid)
    if src is None:
        abort(404)
    s._caster_seq += 1
    c = {"id": f"c{s._caster_seq}", "name": f"{src['name']} (copy)",
         "level": src["level"], "spells": {lvl: list(names) for lvl, names in src["spells"].items()},
         "slots_used": dict(src["slots_used"]), "token_id": None}
    s.casters.append(c)
    return jsonify(_caster_dict(c)), 201


@bp.patch("/casters/<cid>")
def update_caster(cid: str):
    s = app_state.STATE
    c = _find_caster(s, cid)
    if c is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    if "name" in body:
        c["name"] = body["name"]
    if "level" in body:
        c["level"] = max(1, min(20, int(body["level"])))
    if "token_id" in body:
        c["token_id"] = body["token_id"] or None
    return jsonify(_caster_dict(c))


@bp.delete("/casters/<cid>")
def delete_caster(cid: str):
    s = app_state.STATE
    s.casters = [c for c in s.casters if c["id"] != cid]
    return jsonify({"casters": [_caster_dict(c) for c in s.casters]})


@bp.post("/casters/<cid>/spells")
def add_caster_spell(cid: str):
    s = app_state.STATE
    c = _find_caster(s, cid)
    if c is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    level = str(body.get("level", 1))
    name = body.get("name", "")
    bucket = c["spells"].setdefault(level, [])
    if name and name not in bucket:
        bucket.append(name)
    return jsonify(_caster_dict(c))


@bp.delete("/casters/<cid>/spells")
def remove_caster_spell(cid: str):
    s = app_state.STATE
    c = _find_caster(s, cid)
    if c is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    level = str(body.get("level", 1))
    name = body.get("name", "")
    if level in c["spells"]:
        c["spells"][level] = [n for n in c["spells"][level] if n != name]
    return jsonify(_caster_dict(c))


@bp.post("/casters/<cid>/cast")
def cast_slot(cid: str):
    """Expend one slot of the given spell level (clamped to max)."""
    s = app_state.STATE
    c = _find_caster(s, cid)
    if c is None:
        abort(404)
    body = request.get_json(silent=True) or {}
    level = int(body.get("level", 1))
    table = SPELL_SLOTS_BY_LEVEL.get(c["level"], [])
    mx = table[level - 1] if 1 <= level <= len(table) else 0
    used = c["slots_used"].get(str(level), 0)
    c["slots_used"][str(level)] = min(mx, used + (1 if body.get("restore") is not True else -1))
    c["slots_used"][str(level)] = max(0, c["slots_used"][str(level)])
    return jsonify(_caster_dict(c))


@bp.post("/casters/<cid>/reset-slots")
def reset_slots(cid: str):
    s = app_state.STATE
    c = _find_caster(s, cid)
    if c is None:
        abort(404)
    c["slots_used"] = {}
    return jsonify(_caster_dict(c))
