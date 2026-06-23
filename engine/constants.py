"""Canonical D&D constant lists — single source of truth.

These were previously duplicated across GlobalStateManager, MonsterCreation, and
Spellcasters. UI modules import from here so the values can't drift, and the web
server will expose them to the client via an endpoint during the migration.

Pure data — no Tkinter, no GSM.
"""

from __future__ import annotations

from engine.conditions import Condition

ROLL_TYPES = ["Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"]

DMG_TYPES = [
    "bludgeoning",
    "magic bludgeoning",
    "piercing",
    "magic piercing",
    "slashing",
    "magic slashing",
    "acid",
    "cold",
    "fire",
    "force",
    "lightning",
    "thunder",
    "necrotic",
    "poison",
    "psychic",
    "radiant",
]

DICE_TYPES = ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]

# Note: WIS before INT — preserved from the original GSM ordering (UI dropdowns).
SAVING_THROW_TYPES = ["STR", "DEX", "CON", "WIS", "INT", "CHA"]

# Leading "" is the "unspecified" option shown in the creature-type dropdown.
CREATURE_TYPES = [
    "", "Aberration", "Beast", "Celestial", "Construct", "Dragon",
    "Elemental", "Fey", "Fiend", "Giant", "Humanoid", "Monstrosity",
    "Ooze", "Plant", "Undead",
]

CREATURE_SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]

# Derived from the Condition enum so the two can never drift apart.
ALL_CONDITIONS = [c.value for c in Condition]

# Leading "" is the "unspecified" option; "Other" catches rare/homebrew schools.
SPELL_SCHOOLS = [
    "", "Abjuration", "Conjuration", "Divination", "Enchantment",
    "Evocation", "Illusion", "Necromancy", "Transmutation", "Other",
]

# Player skills tracked for party skill checks (keys match PlayerData.skills).
SKILLS = ["perception", "investigation", "arcana", "insight", "stealth"]

# Full 5e skill list (for monster skill checks, which can use any skill).
ALL_SKILLS = [
    "acrobatics", "animal handling", "arcana", "athletics", "deception",
    "history", "insight", "intimidation", "investigation", "medicine",
    "nature", "perception", "performance", "persuasion", "religion",
    "sleight of hand", "stealth", "survival",
]
