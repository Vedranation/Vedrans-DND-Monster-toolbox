"""Fuzzy search over the 5e.tools catalog + the local spell library."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from search import links
from search.matcher import NameMatcher, build_matcher
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

    # Local spell library fuzzy matches (small list → build a matcher on the fly).
    local = []
    lib = app_state.STATE.spell_library
    if lib:
        lib_matcher = NameMatcher([(s.get("name", ""), "spell") for s in lib])
        by_name = {s.get("name", ""): s for s in lib}
        for r in lib_matcher.suggestions(q, limit=8, score_cutoff=55):
            if r.name in by_name:
                local.append(by_name[r.name])

    return jsonify({"suggestions": suggestions, "local": local})
