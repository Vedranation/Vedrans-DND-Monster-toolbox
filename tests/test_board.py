"""Tests for engine/board.py and engine/inference.py."""

import pytest

from engine.board import (
    Board,
    GridPosition,
    Token,
    distance_ft,
    is_flanking,
    ranged_in_melee,
    tokens_in_range,
)
from engine.conditions import Condition
from engine.inference import (
    compute_roll_type_modifiers,
    flanking_to_hit_bonus,
    is_ambiguous,
    suggest_targets,
)


# ─── helpers ─────────────────────────────────────────────────────────────────


def _pos(col: int, row: int) -> GridPosition:
    return GridPosition(col, row)


def _monster(id: str, col: int, row: int, **kwargs) -> Token:
    return Token(id=id, kind="monster", data_ref=id, pos=_pos(col, row), **kwargs)


def _player(id: str, col: int, row: int, **kwargs) -> Token:
    return Token(id=id, kind="player", data_ref=id, pos=_pos(col, row), **kwargs)


# ─── GridPosition ─────────────────────────────────────────────────────────────


class TestGridPosition:
    def test_equality(self):
        assert _pos(3, 4) == _pos(3, 4)

    def test_inequality(self):
        assert _pos(3, 4) != _pos(3, 5)

    def test_hashable(self):
        s = {_pos(0, 0), _pos(1, 1), _pos(0, 0)}
        assert len(s) == 2


# ─── distance_ft ─────────────────────────────────────────────────────────────


class TestDistanceFt:
    def test_same_cell_is_zero(self):
        assert distance_ft(_pos(0, 0), _pos(0, 0)) == 0

    def test_straight_one_cell(self):
        assert distance_ft(_pos(0, 0), _pos(1, 0)) == 5

    def test_diagonal_one_cell_standard(self):
        # standard: max(1, 1) * 5 = 5
        assert distance_ft(_pos(0, 0), _pos(1, 1)) == 5

    def test_standard_two_diagonal(self):
        assert distance_ft(_pos(0, 0), _pos(2, 2)) == 10

    def test_mixed_dx_dy_standard(self):
        # max(3, 1) * 5 = 15
        assert distance_ft(_pos(0, 0), _pos(3, 1)) == 15

    def test_5_10_5_one_diagonal(self):
        # 1 diagonal step: cost 5
        assert distance_ft(_pos(0, 0), _pos(1, 1), mode="5-10-5") == 5

    def test_5_10_5_two_diagonals(self):
        # 2 diagonal steps: 5 + 10 = 15
        assert distance_ft(_pos(0, 0), _pos(2, 2), mode="5-10-5") == 15

    def test_5_10_5_three_diagonals(self):
        # 3 diagonal steps: 5 + 10 + 5 = 20
        assert distance_ft(_pos(0, 0), _pos(3, 3), mode="5-10-5") == 20

    def test_5_10_5_mixed(self):
        # dx=3, dy=1 → 1 diagonal (cost 5) + 2 straight (cost 10) = 15
        assert distance_ft(_pos(0, 0), _pos(3, 1), mode="5-10-5") == 15


# ─── tokens_in_range ─────────────────────────────────────────────────────────


class TestTokensInRange:
    def test_adjacent_enemy_in_melee_range(self):
        attacker = _monster("orc", 0, 0)
        enemy = _player("hero", 1, 0)
        board = Board(tokens=[attacker, enemy])
        assert enemy in tokens_in_range(attacker, board, range_ft=5)

    def test_far_enemy_not_in_range(self):
        attacker = _monster("orc", 0, 0)
        enemy = _player("hero", 10, 0)
        board = Board(tokens=[attacker, enemy])
        assert tokens_in_range(attacker, board, range_ft=5) == []

    def test_ally_excluded(self):
        attacker = _monster("orc1", 0, 0)
        ally = _monster("orc2", 1, 0)
        board = Board(tokens=[attacker, ally])
        assert tokens_in_range(attacker, board, range_ft=5) == []

    def test_self_excluded(self):
        attacker = _monster("orc", 0, 0)
        board = Board(tokens=[attacker])
        assert tokens_in_range(attacker, board, range_ft=5) == []

    def test_exactly_on_boundary(self):
        attacker = _monster("orc", 0, 0)
        enemy = _player("hero", 2, 0)  # 10 ft
        board = Board(tokens=[attacker, enemy])
        assert enemy in tokens_in_range(attacker, board, range_ft=10)
        assert tokens_in_range(attacker, board, range_ft=5) == []


# ─── is_flanking ─────────────────────────────────────────────────────────────


