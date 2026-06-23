from __future__ import annotations

from enum import Enum


class Condition(Enum):
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


# Effect table keys:
#   "attack_roll_type"   — roll modifier for the conditioned creature's own attacks
#   "defense_roll_type"  — roll modifier for attackers targeting the conditioned creature
#   "melee_vs_prone_adv" — adjacent melee attackers get advantage, ranged get disadvantage (prone)
# INCAPACITATED (and the four conditions that imply it — paralyzed/petrified/
# stunned/unconscious) means the creature CAN'T ATTACK. That is enforced separately
# (see CANT_ATTACK below + the board resolve/targeting code), so those conditions no
# longer carry an "attack_roll_type" — they keep only the advantage they grant to
# attackers targeting them.
CONDITION_EFFECTS: dict[Condition, dict[str, object]] = {
    Condition.BLINDED:       {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.CHARMED:       {},
    Condition.DEAFENED:      {},
    Condition.FRIGHTENED:    {"attack_roll_type": "disadvantage"},
    Condition.GRAPPLED:      {},
    Condition.INCAPACITATED: {},
    Condition.INVISIBLE:     {"attack_roll_type": "advantage", "defense_roll_type": "disadvantage"},
    Condition.PARALYZED:     {"defense_roll_type": "advantage"},
    Condition.PETRIFIED:     {"defense_roll_type": "advantage"},
    Condition.POISONED:      {"attack_roll_type": "disadvantage"},
    Condition.PRONE:         {"attack_roll_type": "disadvantage", "melee_vs_prone_adv": True},
    Condition.RESTRAINED:    {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.STUNNED:       {"defense_roll_type": "advantage"},
    Condition.UNCONSCIOUS:   {"defense_roll_type": "advantage"},
}

# A creature with any of these can't attack at all (incapacitated). The four parent
# conditions imply incapacitated; the UI auto-adds it but the user may override.
CANT_ATTACK = frozenset({"incapacitated"})

# Conditions that imply incapacitated (the UI links them; listed here for reference).
INCAPACITATING = frozenset({"paralyzed", "petrified", "stunned", "unconscious"})
