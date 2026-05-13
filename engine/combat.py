"""
Pure combat engine — no Tkinter, no UI references.

Faithfully ports the logic from tabs/Attack.py so tests can lock down
the arithmetic before any refactoring of the UI layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine import dice
from engine.models import AttackSpec, MonsterData, PlayerData


@dataclass
class CombatSettings:
    meets_it_beats_it: bool = False
    crits_double_dmg: bool = True
    crits_extra_die_is_max: bool = False
    nat1_always_miss: bool = True
    adv_combine: bool = False
    adv_mode: str = "RAW"  # "RAW" | "Arithmetic"


@dataclass
class SingleRollResult:
    """Detail record for one individual attack roll."""
    attack_name: str
    d20: int          # kept d20 value (highest for adv, lowest for disadv)
    total: int        # d20 + modifiers (what is compared to AC)
    is_crit: bool
    is_hit: bool
    dmg1: int
    dmg2: int
    dmg_type_1: str
    dmg_type_2: str
    roll_type: str = "Normal"
    all_d20s: list[int] = field(default_factory=list)  # kept first, dropped after
    save_info: tuple[bool, int, str] = field(default_factory=lambda: (False, 0, ""))


@dataclass
class AttackResult:
    hits: list[str | int]
    dmgs1: list[int]
    dmgs2: list[int]
    dmg_type_1: str
    dmg_type_2: str
    save_info: tuple[bool, int, str]  # (force_save, dc, save_type)
    rolls: list[SingleRollResult] = field(default_factory=list)


_ADV = frozenset({"Advantage", "Super Advantage"})
_DIS = frozenset({"Disadvantage", "Super Disadvantage"})


def combine_all_roll_types(types: list[str], adv_combine: bool, adv_mode: str = "RAW") -> str:
    """Combine any number of roll-type sources into a single effective type.

    All sources (monster attack type, player imposed, board modifier) must be
    fed in together so RAW cancellation works correctly across all three.

    RAW: any mix of adv and dis sources collapses to Normal.
    Arithmetic: net count where Super=2, Regular=1.  adv_combine controls
    whether multiple regular-polarity sources can stack to a super result.
    """
    n_super_adv = sum(1 for t in types if t == "Super Advantage")
    n_adv       = sum(1 for t in types if t == "Advantage")
    n_super_dis = sum(1 for t in types if t == "Super Disadvantage")
    n_dis       = sum(1 for t in types if t == "Disadvantage")

    has_any_adv = (n_super_adv + n_adv) > 0
    has_any_dis = (n_super_dis + n_dis) > 0

    if adv_mode == "RAW":
        if has_any_adv and has_any_dis:
            return "Normal"
        if has_any_adv:
            if n_super_adv > 0:
                return "Super Advantage"
            return "Super Advantage" if (n_adv > 1 and adv_combine) else "Advantage"
        if has_any_dis:
            if n_super_dis > 0:
                return "Super Disadvantage"
            return "Super Disadvantage" if (n_dis > 1 and adv_combine) else "Disadvantage"
        return "Normal"

    # Arithmetic mode — super type wins over stacking; adv_combine controls regular stacking
    if adv_combine:
        total_adv = n_super_adv * 2 + n_adv
        total_dis = n_super_dis * 2 + n_dis
    else:
        total_adv = 2 if n_super_adv > 0 else (1 if n_adv > 0 else 0)
        total_dis = 2 if n_super_dis > 0 else (1 if n_dis > 0 else 0)

    net = total_adv - total_dis
    if net >= 2:
        return "Super Advantage"
    if net == 1:
        return "Advantage"
    if net == -1:
        return "Disadvantage"
    if net <= -2:
        return "Super Disadvantage"
    return "Normal"


def combine_roll_types(
    monster_type: str, target_type: str, adv_combine: bool, adv_mode: str = "RAW"
) -> str:
    """Combine two roll-type sources. Delegates to combine_all_roll_types."""
    return combine_all_roll_types([monster_type, target_type], adv_combine, adv_mode)


def roll_to_hit(final_rolltype: str) -> tuple[int, list[int]]:
    """Roll d20(s) for the given roll type.

    Returns (kept_value, all_dice) where all_dice has the kept die first
    and any dropped dice after (highest→lowest for adv, lowest→highest for disadv).
    """
    if final_rolltype == "Advantage":
        d1, d2 = dice.roll_die("d20"), dice.roll_die("d20")
        return max(d1, d2), sorted([d1, d2], reverse=True)
    if final_rolltype == "Disadvantage":
        d1, d2 = dice.roll_die("d20"), dice.roll_die("d20")
        return min(d1, d2), sorted([d1, d2])
    if final_rolltype == "Super Advantage":
        d1, d2, d3 = dice.roll_die("d20"), dice.roll_die("d20"), dice.roll_die("d20")
        return max(d1, d2, d3), sorted([d1, d2, d3], reverse=True)
    if final_rolltype == "Super Disadvantage":
        d1, d2, d3 = dice.roll_die("d20"), dice.roll_die("d20"), dice.roll_die("d20")
        return min(d1, d2, d3), sorted([d1, d2, d3])
    d = dice.roll_die("d20")
    return d, [d]


def compute_damage(
    dmg_1_n_die: int,
    dmg_1_die_type: str,
    dmg_1_flat: int,
    dmg_2_n_die: int,
    dmg_2_die_type: str,
    dmg_2_flat: int,
    gw_fighting_style: bool,
    brut_crit: bool,
    savage_attacker: bool,
    settings: CombatSettings,
    crit: bool = False,
) -> tuple[int, int]:
    """Roll damage for one attack, respecting special abilities and crit mode.

    Ported from Attack.py:ComputeDamage. The anti-snake-eyes crit mode uses
    dmg_1_die_type for the bonus max-die on dmg2 — this matches the original.
    """

    def gw_roll(die_type: str) -> int:
        roll = dice.roll_die(die_type)
        if roll <= 2:
            roll = dice.roll_die(die_type)
        return roll

    def savage_roll(die_type: str) -> int:
        return max(dice.roll_die(die_type), dice.roll_die(die_type))

    def brutal_crit_roll(die_type: str) -> int:
        return dice.roll_die(die_type) + dice.roll_die(die_type)

    def roll_no_crit(die_type: str) -> int:
        if gw_fighting_style:
            return gw_roll(die_type)
        if savage_attacker:
            return savage_roll(die_type)
        return dice.roll_die(die_type)

    def roll_is_crit(die_type: str) -> int:
        if gw_fighting_style:
            return gw_roll(die_type)
        if savage_attacker:
            return savage_roll(die_type)
        if brut_crit:
            return brutal_crit_roll(die_type)
        return dice.roll_die(die_type)

    if not crit:
        dmg1 = dmg_1_flat + sum(roll_no_crit(dmg_1_die_type) for _ in range(dmg_1_n_die))
        dmg2 = dmg_2_flat + sum(roll_no_crit(dmg_2_die_type) for _ in range(dmg_2_n_die))
    elif settings.crits_double_dmg:
        dmg1 = (dmg_1_flat + sum(roll_is_crit(dmg_1_die_type) for _ in range(dmg_1_n_die))) * 2
        dmg2 = (dmg_2_flat + sum(roll_is_crit(dmg_2_die_type) for _ in range(dmg_2_n_die))) * 2
    elif not settings.crits_extra_die_is_max:
        # Double the number of dice rolled
        dmg1 = dmg_1_flat + sum(roll_is_crit(dmg_1_die_type) for _ in range(dmg_1_n_die * 2))
        dmg2 = dmg_2_flat + sum(roll_is_crit(dmg_2_die_type) for _ in range(dmg_2_n_die * 2))
    else:
        # Anti-snake-eyes: roll once per die + add the max possible value of that die
        dmg1 = dmg_1_flat + sum(roll_is_crit(dmg_1_die_type) + dice.max_die(dmg_1_die_type) for _ in range(dmg_1_n_die))
        # Original code uses dmg_1_die_type for the bonus on dmg2 as well (preserved as-is)
        dmg2 = dmg_2_flat + sum(roll_is_crit(dmg_2_die_type) + dice.max_die(dmg_1_die_type) for _ in range(dmg_2_n_die))

    return dmg1, dmg2


def compute_single_attack(
    monster: MonsterData,
    target: PlayerData,
    settings: CombatSettings,
    board_tohit_bonus: int = 0,
    board_roll_type_mod: str = "Normal",
) -> AttackResult:
    """Resolve all attacks in one multiattack sequence against a single target.

    Iterates monster.attacks; each AttackSpec's n_attacks controls how many
    times that attack type is repeated. Mixed specs model heterogeneous
    multiattacks (e.g. 2 claws + 1 bite).
    """
    hits: list[str | int] = []
    dmgs1: list[int] = []
    dmgs2: list[int] = []
    rolls: list[SingleRollResult] = []

    crit_extra_dmg = not target.adamantine  # adamantine converts crits to normal hits

    for atk in monster.attacks:
        final_rolltype = combine_all_roll_types(
            [atk.roll_type, target.imposed_roll_type, board_roll_type_mod],
            settings.adv_combine, settings.adv_mode,
        )

        for _ in range(atk.n_attacks):
            roll, all_d20s = roll_to_hit(final_rolltype)
            if roll == 1 and atk.reroll_1_on_hit:
                roll, all_d20s = roll_to_hit(final_rolltype)

            final_tohit = roll + atk.to_hit_mod + board_tohit_bonus
            if atk.bless:
                final_tohit += dice.roll_die("d4")
            if atk.bane:
                final_tohit -= dice.roll_die("d4")

            if roll >= atk.crit_number:
                dmg1, dmg2 = compute_damage(
                    atk.dmg_n_die_1, atk.dmg_die_type_1, atk.dmg_flat_1,
                    atk.dmg_n_die_2, atk.dmg_die_type_2, atk.dmg_flat_2,
                    atk.reroll_1_2_dmg, atk.brutal_critical, atk.savage_attacker,
                    settings, crit=crit_extra_dmg,
                )
                hits.append(f"crit{roll}")
                dmgs1.append(dmg1)
                dmgs2.append(dmg2)
                _si = (atk.on_hit_force_save, atk.on_hit_save_dc, atk.on_hit_save_type)
                rolls.append(SingleRollResult(
                    attack_name=atk.name, d20=roll, total=final_tohit,
                    is_crit=True, is_hit=True, dmg1=dmg1, dmg2=dmg2,
                    dmg_type_1=atk.dmg_type_1, dmg_type_2=atk.dmg_type_2,
                    roll_type=final_rolltype, all_d20s=all_d20s, save_info=_si,
                ))

            elif roll == 1 and settings.nat1_always_miss:
                hits.append("nat1")
                rolls.append(SingleRollResult(
                    attack_name=atk.name, d20=roll, total=final_tohit,
                    is_crit=False, is_hit=False, dmg1=0, dmg2=0,
                    dmg_type_1=atk.dmg_type_1, dmg_type_2=atk.dmg_type_2,
                    roll_type=final_rolltype, all_d20s=all_d20s,
                    save_info=(atk.on_hit_force_save, atk.on_hit_save_dc, atk.on_hit_save_type),
                ))

            elif settings.meets_it_beats_it:
                is_hit = final_tohit >= target.ac
                if is_hit:
                    dmg1, dmg2 = compute_damage(
                        atk.dmg_n_die_1, atk.dmg_die_type_1, atk.dmg_flat_1,
                        atk.dmg_n_die_2, atk.dmg_die_type_2, atk.dmg_flat_2,
                        atk.reroll_1_2_dmg, atk.brutal_critical, atk.savage_attacker,
                        settings, crit=False,
                    )
                    hits.append(final_tohit)
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)
                else:
                    dmg1, dmg2 = 0, 0
                rolls.append(SingleRollResult(
                    attack_name=atk.name, d20=roll, total=final_tohit,
                    is_crit=False, is_hit=is_hit, dmg1=dmg1, dmg2=dmg2,
                    dmg_type_1=atk.dmg_type_1, dmg_type_2=atk.dmg_type_2,
                    roll_type=final_rolltype, all_d20s=all_d20s,
                    save_info=(atk.on_hit_force_save, atk.on_hit_save_dc, atk.on_hit_save_type),
                ))

            else:
                is_hit = final_tohit > target.ac
                if is_hit:
                    dmg1, dmg2 = compute_damage(
                        atk.dmg_n_die_1, atk.dmg_die_type_1, atk.dmg_flat_1,
                        atk.dmg_n_die_2, atk.dmg_die_type_2, atk.dmg_flat_2,
                        atk.reroll_1_2_dmg, atk.brutal_critical, atk.savage_attacker,
                        settings, crit=False,
                    )
                    hits.append(final_tohit)
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)
                else:
                    dmg1, dmg2 = 0, 0
                rolls.append(SingleRollResult(
                    attack_name=atk.name, d20=roll, total=final_tohit,
                    is_crit=False, is_hit=is_hit, dmg1=dmg1, dmg2=dmg2,
                    dmg_type_1=atk.dmg_type_1, dmg_type_2=atk.dmg_type_2,
                    roll_type=final_rolltype, all_d20s=all_d20s,
                    save_info=(atk.on_hit_force_save, atk.on_hit_save_dc, atk.on_hit_save_type),
                ))

    first_atk = monster.attacks[0] if monster.attacks else AttackSpec()
    return AttackResult(
        hits=hits,
        dmgs1=dmgs1,
        dmgs2=dmgs2,
        dmg_type_1=first_atk.dmg_type_1,
        dmg_type_2=first_atk.dmg_type_2,
        save_info=(first_atk.on_hit_force_save, first_atk.on_hit_save_dc, first_atk.on_hit_save_type),
        rolls=rolls,
    )
