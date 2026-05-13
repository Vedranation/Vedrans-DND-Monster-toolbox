"""Initiative tracker domain model."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine import dice


@dataclass
class InitiativeEntry:
    name: str
    initiative: int
    is_player: bool
    is_active: bool = True


def roll_initiative(mod: int = 0) -> int:
    return dice.roll_die("d20") + mod


def sort_entries(entries: list[InitiativeEntry]) -> list[InitiativeEntry]:
    return sorted(entries, key=lambda e: e.initiative, reverse=True)
