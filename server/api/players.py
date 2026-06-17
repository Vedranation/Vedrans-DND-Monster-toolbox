"""Player CRUD."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from engine.models import PlayerData
from persistence.appstate import deserialize_player
from server import state as app_state

bp = Blueprint("players", __name__, url_prefix="/api/players")


@bp.get("")
def list_players():
    s = app_state.STATE
    return jsonify([app_state.player_entry(pid, p) for pid, p in s.players.items()])


@bp.post("")
def create_player():
    s = app_state.STATE
    body = request.get_json(silent=True) or {}
    data = deserialize_player(body) if body else PlayerData()
    pid = s.add_player(data)
    return jsonify(app_state.player_entry(pid, data)), 201


@bp.get("/<pid>")
def get_player(pid: str):
    s = app_state.STATE
    if pid not in s.players:
        abort(404)
    return jsonify(app_state.player_entry(pid, s.players[pid]))


@bp.put("/<pid>")
def update_player(pid: str):
    s = app_state.STATE
    if pid not in s.players:
        abort(404)
    body = request.get_json(silent=True) or {}
    s.players[pid] = deserialize_player(body)
    return jsonify(app_state.player_entry(pid, s.players[pid]))


@bp.delete("/<pid>")
def delete_player(pid: str):
    s = app_state.STATE
    if pid not in s.players:
        abort(404)
    del s.players[pid]
    return "", 204
