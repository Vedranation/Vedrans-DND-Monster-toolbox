"""Tests for the 5e.tools deep-link builder (search/links.py)."""

from search.links import url_for


def test_simple_spell_link():
    assert url_for("Fireball", "spell", "PHB") == "https://5e.tools/spells.html#fireball_phb"


def test_multiword_name_spaces_encoded():
    assert (
        url_for("Hunger of Hadar", "spell", "PHB")
        == "https://5e.tools/spells.html#hunger%20of%20hadar_phb"
    )


def test_apostrophe_stays_literal():
    # encodeURIComponent leaves apostrophes untouched — so must we.
    url = url_for("Tasha's Hideous Laughter", "spell", "PHB")
    assert url == "https://5e.tools/spells.html#tasha's%20hideous%20laughter_phb"


def test_category_page_mapping():
    assert url_for("Goblin", "monster", "MM").startswith("https://5e.tools/bestiary.html#")
    assert url_for("Bag of Holding", "item", "DMG").startswith("https://5e.tools/items.html#")
    assert url_for("Grappler", "feat", "PHB").startswith("https://5e.tools/feats.html#")


def test_unknown_category_returns_none():
    assert url_for("Whatever", "background", "PHB") is None


def test_missing_source_returns_none():
    # Homebrew with no 5e.tools source can't be deep-linked.
    assert url_for("Vedran's Wild Bolt", "spell", "") is None
