"""Tests for the typed damage-total breakdown (engine.combat)."""

from engine.combat import (
    SingleRollResult,
    damage_by_type,
    format_damage_breakdown,
    resolve_typed_damage,
    typed_damage_parts,
)


def _roll(is_hit, dmg1, type1, dmg2=0, type2="None"):
    return SingleRollResult(
        attack_name="x", d20=10, total=15, is_crit=False, is_hit=is_hit,
        dmg1=dmg1, dmg2=dmg2, dmg_type_1=type1, dmg_type_2=type2,
    )


def test_multi_type_breakdown():
    rolls = [
        _roll(True, 16, "slashing"),
        _roll(True, 0, "slashing", 4, "fire"),
        _roll(True, 3, "cold"),
        _roll(False, 9, "slashing"),  # miss contributes nothing
    ]
    assert format_damage_breakdown(rolls) == "16 slashing, 4 fire, 3 cold = 23"


def test_single_type_has_no_equals():
    assert format_damage_breakdown([_roll(True, 7, "slashing")]) == "7 slashing"


def test_no_hits_is_zero():
    assert format_damage_breakdown([_roll(False, 0, "slashing")]) == "0"
    assert format_damage_breakdown([]) == "0"


def test_damage_by_type_sums_both_components():
    rolls = [_roll(True, 5, "fire", 2, "fire"), _roll(True, 3, "cold")]
    assert damage_by_type(rolls) == {"fire": 7, "cold": 3}


# ── resistances / immunities ────────────────────────────────────────────────

def test_resistance_halves_one_type():
    # 10 slashing + 10 fire, resistant to fire → 10 + 5 = 15.
    rolls = [_roll(True, 10, "slashing"), _roll(True, 10, "fire")]
    total, text = resolve_typed_damage(rolls, resistances=["fire"])
    assert total == 15
    assert text == "10 slashing, 5 fire (resisted) = 15"


def test_immunity_zeroes_one_type():
    rolls = [_roll(True, 10, "slashing"), _roll(True, 10, "fire")]
    total, text = resolve_typed_damage(rolls, immunities=["fire"])
    assert total == 10
    assert text == "10 slashing, 0 fire (immune) = 10"


def test_resistance_rounds_down():
    total, text = resolve_typed_damage([_roll(True, 7, "cold")], resistances=["cold"])
    assert total == 3  # 7 // 2
    assert text == "3 cold (resisted)"


def test_no_resist_matches_plain_breakdown():
    rolls = [_roll(True, 16, "slashing"), _roll(True, 4, "fire")]
    total, text = resolve_typed_damage(rolls)
    assert total == 20
    assert text == format_damage_breakdown(rolls)


def test_resist_is_case_insensitive():
    total, _ = resolve_typed_damage([_roll(True, 8, "fire")], resistances=["FIRE"])
    assert total == 4


def test_typed_damage_parts_structured():
    rolls = [_roll(True, 16, "bludgeoning"), _roll(True, 10, "fire"), _roll(True, 4, "force")]
    parts = typed_damage_parts(rolls, resistances=["bludgeoning"], vulnerabilities=["fire"])
    assert parts == [
        {"type": "bludgeoning", "amount": 8, "status": "resisted"},
        {"type": "fire", "amount": 20, "status": "vulnerable"},
        {"type": "force", "amount": 4, "status": ""},
    ]
    # the string form (used elsewhere) stays consistent with the parts' total
    total, _ = resolve_typed_damage(rolls, resistances=["bludgeoning"], vulnerabilities=["fire"])
    assert total == sum(p["amount"] for p in parts) == 32


def test_vulnerability_doubles_one_type():
    # Treant: resist bludgeoning/piercing, vulnerable to fire.
    rolls = [_roll(True, 16, "bludgeoning"), _roll(True, 10, "fire")]
    total, text = resolve_typed_damage(rolls, resistances=["bludgeoning", "piercing"],
                                       vulnerabilities=["fire"])
    assert total == 8 + 20  # 16//2 + 10*2
    assert text == "8 bludgeoning (resisted), 20 fire (vulnerable) = 28"


def test_vulnerability_alone():
    total, text = resolve_typed_damage([_roll(True, 7, "fire")], vulnerabilities=["fire"])
    assert total == 14
    assert text == "14 fire (vulnerable)"
