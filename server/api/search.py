"""Fuzzy search over the 5e.tools catalog + the local spell library."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from rapidfuzz import fuzz, process, utils

from search import links
from search.matcher import build_matcher
from server import state as app_state

bp = Blueprint("search", __name__, url_prefix="/api/search")

_matcher = None  # built lazily from the bundled catalog (≈6.5k names)


def _matcher_instance():
    global _matcher
    if _matcher is None:
        _matcher = build_matcher()
    return _matcher


@bp.get("")
def search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"suggestions": [], "local": []})

    suggestions = [
        {"name": r.name, "category": r.category, "source": r.source,
         "url": links.url_for(r.name, r.category, r.source)}
        for r in _matcher_instance().suggestions(q, limit=12)
    ]

    # Local spell library fuzzy matches.
    local = []
    lib = app_state.STATE.spell_library
    if lib:
        names = [s.get("name", "") for s in lib]
        hits = process.extract(q, names, scorer=fuzz.token_sort_ratio,
                               processor=utils.default_process, limit=8, score_cutoff=55)
        local = [lib[idx] for _name, _score, idx in hits]

    return jsonify({"suggestions": suggestions, "local": local})
