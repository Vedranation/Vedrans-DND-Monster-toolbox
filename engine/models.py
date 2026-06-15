"""
Domain models — plain Python dataclasses with no Tkinter dependency.

UI-layer classes (MonsterStats, PlayerStats) hold Tkinter vars and expose
.to_data() / .from_data() to convert to/from these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.conditions import Condition


@dataclass
class AttackSpec:
    """All parameters that define one attack action."""

    name: str = "Attack"
    to_hit_mod: int = 5
    roll_type: str = "Normal"
    n_attacks: int = 1
    dmg_n_die_1: int = 1
    dmg_die_type_1: str = "d6"
    dmg_flat_1: int = 0
    dmg_type_1: str = "slashing"
    dmg_n_die_2: int = 0
    dmg_die_type_2: str = "d6"
    dmg_flat_2: int = 0
    dmg_type_2: str = "None"
    crit_number: int = 20
    brutal_critical: bool = False
    savage_attacker: bool = False
    reroll_1_on_hit: bool = False  # halfling luck
    reroll_1_2_dmg: bool = False  # GW fighting style
    bane: bool = False
    bless: bool = False
    on_hit_force_save: bool = False
    on_hit_save_dc: int = 8
    on_hit_save_type: str = "CON"


@dataclass
class MonsterData:
    name: str = "Monster"
    ac: int = 13
    max_hp: int = 0
    attack_range_ft: int = 5           # 5 = melee; > 5 = ranged
    ignore_ranged_in_melee: bool = False  # crossbow expert etc.
    highlight_range_ft: int = 5        # board range-highlight radius
    # Each entry is one attack type; n_attacks on the spec controls repetitions.
    attacks: list[AttackSpec] = field(default_factory=lambda: [AttackSpec()])
    # keys: "STR","DEX","CON","INT","WIS","CHA"  values: (modifier, roll_type)
    saving_throws: dict[str, tuple[int, str]] = field(default_factory=dict)
    # keys: "walk","fly","climb","burrow","swim"  values: speed in ft
    speeds: dict[str, int] = field(default_factory=dict)
    passive_perception: int = 10
    initiative_mod: int = 0
    conditions: set[Condition] = field(default_factory=set)
    # Informational fields (no mechanical effect except condition_immunities)
    creature_type: str = ""    # Humanoid, Beast, Undead, etc.
    creature_size: str = "Medium"  # Tiny/Small/Medium/Large/Huge/Gargantuan
    # keys: "darkvision","blindsight","tremorsense","truesight"  values: range in ft (0 = none)
    senses: dict[str, int] = field(default_factory=dict)
    damage_resistances: list[str] = field(default_factory=list)
    damage_immunities: list[str] = field(default_factory=list)
    damage_vulnerabilities: list[str] = field(default_factory=list)
    # Condition immunity values match Condition.value strings (e.g. "poisoned")
    condition_immunities: set[str] = field(default_factory=set)


@dataclass
class PlayerData:
    name: str = "Player"
    ac: int = 13
    max_hp: int = 0
    attack_range_ft: int = 5
    ignore_ranged_in_melee: bool = False
    highlight_range_ft: int = 5
    imposed_roll_type: str = "Normal"
    adamantine: bool = False
    # keys: "perception","investigation","arcana","insight","stealth"  values: (modifier, roll_type)
    skills: dict[str, tuple[int, str]] = field(default_factory=dict)
    passive_perception: int = 10
    initiative_mod: int = 0
    conditions: set[Condition] = field(default_factory=set)
