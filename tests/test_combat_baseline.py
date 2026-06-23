"""
Baseline combat tests — lock down existing arithmetic before any refactoring.

Uses engine.combat which is a pure-Python port of tabs/Attack.py logic.
All randomness is controlled via engine.dice.seed() or unittest.mock.patch.
"""

from unittest.mock import patch

from engine import dice
from engine.combat import (
    CombatSettings,
    combine_all_roll_types,
    combine_roll_types,
    compute_single_attack,
    roll_to_hit,
)
from engine.models import AttackSpec, MonsterData, PlayerData


def _monster(**kwargs) -> MonsterData:
    return MonsterData(attacks=[AttackSpec(**kwargs)])


TARGET_AC15 = PlayerData(ac=15)
DEFAULT_SETTINGS = CombatSettings()  # crits_double_dmg=True, nat1_always_miss=True, meets_it_beats_it=False


# ─── combine_roll_types ───────────────────────────────────────────────────────


class TestCombineRollTypes:
    # ── shared behaviour (same in both modes) ─────────────────────────────────

    def test_normal_is_transparent(self):
        for rt in ["Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"]:
            assert combine_roll_types("Normal", rt, adv_combine=False, adv_mode="RAW") == rt
            assert combine_roll_types("Normal", rt, adv_combine=False, adv_mode="Arithmetic") == rt

    def test_adv_plus_disadv_is_normal_both_modes(self):
        for mode in ("RAW", "Arithmetic"):
            assert combine_roll_types("Advantage", "Disadvantage", adv_combine=False, adv_mode=mode) == "Normal"
            assert combine_roll_types("Disadvantage", "Advantage", adv_combine=False, adv_mode=mode) == "Normal"

    def test_super_adv_vs_super_disadv_is_normal_both_modes(self):
        for mode in ("RAW", "Arithmetic"):
            assert combine_roll_types("Super Advantage", "Super Disadvantage", adv_combine=False, adv_mode=mode) == "Normal"
            assert combine_roll_types("Super Disadvantage", "Super Advantage", adv_combine=False, adv_mode=mode) == "Normal"

    # ── RAW mode: any mix collapses to Normal ──────────────────────────────────

    def test_raw_super_adv_plus_disadv_is_normal(self):
        assert combine_roll_types("Super Advantage", "Disadvantage", adv_combine=False, adv_mode="RAW") == "Normal"
        assert combine_roll_types("Super Disadvantage", "Advantage", adv_combine=False, adv_mode="RAW") == "Normal"

    def test_raw_same_polarity(self):
        assert combine_roll_types("Advantage", "Advantage", adv_combine=True, adv_mode="RAW") == "Super Advantage"
        assert combine_roll_types("Advantage", "Advantage", adv_combine=False, adv_mode="RAW") == "Advantage"
        assert combine_roll_types("Disadvantage", "Disadvantage", adv_combine=True, adv_mode="RAW") == "Super Disadvantage"
        assert combine_roll_types("Disadvantage", "Disadvantage", adv_combine=False, adv_mode="RAW") == "Disadvantage"

    # ── Arithmetic mode: net-counting ─────────────────────────────────────────

    def test_arithmetic_adv_plus_adv_with_combine(self):
        assert combine_roll_types("Advantage", "Advantage", adv_combine=True, adv_mode="Arithmetic") == "Super Advantage"

    def test_arithmetic_adv_plus_adv_without_combine(self):
        assert combine_roll_types("Advantage", "Advantage", adv_combine=False, adv_mode="Arithmetic") == "Advantage"

    def test_arithmetic_disadv_plus_disadv_with_combine(self):
        assert combine_roll_types("Disadvantage", "Disadvantage", adv_combine=True, adv_mode="Arithmetic") == "Super Disadvantage"

    def test_arithmetic_disadv_plus_disadv_without_combine(self):
        assert combine_roll_types("Disadvantage", "Disadvantage", adv_combine=False, adv_mode="Arithmetic") == "Disadvantage"

    def test_arithmetic_super_adv_beats_disadv(self):
        assert combine_roll_types("Super Advantage", "Disadvantage", adv_combine=False, adv_mode="Arithmetic") == "Advantage"

    def test_arithmetic_super_disadv_beats_adv(self):
        assert combine_roll_types("Super Disadvantage", "Advantage", adv_combine=False, adv_mode="Arithmetic") == "Disadvantage"

    def test_arithmetic_super_disadv_stays_on_disadv(self):
        assert combine_roll_types("Super Disadvantage", "Disadvantage", adv_combine=False, adv_mode="Arithmetic") == "Super Disadvantage"
        assert combine_roll_types("Super Disadvantage", "Super Disadvantage", adv_combine=False, adv_mode="Arithmetic") == "Super Disadvantage"


