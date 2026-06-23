"""Fuzzy "did you mean" matching against the canonical 5e.tools name catalog.

Voice transcription and typos rarely produce the exact entity name
("Tosha's laughter" → "Tasha's Hideous Laughter").  This module loads the
bundled name catalog, merges in any names from the user's live local
libraries, and resolves a noisy query to the closest real name.

Pure logic — no Tk, no GSM imports — so it can be unit-tested directly.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

_INDEX_PATH = Path(__file__).parent / "data" / "names_index.json"

# Pure-stdlib fuzzy matching (difflib) — no native extension, so it packages
# cleanly for Android (Chaquopy) without a compiled wheel. Replaces rapidfuzz.

_APOS = re.compile(r"[’'`]")
_NONWORD = re.compile(r"[^a-z0-9]+")


def _norm(s: str) -> str:
    """Lowercase, drop apostrophes (so "Tasha's" → "tashas"), other punctuation → space."""
    s = _APOS.sub("", (s or "").lower())
    return _NONWORD.sub(" ", s).strip()


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# Scoring (in NameMatcher._scored) averages two signals, each 0–1:
#   • whole — token-sorted whole-string ratio (typos + word reordering)
#   • per   — per-query-token best-match average (partial phrases / missing words,
#             e.g. "tosha's laughter" → "Tasha's Hideous Laughter")
# The whole half breaks ties toward the closest overall name, so "firebal" prefers
# "Fireball" over "Delayed Blast Fireball". Approximates the old rapidfuzz behaviour.


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
        # Precompute normalized forms once (not per query) for speed over a big catalog.
        self._tokens: dict[str, list[str]] = {}
        self._sorted: dict[str, str] = {}
        self._chars: dict[str, set] = {}
        for n in self._names:
            nn = _norm(n)
            toks = nn.split()
            self._tokens[n] = toks
            self._sorted[n] = " ".join(sorted(toks))
            self._chars[n] = set(nn.replace(" ", ""))

    def __len__(self) -> int:
        return len(self._names)

    def _result(self, name: str, score: float) -> MatchResult:
        return MatchResult(name, self._category.get(name, ""), score, self._source.get(name, ""))

    def _scored(self, query: str, score_cutoff: float) -> list[tuple[str, float]]:
        """All names clearing the cutoff, sorted best-first. A cheap char-overlap prefilter
        skips obviously-unrelated names; SequenceMatcher objects index the query side once
        and reuse it across candidates, with quick_ratio upper bounds pruning the costly
        full ratio() in the per-token loop."""
        qn = _norm(query)
        qt = qn.split()
        if not qt or not self._names:
            return []
        qchars = set(qn.replace(" ", ""))
        need = max(1, len(qchars) // 2)   # candidate must share ~half the query's letters

        sm_whole = SequenceMatcher(autojunk=False)
        sm_whole.set_seq2(" ".join(sorted(qt)))
        tok_sms = []
        for w in qt:
            sm = SequenceMatcher(autojunk=False)
            sm.set_seq2(w)
            tok_sms.append(sm)

        out: list[tuple[str, float]] = []
        for name in self._names:
            if len(qchars & self._chars[name]) < need:
                continue
            ctoks = self._tokens[name]
            if not ctoks:
                continue
            sm_whole.set_seq1(self._sorted[name])
            whole = sm_whole.ratio()
            total = 0.0
            for sm in tok_sms:
                best = 0.0
                for x in ctoks:
                    sm.set_seq1(x)
                    if sm.real_quick_ratio() <= best or sm.quick_ratio() <= best:
                        continue   # cheap upper bounds can't beat the current best → skip
                    r = sm.ratio()
                    if r > best:
                        best = r
                total += best
            sc = (0.5 * whole + 0.5 * (total / len(qt))) * 100.0
            if sc >= score_cutoff:
                out.append((name, sc))
        out.sort(key=lambda ns: ns[1], reverse=True)
        return out

    def best(self, query: str, score_cutoff: float = 60.0) -> MatchResult | None:
        """Closest single match, or None if nothing clears `score_cutoff`."""
        scored = self._scored(query, score_cutoff)
        return self._result(*scored[0]) if scored else None

    def suggestions(
        self, query: str, limit: int = 5, score_cutoff: float = 45.0
    ) -> list[MatchResult]:
        """Ranked candidate matches for a 'Did you mean…' picker."""
        return [self._result(n, s) for n, s in self._scored(query, score_cutoff)[:limit]]


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
