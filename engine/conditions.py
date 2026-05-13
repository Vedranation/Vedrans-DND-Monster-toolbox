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
CONDITION_EFFECTS: dict[Condition, dict[str, object]] = {
    Condition.BLINDED:       {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.CHARMED:       {},
    Condition.DEAFENED:      {},
    Condition.FRIGHTENED:    {"attack_roll_type": "disadvantage"},
    Condition.GRAPPLED:      {},
    Condition.INCAPACITATED: {},
    Condition.INVISIBLE:     {"attack_roll_type": "advantage", "defense_roll_type": "disadvantage"},
    Condition.PARALYZED:     {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.PETRIFIED:     {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.POISONED:      {"attack_roll_type": "disadvantage"},
    Condition.PRONE:         {"attack_roll_type": "disadvantage", "melee_vs_prone_adv": True},
    Condition.RESTRAINED:    {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.STUNNED:       {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
    Condition.UNCONSCIOUS:   {"attack_roll_type": "disadvantage", "defense_roll_type": "advantage"},
}