class TestIsFlanking:
    def test_no_flank_with_no_allies(self):
        attacker = _monster("orc", 0, 5)
        target = _player("hero", 5, 5)
        board = Board(tokens=[attacker, target])
        assert not is_flanking(attacker, target, board)

    def test_hard_flank_ally_directly_opposite(self):
        # attacker adjacent to target from left, ally adjacent from right
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)  # adjacent to target, directly opposite attacker
        board = Board(tokens=[attacker, target, ally])
        assert is_flanking(attacker, target, board)

    def test_no_flank_ally_not_adjacent_to_target(self):
        attacker = _monster("orc1", 0, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 10, 5)  # far from target
        board = Board(tokens=[attacker, target, ally])
        assert not is_flanking(attacker, target, board)

    def test_no_flank_ally_same_side_as_attacker(self):
        # both attacker and ally on the same side
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 4, 4)  # adjacent to target but same general side
        board = Board(tokens=[attacker, target, ally])
        # direction from target→attacker ≈ (−1,0); direction from target→ally ≈ (−1,−1)
        # dot product = 1/√2 > 0 → not opposite → no flank
        assert not is_flanking(attacker, target, board)

    def test_soft_flank_allows_slightly_off_axis(self):
        # attacker left, ally diagonally upper-right: dot ≈ −0.707 → soft only
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 4)
        board_soft = Board(tokens=[attacker, target, ally], flank_geometry="soft")
        assert is_flanking(attacker, target, board_soft)

    def test_hard_flank_rejects_off_axis(self):
        # same positions as above — dot ≈ −0.707 which is > −0.95, so hard mode rejects
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 4)
        board_hard = Board(tokens=[attacker, target, ally], flank_geometry="hard")
        assert not is_flanking(attacker, target, board_hard)

    def test_hard_flank_accepts_collinear(self):
        # attacker and ally on exact opposite sides (same row) → dot = −1.0 → hard allows
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)
        board_hard = Board(tokens=[attacker, target, ally], flank_geometry="hard")
        assert is_flanking(attacker, target, board_hard)

    def test_hard_flank_accepts_diagonal_collinear(self):
        # attacker NW, target centre, ally SE — strictly collinear on diagonal → dot = −1.0
        attacker = _monster("orc1", 4, 4)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 6)
        board_hard = Board(tokens=[attacker, target, ally], flank_geometry="hard")
        assert is_flanking(attacker, target, board_hard)

    def test_attacker_not_adjacent_does_not_flank(self):
        # attacker far away — no flanking even with ally opposite
        attacker = _monster("orc1", 0, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)
        board = Board(tokens=[attacker, target, ally])
        assert not is_flanking(attacker, target, board)

    def test_inactive_ally_does_not_flank(self):
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5, active=False)
        board = Board(tokens=[attacker, target, ally])
        assert not is_flanking(attacker, target, board)


# ─── ranged_in_melee ─────────────────────────────────────────────────────────


class TestRangedInMelee:
    def test_adjacent_enemy_triggers(self):
        attacker = _monster("orc", 0, 0)
        enemy = _player("hero", 1, 0)
        board = Board(tokens=[attacker, enemy])
        assert ranged_in_melee(attacker, board)

    def test_no_adjacent_enemy(self):
        attacker = _monster("orc", 0, 0)
        enemy = _player("hero", 5, 0)
        board = Board(tokens=[attacker, enemy])
        assert not ranged_in_melee(attacker, board)

    def test_adjacent_ally_does_not_trigger(self):
        attacker = _monster("orc1", 0, 0)
        ally = _monster("orc2", 1, 0)
        board = Board(tokens=[attacker, ally])
        assert not ranged_in_melee(attacker, board)


# ─── inference ───────────────────────────────────────────────────────────────


class TestSuggestTargets:
    def test_returns_closest_first(self):
        attacker = _monster("orc", 0, 0)
        near = _player("near", 1, 0)
        far = _player("far", 3, 0)
        board = Board(tokens=[attacker, near, far])
        result = suggest_targets(attacker, board, range_ft=30)
        assert result[0] is near

    def test_excludes_out_of_range(self):
        attacker = _monster("orc", 0, 0)
        near = _player("near", 1, 0)
        far = _player("far", 10, 0)
        board = Board(tokens=[attacker, near, far])
        result = suggest_targets(attacker, board, range_ft=5)
        assert far not in result

    def test_excludes_inactive(self):
        attacker = _monster("orc", 0, 0)
        target = _player("hero", 1, 0, active=False)
        board = Board(tokens=[attacker, target])
        assert suggest_targets(attacker, board, range_ft=5) == []


class TestIsAmbiguous:
    def test_two_equidistant(self):
        attacker = _monster("orc", 5, 5)
        t1 = _player("h1", 4, 5)
        t2 = _player("h2", 6, 5)
        assert is_ambiguous(attacker, [t1, t2])

    def test_not_ambiguous_when_one_closer(self):
        attacker = _monster("orc", 5, 5)
        near = _player("near", 4, 5)
        far = _player("far", 3, 5)
        assert not is_ambiguous(attacker, [near, far])

    def test_single_candidate_not_ambiguous(self):
        attacker = _monster("orc", 5, 5)
        t = _player("h", 4, 5)
        assert not is_ambiguous(attacker, [t])


