"""Target suggestion and roll-type modifier inference for board state."""

from __future__ import annotations

from engine.board import Board, Token, distance_ft, is_flanking, ranged_in_melee
from engine.conditions import CONDITION_EFFECTS, Condition


def suggest_targets(attacker: Token, board: Board, range_ft: int = 5) -> list[Token]:
    """Return enemy tokens within range_ft, sorted by proximity (closest first)."""
    enemies = [
        t for t in board.tokens
        if t.kind != attacker.kind and t.active
        and distance_ft(attacker.pos, t.pos, board.diagonal_mode) <= range_ft
    ]
    enemies.sort(key=lambda t: distance_ft(attacker.pos, t.pos, board.diagonal_mode))
    return enemies


def is_ambiguous(attacker: Token, candidates: list[Token]) -> bool:
    """True if two or more candidates are equidistant from attacker."""
    if len(candidates) < 2:
        return False
    board_diagonal = "standard"  # candidates already filtered; distance mode embedded in list
    d0 = distance_ft(attacker.pos, candidates[0].pos)
    d1 = distance_ft(attacker.pos, candidates[1].pos)
    return d0 == d1


def compute_roll_type_modifiers(
    attacker: Token, target: Token, board: Board, adv_mode: str = "RAW"
) -> str:
    """Return the net roll-type string combining flanking, ranged-in-melee, and conditions.

    RAW (default): any mix of adv and disadv sources → Normal.
    Arithmetic: net count of sources determines the result.
    """
    adv_sources: list[str] = []
    disadv_sources: list[str] = []

    # Flanking
    if is_flanking(attacker, target, board) and board.flank_benefit == "advantage":
        adv_sources.append("flanking")

    # Ranged attack while in melee (only applies if the attacker uses a ranged weapon)
    if (
        attacker.attack_range_ft > 5
        and not attacker.ignore_ranged_in_melee
        and ranged_in_melee(attacker, board)
    ):
        disadv_sources.append("ranged_in_melee")

    # Attacker conditions
    for cond in attacker.conditions:
        effects = CONDITION_EFFECTS.get(cond, {})
        art = effects.get("attack_roll_type")
        if art == "disadvantage":
            disadv_sources.append(cond.value)
        elif art == "advantage":
            adv_sources.append(cond.value)

    # Target conditions that grant advantage or disadvantage to attacker
    for cond in target.conditions:
        effects = CONDITION_EFFECTS.get(cond, {})
        drt = effects.get("defense_roll_type")
        if drt == "advantage":
            adv_sources.append(f"target_{cond.value}")
        elif drt == "disadvantage":
            disadv_sources.append(f"target_{cond.value}")
        if effects.get("melee_vs_prone_adv"):
            if attacker.attack_range_ft <= 5:
                adv_sources.append("target_prone_melee")
            else:
                disadv_sources.append("target_prone_ranged")

    n_adv = len(adv_sources)
    n_dis = len(disadv_sources)

    if adv_mode == "Arithmetic":
        net = n_adv - n_dis
        if net > 1:
            return "Super Advantage"
        if net == 1:
            return "Advantage"
        if net == -1:
            return "Disadvantage"
        if net < -1:
            return "Super Disadvantage"
        return "Normal"

    # RAW: any mix cancels to Normal
    if n_adv > 0 and n_dis > 0:
        return "Normal"
    if n_adv > 1:
        return "Super Advantage"
    if n_adv == 1:
        return "Advantage"
    if n_dis > 1:
        return "Super Disadvantage"
    if n_dis == 1:
        return "Disadvantage"
    return "Normal"


def flanking_to_hit_bonus(attacker: Token, target: Token, board: Board) -> int:
    """Return flat +2 if flanking and board uses '+2' flank_benefit, else 0."""
    if board.flank_benefit == "+2" and is_flanking(attacker, target, board):
        return 2
    return 0