# ─── combine_all_roll_types (3-source, the board+player+monster case) ────────


class TestCombineAllRollTypes:
    """The key bug: monster roll type must not override a board+player cancellation."""

    def test_raw_three_way_adv_dis_cancels(self):
        # Board: flanking (adv), Player imposes: dis, Monster atk: adv → any adv+dis = Normal
        assert combine_all_roll_types(["Advantage", "Disadvantage", "Advantage"],
                                      adv_combine=False, adv_mode="RAW") == "Normal"

    def test_raw_super_adv_with_dis_and_board_adv_cancels(self):
        assert combine_all_roll_types(["Super Advantage", "Disadvantage", "Advantage"],
                                      adv_combine=False, adv_mode="RAW") == "Normal"

    def test_raw_super_dis_with_dis_and_board_adv_cancels(self):
        assert combine_all_roll_types(["Super Disadvantage", "Disadvantage", "Advantage"],
                                      adv_combine=False, adv_mode="RAW") == "Normal"

    def test_raw_all_normal_is_normal(self):
        assert combine_all_roll_types(["Normal", "Normal", "Normal"],
                                      adv_combine=False, adv_mode="RAW") == "Normal"

    def test_raw_only_adv_sources(self):
        assert combine_all_roll_types(["Advantage", "Normal", "Advantage"],
                                      adv_combine=True, adv_mode="RAW") == "Super Advantage"
        assert combine_all_roll_types(["Advantage", "Normal", "Advantage"],
                                      adv_combine=False, adv_mode="RAW") == "Advantage"

    def test_arithmetic_board_adv_impose_super_dis_monster_normal(self):
        # net = 0 + (-2) + 1 = -1 → Disadvantage
        assert combine_all_roll_types(["Normal", "Super Disadvantage", "Advantage"],
                                      adv_combine=False, adv_mode="Arithmetic") == "Disadvantage"

    def test_arithmetic_super_dis_dis_board_adv(self):
        # net: super_dis(-2) + dis(-1) + adv(+1) = -2 → Super Disadvantage
        assert combine_all_roll_types(["Super Disadvantage", "Disadvantage", "Advantage"],
                                      adv_combine=True, adv_mode="Arithmetic") == "Super Disadvantage"

    def test_board_roll_type_mod_passed_through_compute(self):
        # Monster atk Normal, player imposed Normal, board = Advantage → should be Advantage
        monster = _monster(to_hit_mod=5, n_attacks=1, dmg_n_die_1=1, dmg_die_type_1="d6")
        # Advantage rolls 2 d20s (15, 12 → keeps 15); then 1 d6 for damage
        with patch("engine.dice.roll_die", side_effect=[15, 12, 4]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS,
                                           board_roll_type_mod="Advantage")
        assert result.rolls[0].roll_type == "Advantage"

    def test_board_dis_plus_monster_adv_cancels_raw(self):
        # Monster atk: Adv, Board: Dis (ranged in melee), Player: Normal → Normal in RAW
        monster = _monster(roll_type="Advantage", to_hit_mod=5, n_attacks=1,
                           dmg_n_die_1=1, dmg_die_type_1="d6")
        # Normal (after RAW cancellation) rolls 1 d20; then 1 d6 for damage
        with patch("engine.dice.roll_die", side_effect=[10, 4]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS,
                                           board_roll_type_mod="Disadvantage")
        assert result.rolls[0].roll_type == "Normal"


