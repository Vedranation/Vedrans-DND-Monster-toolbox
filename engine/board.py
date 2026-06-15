"""Board domain model: grid, tokens, distance, flanking, range."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from engine.conditions import Condition


@dataclass
class GridPosition:
    col: int
    row: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GridPosition) and self.col == other.col and self.row == other.row

    def __hash__(self) -> int:
        return hash((self.col, self.row))


# Default teams reproduce the original monster-vs-player allegiance. `kind`
# stays purely cosmetic/role (has-attacks vs has-imposed-roll, token fill);
# allegiance is now the `team` string — different team = enemy, same = ally.
TEAM_PLAYERS = "Players"
TEAM_MONSTERS = "Monsters"


@dataclass
class Team:
    name: str
    color: str  # hex colour for the on-token team dot


def default_teams() -> list[Team]:
    return [Team(TEAM_PLAYERS, "#3a6ea5"), Team(TEAM_MONSTERS, "#a53a3a")]


@dataclass
class Token:
    id: str
    kind: Literal["monster", "player"]
    data_ref: str  # MonsterData.name or PlayerData.name
    pos: GridPosition
    hp: int = 0
    max_hp: int = 0
    attack_range_ft: int = 5           # 5 = melee; > 5 = ranged
    ignore_ranged_in_melee: bool = False
    highlight_range_ft: int = 5
    conditions: set[Condition] = field(default_factory=set)
    active: bool = True
    team: str = ""  # allegiance; blank → defaulted from kind in __post_init__

    def __post_init__(self) -> None:
        if not self.team:
            self.team = TEAM_PLAYERS if self.kind == "player" else TEAM_MONSTERS


@dataclass
class Board:
    width: int = 20
    height: int = 20
    tokens: list[Token] = field(default_factory=list)
    diagonal_mode: str = "standard"  # "standard" | "5-10-5"
    flank_geometry: str = "hard"     # "hard" | "soft"
    flank_benefit: str = "advantage" # "advantage" | "+2"
    range_mode: str = "warn"         # "warn" | "block"
    teams: list[Team] = field(default_factory=default_teams)


# ─── distance ────────────────────────────────────────────────────────────────


def distance_ft(a: GridPosition, b: GridPosition, mode: str = "standard") -> float:
    """Return distance in feet between two grid cells (5 ft per cell)."""
    dx = abs(a.col - b.col)
    dy = abs(a.row - b.row)
    if mode == "5-10-5":
        straight = min(dx, dy)
        diagonal_steps = abs(dx - dy)
        # alternating 5/10: first diagonal is 5, second 10, …
        # total diagonal cost: ceil(straight / 2) * 10 + floor(straight / 2) * 5
        full_pairs, remainder = divmod(straight, 2)
        diag_cost = full_pairs * 15 + remainder * 5
        return (diag_cost + diagonal_steps * 5)
    # standard: max(dx, dy) * 5
    return max(dx, dy) * 5.0


def tokens_in_range(attacker: Token, board: Board, range_ft: int) -> list[Token]:
    """Return all tokens not on attacker's team within range_ft feet."""
    result = []
    for token in board.tokens:
        if token is attacker:
            continue
        if token.team == attacker.team:
            continue
        if distance_ft(attacker.pos, token.pos, board.diagonal_mode) <= range_ft:
            result.append(token)
    return result


# ─── flanking ────────────────────────────────────────────────────────────────


def _direction(src: GridPosition, dst: GridPosition) -> tuple[float, float]:
    """Unit vector from src toward dst (or zero vector if same cell)."""
    dx = dst.col - src.col
    dy = dst.row - src.row
    length = math.hypot(dx, dy)
    if length == 0:
        return (0.0, 0.0)
    return (dx / length, dy / length)


def _dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def is_flanking(attacker: Token, target: Token, board: Board) -> bool:
    """Return True if any ally of attacker is flanking target with attacker.

    Flanking requires the attacker to be in melee range (≤ 5 ft) of the target.
    Hard geometry: ally must be in the 3-cell arc exactly opposite the attacker
    (dot product of direction vectors ≤ –0.707, i.e., angle ≥ 135°).
    Soft geometry: ≤ –0.5 (angle ≥ 120°).
    """
    # Attacker must be adjacent to target for flanking to apply
    if distance_ft(attacker.pos, target.pos, board.diagonal_mode) > 5:
        return False
    # hard: only strictly collinear positions yield dot=-1.0; -0.95 excludes
    # the 1-off-axis cases (dot≈-0.707) that soft allows at threshold -0.5
    threshold = -0.95 if board.flank_geometry == "hard" else -0.5
    atk_dir = _direction(target.pos, attacker.pos)
    for ally in board.tokens:
        if ally is attacker or ally is target:
            continue
        if ally.team != attacker.team:
            continue
        if not ally.active:
            continue
        # ally must be adjacent to target (within 5 ft)
        if distance_ft(ally.pos, target.pos, board.diagonal_mode) > 5:
            continue
        ally_dir = _direction(target.pos, ally.pos)
        if _dot(atk_dir, ally_dir) <= threshold:
            return True
    return False


def ranged_in_melee(attacker: Token, board: Board) -> bool:
    """Return True if attacker has an enemy token adjacent (within 5 ft)."""
    for token in board.tokens:
        if token.team == attacker.team:
            continue
        if distance_ft(attacker.pos, token.pos, board.diagonal_mode) <= 5:
            return True
    return False
