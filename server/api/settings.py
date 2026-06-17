"""Settings (combat rules + board settings) get/update."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from server import state as app_state

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.get("")
def get_settings():
    return jsonify(app_state.settings_dict(app_state.STATE))


@bp.put("")
def update_settings():
    body = request.get_json(silent=True) or {}
    app_state.apply_settings(app_state.STATE, body)
    return jsonify(app_state.settings_dict(app_state.STATE))