# ─── roll_to_hit ─────────────────────────────────────────────────────────────


class TestRollToHit:
    def test_normal_is_single_die(self):
        dice.seed(42)
        expected = dice.roll_die("d20")
        dice.seed(42)
        value, all_dice = roll_to_hit("Normal")
        assert value == expected
        assert all_dice == [expected]

    # all_dice is returned in NATURAL roll order (not sorted) so the UI shows the
    # real sequence; only `value` (the kept die) is the max/min.
    def test_advantage_takes_max_of_two(self):
        dice.seed(42)
        r1, r2 = dice.roll_die("d20"), dice.roll_die("d20")
        dice.seed(42)
        value, all_dice = roll_to_hit("Advantage")
        assert value == max(r1, r2)
        assert all_dice == [r1, r2]

    def test_disadvantage_takes_min_of_two(self):
        dice.seed(42)
        r1, r2 = dice.roll_die("d20"), dice.roll_die("d20")
        dice.seed(42)
        value, all_dice = roll_to_hit("Disadvantage")
        assert value == min(r1, r2)
        assert all_dice == [r1, r2]

    def test_super_advantage_takes_max_of_three(self):
        dice.seed(77)
        r1, r2, r3 = dice.roll_die("d20"), dice.roll_die("d20"), dice.roll_die("d20")
        dice.seed(77)
        value, all_dice = roll_to_hit("Super Advantage")
        assert value == max(r1, r2, r3)
        assert all_dice == [r1, r2, r3]

    def test_super_disadvantage_takes_min_of_three(self):
        dice.seed(77)
        r1, r2, r3 = dice.roll_die("d20"), dice.roll_die("d20"), dice.roll_die("d20")
        dice.seed(77)
        value, all_dice = roll_to_hit("Super Disadvantage")
        assert value == min(r1, r2, r3)
        assert all_dice == [r1, r2, r3]


# ─── nat 1 ───────────────────────────────────────────────────────────────────


class TestNat1:
    def test_nat1_always_miss_when_enabled(self):
        settings = CombatSettings(nat1_always_miss=True)
        monster = _monster(to_hit_mod=100, n_attacks=1)  # +100 would beat any AC
        with patch("engine.dice.roll_die", return_value=1):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.hits == ["nat1"]
        assert result.dmgs1 == []
        assert result.dmgs2 == []

    def test_nat1_can_hit_when_disabled(self):
        settings = CombatSettings(nat1_always_miss=False, meets_it_beats_it=True)
        monster = _monster(to_hit_mod=20, n_attacks=1)  # 1 + 20 = 21 >= 15
        with patch("engine.dice.roll_die", return_value=1):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert len(result.hits) == 1
        assert result.hits[0] == 21  # not a crit (1 < 20), not missed → hit value


# ─── critical hits ───────────────────────────────────────────────────────────


