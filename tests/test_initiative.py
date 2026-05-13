"""Tests for engine/initiative.py."""

from unittest.mock import patch

import pytest

from engine.initiative import InitiativeEntry, roll_initiative, sort_entries


class TestInitiativeEntry:
    def test_defaults_to_active(self):
        e = InitiativeEntry(name="Goblin", initiative=12, is_player=False)
        assert e.is_active is True

    def test_player_flag(self):
        e = InitiativeEntry(name="Hero", initiative=15, is_player=True)
        assert e.is_player is True

    def test_can_set_inactive(self):
        e = InitiativeEntry(name="Goblin", initiative=12, is_player=False, is_active=False)
        assert not e.is_active


class TestSortEntries:
    def test_sorted_descending(self):
        entries = [
            InitiativeEntry("A", 5, False),
            InitiativeEntry("B", 18, True),
            InitiativeEntry("C", 12, False),
        ]
        result = sort_entries(entries)
        assert [e.name for e in result] == ["B", "C", "A"]

    def test_single_entry(self):
        entries = [InitiativeEntry("Only", 10, False)]
        result = sort_entries(entries)
        assert result[0].name == "Only"

    def test_empty_list(self):
        assert sort_entries([]) == []

    def test_does_not_mutate_original(self):
        entries = [
            InitiativeEntry("A", 5, False),
            InitiativeEntry("B", 18, True),
        ]
        original_first = entries[0].name
        sort_entries(entries)
        assert entries[0].name == original_first  # original unchanged

    def test_equal_initiatives_preserved(self):
        entries = [
            InitiativeEntry("A", 10, False),
            InitiativeEntry("B", 10, True),
        ]
        result = sort_entries(entries)
        assert len(result) == 2
        assert all(e.initiative == 10 for e in result)


class TestRollInitiative:
    def test_with_zero_mod(self):
        with patch("engine.dice.roll_die", return_value=15):
            assert roll_initiative(0) == 15

    def test_with_positive_mod(self):
        with patch("engine.dice.roll_die", return_value=10):
            assert roll_initiative(3) == 13

    def test_with_negative_mod(self):
        with patch("engine.dice.roll_die", return_value=10):
            assert roll_initiative(-2) == 8
