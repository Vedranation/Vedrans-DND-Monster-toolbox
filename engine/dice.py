import random

_rng = random.Random()

_DIE_MAX: dict[str, int] = {
    "d4": 4,
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
    "d20": 20,
    "d100": 100,
}


def seed(value: int) -> None:
    _rng.seed(value)


def roll_die(die_type: str) -> int:
    return _rng.randint(1, _DIE_MAX[die_type])


def max_die(die_type: str) -> int:
    return _DIE_MAX[die_type]
