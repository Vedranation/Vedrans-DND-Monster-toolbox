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

from engine.board import Board, GridPosition, Team, Token
from engine.combat import CombatSettings
from engine.conditions import Condition
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
    target_overrides: dict = field(default_factory=dict)  # token_id → manually chosen target_id
    initiative: list = field(default_factory=list)        # [{id,name,initiative,mod,is_player,is_active}]
    casters: list = field(default_factory=list)           # [{id,name,level,spells,slots_used}]
    n_casters: int = 1  # round-tripped for preset compatibility
    _mon_seq: int = 0
    _ply_seq: int = 0
    _tok_seq: int = 0
    _init_seq: int = 0
    _caster_seq: int = 0

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


def token_dict(t: Token) -> dict:
    return {
        "id": t.id, "kind": t.kind, "data_ref": t.data_ref,
        "col": t.pos.col, "row": t.pos.row, "hp": t.hp, "max_hp": t.max_hp,
        "attack_range_ft": t.attack_range_ft,
        "ignore_ranged_in_melee": t.ignore_ranged_in_melee,
        "highlight_range_ft": t.highlight_range_ft,
        "sight_invisible_range": t.sight_invisible_range,
        "conditions": sorted(c.value for c in t.conditions),
        "charmed_by": t.charmed_by,
        "color": t.color,
        "show_range": t.show_range,
        "active": t.active, "team": t.team,
    }


def board_dict(state: AppState) -> dict:
    b = state.board
    return {
        "width": b.width, "height": b.height,
        "tokens": [token_dict(t) for t in b.tokens],
        "teams": [{"name": tm.name, "color": tm.color} for tm in b.teams],
        "diagonal_mode": b.diagonal_mode, "flank_geometry": b.flank_geometry,
        "flank_benefit": b.flank_benefit, "range_mode": b.range_mode,
    }


def find_free_cell(board: Board, kind: str) -> GridPosition:
    start_col = 0 if kind == "monster" else board.width - 1
    step = 1 if kind == "monster" else -1
    occupied = {(t.pos.col, t.pos.row) for t in board.tokens}
    for r in range(board.height):
        for dc in range(board.width):
            c = start_col + dc * step
            if 0 <= c < board.width and (c, r) not in occupied:
                return GridPosition(c, r)
    return GridPosition(start_col, 0)


def add_board_token(state: AppState, kind: str, ref_id: str, col=None, row=None) -> Token | None:
    data = state.monsters.get(ref_id) if kind == "monster" else state.players.get(ref_id)
    if data is None:
        return None
    state._tok_seq += 1
    pos = GridPosition(col, row) if col is not None and row is not None else find_free_cell(state.board, kind)
    senses = getattr(data, "senses", {}) or {}
    tok = Token(
        id=f"t{state._tok_seq}", kind=kind, data_ref=data.name, pos=pos,
        hp=data.max_hp, max_hp=data.max_hp,
        attack_range_ft=data.attack_range_ft,
        ignore_ranged_in_melee=data.ignore_ranged_in_melee,
        highlight_range_ft=data.highlight_range_ft,
        sight_invisible_range=max(senses.get("blindsight", 0), senses.get("truesight", 0)),
        color=getattr(data, "color", "") or "",
        show_range=getattr(data, "show_range", False),
    )
    # The token's default team (Players/Monsters from kind) may have been deleted —
    # fall back to an existing team (the last one) so it never lands on a phantom team.
    team_names = [tm.name for tm in state.board.teams]
    if team_names and tok.team not in team_names:
        tok.team = team_names[-1]
    state.board.tokens.append(tok)
    return tok


def token_by_id(state: AppState, tid: str) -> Token | None:
    return next((t for t in state.board.tokens if t.id == tid), None)


def token_from_dict(d: dict) -> Token:
    """Reconstruct a Token from its serialized (token_dict) form."""
    return Token(
        id=d["id"], kind=d.get("kind", "monster"), data_ref=d.get("data_ref", ""),
        pos=GridPosition(d.get("col", 0), d.get("row", 0)),
        hp=d.get("hp", 0), max_hp=d.get("max_hp", 0),
        attack_range_ft=d.get("attack_range_ft", 5),
        ignore_ranged_in_melee=d.get("ignore_ranged_in_melee", False),
        highlight_range_ft=d.get("highlight_range_ft", 5),
        sight_invisible_range=d.get("sight_invisible_range", 0),
        color=d.get("color", ""),
        show_range=d.get("show_range", False),
        conditions=conditions_from_values(d.get("conditions", [])),
        charmed_by=d.get("charmed_by"),
        active=d.get("active", True), team=d.get("team", ""),
    )


def _max_seq(ids, prefix: str) -> int:
    """Highest numeric suffix among ids like 't12' (0 if none) — to resume id counters."""
    best = 0
    for i in ids:
        s = str(i)
        if s.startswith(prefix) and s[len(prefix):].isdigit():
            best = max(best, int(s[len(prefix):]))
    return best


def conditions_from_values(values) -> set:
    """['poisoned', …] → set[Condition], ignoring unknown strings."""
    out = set()
    for v in values or []:
        try:
            out.add(Condition(v))
        except ValueError:
            pass
    return out


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
        # Web-app extensions (ignored by the desktop app, which skips unknown keys).
        "casters": state.casters,
        "initiative": state.initiative,
        "Board_obj": board_dict(state),
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

    # Web-app extensions. Absent in desktop/legacy presets → reset to empty so a
    # load fully defines the scenario rather than leaving stale state behind.
    state.casters = list(data.get("casters", []))
    state._caster_seq = _max_seq((c.get("id") for c in state.casters), "c")

    state.initiative = list(data.get("initiative", []))
    state._init_seq = _max_seq((e.get("id") for e in state.initiative), "i")

    board_obj = data.get("Board_obj")
    b = state.board
    if board_obj is not None:
        b.width = board_obj.get("width", b.width)
        b.height = board_obj.get("height", b.height)
        b.tokens = [token_from_dict(t) for t in board_obj.get("tokens", [])]
        teams = board_obj.get("teams")
        if teams:
            b.teams = [Team(tm["name"], tm.get("color", "#888")) for tm in teams]
        b.diagonal_mode = board_obj.get("diagonal_mode", b.diagonal_mode)
        b.flank_geometry = board_obj.get("flank_geometry", b.flank_geometry)
        b.flank_benefit = board_obj.get("flank_benefit", b.flank_benefit)
        b.range_mode = board_obj.get("range_mode", b.range_mode)
        state._tok_seq = _max_seq((t.id for t in b.tokens), "t")
    else:
        b.tokens = []
        state._tok_seq = 0
    state.target_overrides = {}
