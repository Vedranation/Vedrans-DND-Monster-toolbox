"""Preset save / load / list / delete — schema-v2, desktop-compatible files."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, request

from persistence.preset import delete_preset, list_presets, load_preset, save_preset
from server import state as app_state

bp = Blueprint("presets", __name__, url_prefix="/api/presets")


@bp.get("")
def list_all():
    return jsonify({"presets": list_presets()})


@bp.post("")
def save():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        abort(400, "Preset name is required.")
    save_preset(name, app_state.state_to_preset_data(app_state.STATE))
    return jsonify({"ok": True, "name": name, "presets": list_presets()})


@bp.get("/<name>")
def load(name: str):
    try:
        data = load_preset(name)
    except FileNotFoundError:
        abort(404, f"No preset named {name!r}.")
    app_state.apply_preset_data(app_state.STATE, data)
    return jsonify(app_state.snapshot(app_state.STATE))


@bp.delete("/<name>")
def delete(name: str):
    delete_preset(name)
    return jsonify({"ok": True, "presets": list_presets()})
