"""Tests for the fuzzy name matcher (search/matcher.py)."""

from search.matcher import NameMatcher, build_matcher, load_index

_ENTRIES = [
    ("Tasha's Hideous Laughter", "spell", "PHB"),
    ("Hunger of Hadar", "spell", "PHB"),
    ("Fireball", "spell", "PHB"),
    ("Fire Bolt", "spell", "PHB"),
    ("Conjure Woodland Beings", "spell", "PHB"),
    ("Ghoul", "monster", "MM"),
    ("Adult Red Dragon", "monster", "MM"),
    ("Bag of Holding", "item", "DMG"),
]


def _matcher() -> NameMatcher:
    return NameMatcher(_ENTRIES)


def test_misheard_name_resolves():
    m = _matcher()
    result = m.best("tosha's laughter")
    assert result is not None
    assert result.name == "Tasha's Hideous Laughter"
    assert result.category == "spell"


def test_typo_resolves():
    m = _matcher()
    assert m.best("fierball").name == "Fireball"


def test_partial_phrase_resolves():
    m = _matcher()
    assert m.best("hunger of hadr").name == "Hunger of Hadar"


def test_category_is_reported():
    m = _matcher()
    assert m.best("gohul").category == "monster"


def test_garbage_returns_none():
    m = _matcher()
    assert m.best("zzzxqq wphbbl", score_cutoff=60) is None


def test_suggestions_are_ranked_and_capped():
    m = _matcher()
    sugg = m.suggestions("fire", limit=3)
    assert len(sugg) <= 3
    # Scores should be sorted descending
    scores = [s.score for s in sugg]
    assert scores == sorted(scores, reverse=True)
    names = {s.name for s in sugg}
    assert names & {"Fireball", "Fire Bolt"}


def test_source_is_reported():
    m = _matcher()
    assert m.best("hunger of hadar").source == "PHB"


def test_dedup_keeps_first_category():
    m = NameMatcher([("Light", "spell", "PHB"), ("Light", "item", "DMG")])
    assert len(m) == 1
    best = m.best("light")
    assert best.category == "spell"
    assert best.source == "PHB"


def test_extra_names_fold_in():
    # A homebrew spell not present in the (empty) index still resolves.
    m = build_matcher(extra=[("Vedran's Wild Bolt", "spell")], index={})
    res = m.best("vedrans wild bolt")
    assert res.name == "Vedran's Wild Bolt"
    assert res.source == ""  # homebrew has no 5e.tools source


def test_empty_query_returns_none():
    m = _matcher()
    assert m.best("") is None
    assert m.suggestions("   ") == []


# ── bundled catalog smoke tests ────────────────────────────────────────────────

def test_bundled_index_loads():
    index = load_index()
    assert index, "bundled names_index.json should be present"
    assert len(index.get("spell", {})) > 300
    assert "Hunger of Hadar" in index["spell"]
    assert index["spell"]["Hunger of Hadar"]  # has a source code


def test_bundled_matcher_resolves_obscure_spell():
    m = build_matcher()
    assert m.best("hunger of hadar").name == "Hunger of Hadar"
    assert m.best("tashas hideous laughter").name == "Tasha's Hideous Laughter"
