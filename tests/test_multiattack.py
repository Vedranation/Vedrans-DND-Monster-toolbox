"""Tests for heterogeneous multiattack sequences (Phase 4)."""

from unittest.mock import patch

import pytest

from engine.combat import CombatSettings, compute_single_attack
from engine.models import AttackSpec, MonsterData, PlayerData

TARGET_AC15 = PlayerData(ac=15)
DEFAULT_SETTINGS = CombatSettings()


def _multi(*atk_kwargs_list) -> MonsterData:
    return MonsterData(attacks=[AttackSpec(**kw) for kw in atk_kwargs_list])


# ─── heterogeneous sequences ──────────────────────────────────────────────────


class TestHeterogeneousAttacks:
    def test_two_distinct_attacks_produce_two_hits(self):
        # claw (d6) and bite (d8), both guaranteed to hit
        monster = _multi(
            {"n_attacks": 1, "to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
            {"n_attacks": 1, "to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d8"},
        )
        with patch("engine.dice.roll_die", side_effect=[10, 3, 10, 5]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert len(result.hits) == 2
        assert result.dmgs1 == [3, 5]

    def test_2_claws_1_bite(self):
        # mixed n_attacks: claw×2 then bite×1 → 3 total rolls
        monster = _multi(
            {"n_attacks": 2, "to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
            {"n_attacks": 1, "to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d8"},
        )
        with patch("engine.dice.roll_die", side_effect=[10, 2, 10, 4, 10, 6]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert len(result.hits) == 3
        assert result.dmgs1 == [2, 4, 6]

    def test_empty_attacks_list_produces_nothing(self):
        monster = MonsterData(attacks=[])
        result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.hits == []
        assert result.dmgs1 == []
        assert result.dmgs2 == []

    def test_single_spec_n_attacks_still_works(self):
        monster = MonsterData(attacks=[AttackSpec(n_attacks=3, to_hit_mod=100, dmg_n_die_1=1, dmg_die_type_1="d6")])
        with patch("engine.dice.roll_die", side_effect=[10, 1, 10, 2, 10, 3]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert len(result.hits) == 3
        assert result.dmgs1 == [1, 2, 3]


# ─── per-spec crit numbers ────────────────────────────────────────────────────


class TestPerSpecCritNumbers:
    def test_first_spec_crits_at_19_second_does_not(self):
        # spec1: crit_number=19, spec2: crit_number=20 — both roll 19
        monster = _multi(
            {"n_attacks": 1, "crit_number": 19, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
            {"n_attacks": 1, "crit_number": 20, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
        )
        with patch("engine.dice.roll_die", side_effect=[19, 4, 19, 4]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert str(result.hits[0]).startswith("crit")
        assert isinstance(result.hits[1], int)  # 19+0=19>15 → normal hit, not crit

    def test_independent_roll_types_per_spec(self):
        # spec1: Advantage, spec2: Normal — verify two d20 rolls for first, one for second
        monster = _multi(
            {"n_attacks": 1, "roll_type": "Advantage", "to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
            {"n_attacks": 1, "roll_type": "Normal", "to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
        )
        # Advantage: roll 2 d20 (max=12), then 1 dmg; Normal: roll 1 d20, then 1 dmg
        with patch("engine.dice.roll_die", side_effect=[8, 12, 3, 10, 5]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert len(result.hits) == 2  # both hit (to_hit_mod=100)


# ─── dmg_type and save_info come from first spec ──────────────────────────────


class TestAttackResultMetadata:
    def test_dmg_type_from_first_spec(self):
        monster = _multi(
            {"to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d6", "dmg_type_1": "fire"},
            {"to_hit_mod": 100, "dmg_n_die_1": 1, "dmg_die_type_1": "d6", "dmg_type_1": "cold"},
        )
        with patch("engine.dice.roll_die", side_effect=[10, 3, 10, 4]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.dmg_type_1 == "fire"  # from first spec

    def test_save_info_from_first_spec(self):
        monster = _multi(
            {"to_hit_mod": 100, "on_hit_force_save": True, "on_hit_save_dc": 14,
             "on_hit_save_type": "DEX", "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
            {"to_hit_mod": 100, "on_hit_force_save": False,
             "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
        )
        with patch("engine.dice.roll_die", side_effect=[10, 3, 10, 4]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.save_info == (True, 14, "DEX")

    def test_empty_attacks_returns_default_metadata(self):
        monster = MonsterData(attacks=[])
        result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.dmg_type_1 == "slashing"  # AttackSpec default
        assert result.save_info[0] is False


# ─── persistence roundtrip ────────────────────────────────────────────────────


class TestAttacksSerialisation:
    def test_attack_list_roundtrip(self, tmp_path, monkeypatch):
        import persistence.preset as pm

        monkeypatch.setattr(pm, "_PRESETS_DIR", tmp_path / "Presets")
        attacks_data = [
            {"name": "Claw", "to_hit_mod": 5, "n_attacks": 2, "dmg_n_die_1": 1, "dmg_die_type_1": "d6"},
            {"name": "Bite", "to_hit_mod": 7, "n_attacks": 1, "dmg_n_die_1": 1, "dmg_die_type_1": "d8"},
        ]
        pm.save_preset("enc", {"attacks": attacks_data})
        loaded = pm.load_preset("enc")
        assert len(loaded["attacks"]) == 2
        assert loaded["attacks"][0]["name"] == "Claw"
        assert loaded["attacks"][1]["name"] == "Bite"
        assert loaded["attacks"][0]["n_attacks"] == 2
