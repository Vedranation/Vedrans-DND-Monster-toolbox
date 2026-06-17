"""Monster CRUD + 5etools import."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from engine.models import MonsterData
from persistence.appstate import deserialize_monster
from persistence.import_5etools import parse_5etools_monster
from server import state as app_state

bp = Blueprint("monsters", __name__, url_prefix="/api/monsters")


@bp.get("")
def list_monsters():
    s = app_state.STATE
    return jsonify([app_state.monster_entry(mid, m) for mid, m in s.monsters.items()])


@bp.post("")
def create_monster():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    data = deserialize_monster(body) if body else MonsterData()
    mid = s.add_monster(data)
    return jsonify(app_state.monster_entry(mid, data)), 201


@bp.get("/<mid>")
def get_monster(mid: str):
    s = app_state.STATE
    if mid not in s.monsters:
        abort(404)
    return jsonify(app_state.monster_entry(mid, s.monsters[mid]))


@bp.put("/<mid>")
def update_monster(mid: str):
    s = app_state.STATE
    if mid not in s.monsters:
        abort(404)
    body = request.get_json(silent=True) or {}
    s.monsters[mid] = deserialize_monster(body)
    return jsonify(app_state.monster_entry(mid, s.monsters[mid]))


@bp.delete("/<mid>")
def delete_monster(mid: str):
    s = app_state.STATE
    if mid not in s.monsters:
        abort(404)
    del s.monsters[mid]
    return "", 204


@bp.post("/import-5etools")
def import_5etools():
    """Body: a raw 5etools monster JSON object."""
    s = app_state.STATE
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        abort(400, "Expected a 5etools monster JSON object.")
    data = parse_5etools_monster(body)
    mid = s.add_monster(data)
    return jsonify(app_state.monster_entry(mid, data)), 201
