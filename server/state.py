"""In-memory application state for the web server + preset bridge.

`AppState` is the server-side replacement for the Tkinter `GlobalStateManager`
domain data — pure dataclasses, no Tk. One `AppState` instance per process
(single-session, matching the desktop app today).

The preset bridge (`state_to_preset_data` / `apply_preset_data`) reuses the
schema-v2 serializers in persistence.appstate, so presets written by the server
and the desktop app are mutually loadable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.board import Board
from engine.combat import CombatSettings
from engine.models import MonsterData, PlayerData
from persistence.appstate import (
    deserialize_monster,
    deserialize_player,
    serialize_monster,
    serialize_player,
)


@dataclass
class AppState:
    monsters: dict[str, MonsterData] = field(default_factory=dict)
    players: dict[str, PlayerData] = field(default_factory=dict)
    spell_library: list[dict] = field(default_factory=list)
    board: Board = field(default_factory=Board)
    combat: CombatSettings = field(default_factory=CombatSettings)
    auto_disable_zero_hp: bool = True
    ignore_resistances: bool = False
    n_casters: int = 1  # round-tripped for preset compatibility (casters not modelled yet)
    _mon_seq: int = 0
    _ply_seq: int = 0

    # ── roster mutation ──────────────────────────────────────────────────
    def add_monster(self, data: MonsterData) -> str:
        self._mon_seq += 1
        mid = f"m{self._mon_seq}"
        self.monsters[mid] = data
        return mid

    def add_player(self, data: PlayerData) -> str:
        self._ply_seq += 1
        pid = f"p{self._ply_seq}"
        self.players[pid] = data
        return pid


# Module-level singleton (one session per process).
STATE = AppState()


def reset() -> None:
    """Replace the singleton with a fresh state (used by tests)."""
    global STATE
    STATE = AppState()


# ── API snapshots ────────────────────────────────────────────────────────────

def monster_entry(mid: str, data: MonsterData) -> dict:
    """API representation of a monster: stable id + schema-v2 fields."""
    return {"id": mid, **serialize_monster(data)}


def player_entry(pid: str, data: PlayerData) -> dict:
    return {"id": pid, **serialize_player(data)}


def settings_dict(state: AppState) -> dict:
    c = state.combat
    b = state.board
    return {
        "meets_it_beats_it": c.meets_it_beats_it,
        "crits_double_dmg": c.crits_double_dmg,
        "crits_extra_die_is_max": c.crits_extra_die_is_max,
        "nat1_always_miss": c.nat1_always_miss,
        "adv_combine": c.adv_combine,
        "adv_mode": c.adv_mode,
        "auto_disable_zero_hp": state.auto_disable_zero_hp,
        "ignore_resistances": state.ignore_resistances,
        "board_diagonal_mode": b.diagonal_mode,
        "board_flank_geometry": b.flank_geometry,
        "board_flank_benefit": b.flank_benefit,
        "board_range_mode": b.range_mode,
    }


def apply_settings(state: AppState, patch: dict) -> None:
    """Partial update — only keys present in `patch` are changed."""
    c = state.combat
    for key in ("meets_it_beats_it", "crits_double_dmg", "crits_extra_die_is_max",
                "nat1_always_miss", "adv_combine", "adv_mode"):
        if key in patch:
            setattr(c, key, patch[key])
    if "auto_disable_zero_hp" in patch:
        state.auto_disable_zero_hp = patch["auto_disable_zero_hp"]
    if "ignore_resistances" in patch:
        state.ignore_resistances = patch["ignore_resistances"]
    b = state.board
    if "board_diagonal_mode" in patch:
        b.diagonal_mode = patch["board_diagonal_mode"]
    if "board_flank_geometry" in patch:
        b.flank_geometry = patch["board_flank_geometry"]
    if "board_flank_benefit" in patch:
        b.flank_benefit = patch["board_flank_benefit"]
    if "board_range_mode" in patch:
        b.range_mode = patch["board_range_mode"]


def snapshot(state: AppState) -> dict:
    """Full state for the client's initial load."""
    return {
        "monsters": [monster_entry(mid, m) for mid, m in state.monsters.items()],
        "players": [player_entry(pid, p) for pid, p in state.players.items()],
        "spell_library": state.spell_library,
        "settings": settings_dict(state),
    }


# ── preset bridge (schema-v2, desktop-compatible) ──────────────────────────────

def state_to_preset_data(state: AppState) -> dict:
    c = state.combat
    b = state.board
    return {
        "Meets_it_beats_it_bool": c.meets_it_beats_it,
        "Crits_double_dmg_bool": c.crits_double_dmg,
        "Crits_extra_die_is_max_bool": c.crits_extra_die_is_max,
        "Nat1_always_miss_bool": c.nat1_always_miss,
        "Adv_combine_bool": c.adv_combine,
        "Adv_mode": c.adv_mode,
        "Auto_disable_zero_hp_bool": state.auto_disable_zero_hp,
        "Ignore_resistances_bool": state.ignore_resistances,
        "Board_diagonal_mode": b.diagonal_mode,
        "Board_flank_geometry": b.flank_geometry,
        "Board_flank_benefit": b.flank_benefit,
        "Board_range_mode": b.range_mode,
        "spell_library": state.spell_library,
        "N_casters_int": state.n_casters,
        "N_targets_int": len(state.players),
        "Target_obj_list": [serialize_player(p) for p in state.players.values()],
        "N_monsters_int": len(state.monsters),
        "Monster_obj_list": [serialize_monster(m) for m in state.monsters.values()],
    }


def apply_preset_data(state: AppState, data: dict) -> None:
    """Load a preset dict into `state`, mutating it in place (backward-compatible)."""
    c = state.combat
    c.meets_it_beats_it = data.get("Meets_it_beats_it_bool", c.meets_it_beats_it)
    c.crits_double_dmg = data.get("Crits_double_dmg_bool", c.crits_double_dmg)
    c.crits_extra_die_is_max = data.get("Crits_extra_die_is_max_bool", c.crits_extra_die_is_max)
    c.nat1_always_miss = data.get("Nat1_always_miss_bool", c.nat1_always_miss)
    c.adv_combine = data.get("Adv_combine_bool", c.adv_combine)
    c.adv_mode = data.get("Adv_mode", c.adv_mode)
    state.auto_disable_zero_hp = data.get("Auto_disable_zero_hp_bool", state.auto_disable_zero_hp)
    state.ignore_resistances = data.get("Ignore_resistances_bool", state.ignore_resistances)
    b = state.board
    b.diagonal_mode = data.get("Board_diagonal_mode", b.diagonal_mode)
    b.flank_geometry = data.get("Board_flank_geometry", b.flank_geometry)
    b.flank_benefit = data.get("Board_flank_benefit", b.flank_benefit)
    b.range_mode = data.get("Board_range_mode", b.range_mode)

    state.spell_library = list(data.get("spell_library", []))
    state.n_casters = data.get("N_casters_int", state.n_casters)

    state.players.clear()
    state._ply_seq = 0
    for entry in data.get("Target_obj_list", []):
        state.add_player(deserialize_player(entry))

    state.monsters.clear()
    state._mon_seq = 0
    for entry in data.get("Monster_obj_list", []):
        state.add_monster(deserialize_monster(entry))