class TestCriticalHits:
    def test_crit_at_20(self):
        monster = _monster(crit_number=20, dmg_n_die_1=1, dmg_die_type_1="d6")
        with patch("engine.dice.roll_die", side_effect=[20, 4]):  # d20=20, d6=4
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert len(result.hits) == 1
        assert str(result.hits[0]).startswith("crit")

    def test_crit_at_champion_19(self):
        monster = _monster(crit_number=19, dmg_n_die_1=1, dmg_die_type_1="d6")
        with patch("engine.dice.roll_die", side_effect=[19, 3]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert str(result.hits[0]) == "crit19"

    def test_roll_below_crit_number_is_not_crit(self):
        monster = _monster(crit_number=20, to_hit_mod=100, dmg_n_die_1=1, dmg_die_type_1="d6")
        with patch("engine.dice.roll_die", side_effect=[19, 5]):  # 19 < 20, so not a crit
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        # 19 + 100 = 119 → plain hit (no "crit" prefix)
        assert result.hits[0] == 119

    def test_19_below_crit_number_20_is_normal_hit(self):
        monster = _monster(crit_number=20, to_hit_mod=0, dmg_n_die_1=1, dmg_die_type_1="d6")
        settings = CombatSettings(meets_it_beats_it=False)
        with patch("engine.dice.roll_die", side_effect=[19, 5]):  # 19 + 0 = 19 > 15 → hit
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.hits[0] == 19


# ─── meets-it-beats-it ───────────────────────────────────────────────────────


class TestMeetsItBeatsIt:
    def test_exact_ac_hits_when_enabled(self):
        settings = CombatSettings(meets_it_beats_it=True, nat1_always_miss=False)
        monster = _monster(to_hit_mod=0, dmg_n_die_1=1, dmg_die_type_1="d6")
        with patch("engine.dice.roll_die", side_effect=[15, 3]):  # roll=15, 15>=15 → hit
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert len(result.hits) == 1

    def test_exact_ac_misses_when_disabled(self):
        settings = CombatSettings(meets_it_beats_it=False, nat1_always_miss=False)
        monster = _monster(to_hit_mod=0)
        with patch("engine.dice.roll_die", return_value=15):  # 15 > 15 is False → miss
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.hits == []

    def test_one_below_ac_always_misses(self):
        for mitbi in [True, False]:
            settings = CombatSettings(meets_it_beats_it=mitbi, nat1_always_miss=False)
            monster = _monster(to_hit_mod=0)
            with patch("engine.dice.roll_die", return_value=14):  # 14 < 15 either way
                result = compute_single_attack(monster, TARGET_AC15, settings)
            assert result.hits == []


# ─── multiattack ─────────────────────────────────────────────────────────────


class TestMultiattack:
    def test_n_attacks_produces_n_independent_rolls(self):
        monster = _monster(n_attacks=3, to_hit_mod=100, dmg_n_die_1=1, dmg_die_type_1="d6")
        # 3 d20 rolls of 10 each → all hit (10+100=110>15); 3 d6 rolls of 4 each
        with patch("engine.dice.roll_die", side_effect=[10, 4, 10, 4, 10, 4]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert len(result.hits) == 3
        assert len(result.dmgs1) == 3
        assert len(result.dmgs2) == 3

    def test_zero_attacks_produces_nothing(self):
        monster = _monster(n_attacks=0)
        result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.hits == []
        assert result.dmgs1 == []

    def test_four_attacks_all_miss(self):
        settings = CombatSettings(nat1_always_miss=False, meets_it_beats_it=False)
        monster = _monster(n_attacks=4, to_hit_mod=0)
        with patch("engine.dice.roll_die", return_value=5):  # 5+0=5, 5>15 False → miss
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.hits == []


# ─── damage modes ────────────────────────────────────────────────────────────


class TestDamageModes:
    def test_double_total_damage_on_crit(self):
        settings = CombatSettings(crits_double_dmg=True)
        monster = _monster(crit_number=20, dmg_n_die_1=1, dmg_die_type_1="d6", dmg_flat_1=3)
        # d20=20 (crit), d6=4 → dmg = (4+3)*2 = 14
        with patch("engine.dice.roll_die", side_effect=[20, 4]):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.dmgs1[0] == 14

    def test_double_dice_on_crit(self):
        settings = CombatSettings(crits_double_dmg=False, crits_extra_die_is_max=False)
        monster = _monster(crit_number=20, dmg_n_die_1=1, dmg_die_type_1="d6", dmg_flat_1=0)
        # d20=20 (crit), two d6 rolls: 4 and 3 → dmg = 0+4+3 = 7
        with patch("engine.dice.roll_die", side_effect=[20, 4, 3]):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.dmgs1[0] == 7

    def test_anti_snake_eyes_crit(self):
        settings = CombatSettings(crits_double_dmg=False, crits_extra_die_is_max=True)
        monster = _monster(crit_number=20, dmg_n_die_1=1, dmg_die_type_1="d6", dmg_flat_1=0)
        # d20=20 (crit), d6=2 → dmg = 2 + max_d6(6) = 8
        with patch("engine.dice.roll_die", side_effect=[20, 2]):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.dmgs1[0] == 8

    def test_normal_hit_does_not_double(self):
        settings = CombatSettings(crits_double_dmg=True, meets_it_beats_it=False)
        monster = _monster(crit_number=20, to_hit_mod=10, dmg_n_die_1=1, dmg_die_type_1="d6", dmg_flat_1=2)
        # d20=10 (not crit, 10+10=20 > 15 → hit), d6=3 → dmg = 3+2 = 5 (no doubling)
        with patch("engine.dice.roll_die", side_effect=[10, 3]):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.dmgs1[0] == 5

    def test_second_damage_type(self):
        settings = CombatSettings(meets_it_beats_it=False, crits_double_dmg=True)
        monster = _monster(
            crit_number=20,
            to_hit_mod=10,
            dmg_n_die_1=1,
            dmg_die_type_1="d6",
            dmg_flat_1=0,
            dmg_n_die_2=1,
            dmg_die_type_2="d4",
            dmg_flat_2=0,
        )
        # d20=10 (hit: 20>15), d6=3, d4=2
        with patch("engine.dice.roll_die", side_effect=[10, 3, 2]):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.dmgs1[0] == 3
        assert result.dmgs2[0] == 2


# ─── adamantine ──────────────────────────────────────────────────────────────


class TestAdamantine:
    def test_adamantine_prevents_crit_bonus_damage(self):
        settings = CombatSettings(crits_double_dmg=True)
        target = PlayerData(ac=0, adamantine=True)
        monster = _monster(crit_number=20, dmg_n_die_1=1, dmg_die_type_1="d6", dmg_flat_1=0)
        # d20=20 (crit detected), d6=3 → with adamantine, damage is NOT doubled → 3
        with patch("engine.dice.roll_die", side_effect=[20, 3]):
            result = compute_single_attack(monster, target, settings)
        assert str(result.hits[0]).startswith("crit")  # still registered as crit
        assert result.dmgs1[0] == 3  # no doubling


# ─── saving throw passthrough ─────────────────────────────────────────────────


class TestSaveInfo:
    def test_save_info_on_hit(self):
        monster = _monster(
            to_hit_mod=100,
            on_hit_force_save=True,
            on_hit_save_dc=14,
            on_hit_save_type="DEX",
            dmg_n_die_1=1,
            dmg_die_type_1="d6",
        )
        with patch("engine.dice.roll_die", side_effect=[10, 3]):  # hit, damage
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.save_info == (True, 14, "DEX")

    def test_no_save_info_when_disabled(self):
        monster = _monster(to_hit_mod=100, on_hit_force_save=False, dmg_n_die_1=1, dmg_die_type_1="d6")
        with patch("engine.dice.roll_die", side_effect=[10, 3]):
            result = compute_single_attack(monster, TARGET_AC15, DEFAULT_SETTINGS)
        assert result.save_info[0] is False


# ─── halfling luck (reroll 1s on to-hit) ─────────────────────────────────────


class TestHalflingLuck:
    def test_reroll_1_triggers_second_roll(self):
        settings = CombatSettings(nat1_always_miss=True)
        monster = _monster(reroll_1_on_hit=True, to_hit_mod=100, dmg_n_die_1=1, dmg_die_type_1="d6")
        # First d20=1 (triggers reroll), second d20=10 → 10+100=110 > 15 → hit
        with patch("engine.dice.roll_die", side_effect=[1, 10, 3]):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert len(result.hits) == 1
        assert result.hits[0] == 110

    def test_no_reroll_without_halfling_luck(self):
        settings = CombatSettings(nat1_always_miss=True)
        monster = _monster(reroll_1_on_hit=False, to_hit_mod=100)
        with patch("engine.dice.roll_die", return_value=1):
            result = compute_single_attack(monster, TARGET_AC15, settings)
        assert result.hits == ["nat1"]
