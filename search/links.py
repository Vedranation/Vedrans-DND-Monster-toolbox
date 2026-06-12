"""Build 5e.tools deep-link URLs for catalog entries.

5e.tools is a single-page app addressable by URL hash, e.g.
``https://5e.tools/spells.html#hunger%20of%20hadar_phb``. Opening that link in
the user's real default browser lands directly on the entry — no Selenium, no
automation fingerprint, no Cloudflare challenge.
"""

from __future__ import annotations

from urllib.parse import quote

_BASE = "https://5e.tools/"

# Category → list page on 5e.tools.
_PAGE = {
    "spell": "spells.html",
    "monster": "bestiary.html",
    "item": "items.html",
    "feat": "feats.html",
}

# Characters encodeURIComponent leaves untouched — mirror it so the hash matches
# what 5e.tools generates (apostrophes stay literal, spaces become %20).
_HASH_SAFE = "!~*'()-_."


def url_for(name: str, category: str, source: str) -> str | None:
    """Deep-link URL for a catalog entry, or None if the category/source is unknown."""
    page = _PAGE.get(category)
    if not page or not name or not source:
        return None
    hash_part = f"{quote(name.lower(), safe=_HASH_SAFE)}_{source.lower()}"
    return f"{_BASE}{page}#{hash_part}"
