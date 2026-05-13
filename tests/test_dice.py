import pytest
from engine.dice import seed, roll_die, max_die


def test_roll_die_range():
    for die in ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]:
        expected_max = max_die(die)
        for _ in range(200):
            result = roll_die(die)
            assert 1 <= result <= expected_max, f"{die} rolled {result}, out of [1, {expected_max}]"


def test_max_die_values():
    assert max_die("d4") == 4
    assert max_die("d6") == 6
    assert max_die("d8") == 8
    assert max_die("d10") == 10
    assert max_die("d12") == 12
    assert max_die("d20") == 20
    assert max_die("d100") == 100


def test_seed_deterministic():
    seed(42)
    first_run = [roll_die("d20") for _ in range(10)]
    seed(42)
    second_run = [roll_die("d20") for _ in range(10)]
    assert first_run == second_run


def test_different_seeds_differ():
    seed(1)
    run_a = [roll_die("d20") for _ in range(5)]
    seed(2)
    run_b = [roll_die("d20") for _ in range(5)]
    assert run_a != run_b


def test_unknown_die_raises():
    with pytest.raises(KeyError):
        roll_die("d999")