class TestComputeRollTypeModifiers:
    def test_no_modifiers_is_normal(self):
        attacker = _monster("orc", 0, 5)
        target = _player("hero", 5, 5)
        board = Board(tokens=[attacker, target])
        assert compute_roll_type_modifiers(attacker, target, board) == "Normal"

    def test_flanking_advantage_gives_advantage(self):
        # attacker must be adjacent to target for flanking
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)
        board = Board(tokens=[attacker, target, ally], flank_benefit="advantage")
        assert compute_roll_type_modifiers(attacker, target, board) == "Advantage"

    def test_poisoned_attacker_gives_disadvantage(self):
        attacker = _monster("orc", 0, 5)
        attacker.conditions.add(Condition.POISONED)
        target = _player("hero", 5, 5)
        board = Board(tokens=[attacker, target])
        assert compute_roll_type_modifiers(attacker, target, board) == "Disadvantage"

    def test_flank_adv_plus_poison_cancel(self):
        attacker = _monster("orc1", 4, 5)
        attacker.conditions.add(Condition.POISONED)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)
        board = Board(tokens=[attacker, target, ally], flank_benefit="advantage")
        assert compute_roll_type_modifiers(attacker, target, board) == "Normal"

    def test_stunned_target_gives_advantage_to_attacker(self):
        attacker = _monster("orc", 0, 5)
        target = _player("hero", 5, 5)
        target.conditions.add(Condition.STUNNED)
        board = Board(tokens=[attacker, target])
        assert compute_roll_type_modifiers(attacker, target, board) == "Advantage"

    def test_ranged_in_melee_gives_disadvantage(self):
        # attack_range_ft > 5 makes this a ranged attacker
        attacker = _monster("orc", 0, 0, attack_range_ft=60)
        adjacent_enemy = _player("guardian", 1, 0)
        distant_target = _player("wizard", 10, 0)
        board = Board(tokens=[attacker, adjacent_enemy, distant_target])
        assert compute_roll_type_modifiers(attacker, distant_target, board) == "Disadvantage"

    def test_melee_in_melee_no_disadvantage(self):
        # melee attacker (default attack_range_ft=5) does NOT suffer ranged-in-melee penalty
        attacker = _monster("orc", 0, 0)  # attack_range_ft=5 by default
        adjacent_enemy = _player("guardian", 1, 0)
        distant_target = _player("wizard", 10, 0)
        board = Board(tokens=[attacker, adjacent_enemy, distant_target])
        assert compute_roll_type_modifiers(attacker, distant_target, board) == "Normal"

    def test_ignore_ranged_in_melee_suppresses_disadvantage(self):
        attacker = _monster("orc", 0, 0, attack_range_ft=60, ignore_ranged_in_melee=True)
        adjacent_enemy = _player("guardian", 1, 0)
        target = _player("wizard", 5, 0)
        board = Board(tokens=[attacker, adjacent_enemy, target])
        assert compute_roll_type_modifiers(attacker, target, board) == "Normal"

    def test_prone_target_gives_melee_attacker_advantage(self):
        attacker = _monster("orc", 4, 5)  # melee (default range 5ft)
        target = _player("hero", 5, 5)
        target.conditions.add(Condition.PRONE)
        board = Board(tokens=[attacker, target])
        assert compute_roll_type_modifiers(attacker, target, board) == "Advantage"

    def test_prone_target_gives_ranged_attacker_disadvantage(self):
        attacker = _monster("archer", 0, 5, attack_range_ft=60)
        target = _player("hero", 5, 5)
        target.conditions.add(Condition.PRONE)
        board = Board(tokens=[attacker, target])
        assert compute_roll_type_modifiers(attacker, target, board) == "Disadvantage"

    def test_two_adv_sources_return_spaced_string(self):
        # flanking + stunned target both give advantage → "Super Advantage" (with space)
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        target.conditions.add(Condition.STUNNED)
        ally = _monster("orc2", 6, 5)
        board = Board(tokens=[attacker, target, ally], flank_benefit="advantage")
        result = compute_roll_type_modifiers(attacker, target, board)
        assert result == "Super Advantage"


class TestFlankingToHitBonus:
    def test_no_bonus_without_flanking(self):
        attacker = _monster("orc", 0, 5)
        target = _player("hero", 5, 5)
        board = Board(tokens=[attacker, target], flank_benefit="+2")
        assert flanking_to_hit_bonus(attacker, target, board) == 0

    def test_plus2_when_flanking_and_benefit_is_plus2(self):
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)
        board = Board(tokens=[attacker, target, ally], flank_benefit="+2")
        assert flanking_to_hit_bonus(attacker, target, board) == 2

    def test_no_bonus_when_flank_benefit_is_advantage(self):
        attacker = _monster("orc1", 4, 5)
        target = _player("hero", 5, 5)
        ally = _monster("orc2", 6, 5)
        board = Board(tokens=[attacker, target, ally], flank_benefit="advantage")
        assert flanking_to_hit_bonus(attacker, target, board) == 0
