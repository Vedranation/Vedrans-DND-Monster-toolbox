"""Core endpoints: constants (for dropdowns) and the full state snapshot."""

from __future__ import annotations

from flask import Blueprint, jsonify

from engine import constants
from server import state as app_state

bp = Blueprint("core", __name__, url_prefix="/api")


@bp.get("/constants")
def get_constants():
    return jsonify({
        "roll_types": constants.ROLL_TYPES,
        "dmg_types": constants.DMG_TYPES,
        "dice_types": constants.DICE_TYPES,
        "saving_throw_types": constants.SAVING_THROW_TYPES,
        "creature_types": constants.CREATURE_TYPES,
        "creature_sizes": constants.CREATURE_SIZES,
        "conditions": constants.ALL_CONDITIONS,
        "spell_schools": constants.SPELL_SCHOOLS,
        "skills": constants.SKILLS,
        "all_skills": constants.ALL_SKILLS,
    })


@bp.get("/state")
def get_state():
    return jsonify(app_state.snapshot(app_state.STATE))
