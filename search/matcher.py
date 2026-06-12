"""Fuzzy "did you mean" matching against the canonical 5e.tools name catalog.

Voice transcription and typos rarely produce the exact entity name
("Tosha's laughter" → "Tasha's Hideous Laughter").  This module loads the
bundled name catalog, merges in any names from the user's live local
libraries, and resolves a noisy query to the closest real name.

Pure logic — no Tk, no GSM imports — so it can be unit-tested directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz, process, utils

_INDEX_PATH = Path(__file__).parent / "data" / "names_index.json"

# token_sort_ratio handles word reordering and ignores token order, and (unlike
# WRatio) doesn't inflate short single-word names against long multi-word
# queries — so "conjer woodland beans" resolves to "Conjure Woodland Beings"
# rather than "Wand". See tests/test_search_matcher.py.
_SCORER = fuzz.token_sort_ratio

# default_process lowercases and normalises punctuation on both query and
# candidates, so matching is case-insensitive ("Armor" == "armor").
_PROCESSOR = utils.default_process


@dataclass(frozen=True)
class MatchResult:
    name: str        # canonical name, e.g. "Tasha's Hideous Laughter"
    category: str    # "spell" | "monster" | "item" | "feat" | ...
    score: float     # 0–100 similarity
    source: str = "" # 5e.tools source code, e.g. "PHB" (for deep-linking)


def load_index(path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load the bundled {category: {name: source}} catalog. Returns {} if missing."""
    path = path or _INDEX_PATH
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _iter_entries(mapping) -> list[tuple[str, str]]:
    """Normalise a category mapping to (name, source) pairs.

    Accepts the current {name: source} dict form or the legacy [name, ...] list.
    """
    if isinstance(mapping, dict):
        return list(mapping.items())
    return [(name, "") for name in mapping]


class NameMatcher:
    """Fuzzy matcher over (name, category, source) entries."""

    def __init__(self, entries: list[tuple]):
        # De-duplicate on name, preserving the first category/source seen.
        self._category: dict[str, str] = {}
        self._source: dict[str, str] = {}
        for entry in entries:
            name, category = entry[0], entry[1]
            source = entry[2] if len(entry) > 2 else ""
            if name not in self._category:
                self._category[name] = category
                self._source[name] = source
        self._names: list[str] = list(self._category.keys())

    def __len__(self) -> int:
        return len(self._names)

    def _result(self, name: str, score: float) -> MatchResult:
        return MatchResult(name, self._category.get(name, ""), score, self._source.get(name, ""))

    def best(self, query: str, score_cutoff: float = 60.0) -> MatchResult | None:
        """Closest single match, or None if nothing clears `score_cutoff`."""
        query = (query or "").strip()
        if not query or not self._names:
            return None
        hit = process.extractOne(
            query, self._names, scorer=_SCORER, processor=_PROCESSOR, score_cutoff=score_cutoff
        )
        if hit is None:
            return None
        name, score, _ = hit
        return self._result(name, score)

    def suggestions(
        self, query: str, limit: int = 5, score_cutoff: float = 45.0
    ) -> list[MatchResult]:
        """Ranked candidate matches for a 'Did you mean…' picker."""
        query = (query or "").strip()
        if not query or not self._names:
            return []
        hits = process.extract(
            query, self._names, scorer=_SCORER, processor=_PROCESSOR,
            limit=limit, score_cutoff=score_cutoff,
        )
        return [self._result(n, s) for n, s, _ in hits]


def build_matcher(
    extra: list[tuple] | None = None,
    index: dict[str, dict[str, str]] | None = None,
) -> NameMatcher:
    """Build a matcher from the bundled catalog plus optional live names.

    `extra` lets callers fold in names from the user's local libraries
    (e.g. homebrew spells) as (name, category[, source]) tuples; listed first,
    they win on category/source.
    """
    index = index if index is not None else load_index()
    entries: list[tuple] = list(extra or [])
    for category, mapping in index.items():
        entries.extend((name, category, source) for name, source in _iter_entries(mapping))
    return NameMatcher(entries)
