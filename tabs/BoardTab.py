"""Battle Board tab — Tkinter Canvas grid with drag-and-drop tokens."""

from __future__ import annotations

import colorsys
import hashlib
import tkinter as tk
from tkinter import colorchooser, messagebox, simpledialog, ttk

from engine.board import Board, GridPosition, Team, Token, distance_ft, is_flanking, ranged_in_melee
from engine.conditions import Condition
from engine.combat import resolve_typed_damage
from engine.inference import compute_roll_type_modifiers, flanking_to_hit_bonus, suggest_targets
from engine.models import PlayerData
from GlobalStateManager import GSM

_CELL = 25          # pixels per grid cell
_COLS = 20
_ROWS = 20
_CANVAS_W = _COLS * _CELL
_CANVAS_H = _ROWS * _CELL
_CTRL_W = 175       # left control panel width
_PAD = 5

_COLOR_MONSTER = "#e05555"
_COLOR_PLAYER = "#7aaaf0"
_COLOR_INACTIVE = "#aaaaaa"
_COLOR_RANGE_HL = "#ffffaa"
_COLOR_FLANK_HL = "#aaffaa"
_COLOR_GRID = "#cccccc"
_COLOR_SELECTED = "#ff6600"      # orange outline for selected tokens
_COLOR_TARGET_IN = "#22aa44"     # green arrow — target within attack range
_COLOR_TARGET_OUT = "#cc6600"    # orange arrow — target out of attack range
_OVAL_R = 10        # token oval radius in pixels
_BAR_H = 4          # HP bar height in pixels
_TEAM_DOT_R = 4     # team-color indicator dot radius
# Palette cycled when adding new teams.
_TEAM_PALETTE = ["#3a6ea5", "#a53a3a", "#3a8a4a", "#8a6a2a", "#6a3a8a", "#2a8a8a", "#a53a7a", "#555555"]


def BattleBoard(board_frame: tk.Frame) -> None:
    """Build the Battle Board tab UI inside board_frame."""
    board_frame.columnconfigure(0, weight=0)
    board_frame.columnconfigure(1, weight=1)
    board_frame.rowconfigure(0, weight=1)

    # ── left control panel ────────────────────────────────────────────────────
    ctrl = tk.Frame(board_frame, width=_CTRL_W, relief="groove", bd=1)
    ctrl.grid(row=0, column=0, sticky="ns", padx=_PAD, pady=_PAD)
    ctrl.pack_propagate(False)  # children use pack — this is the correct propagate call

    tk.Label(ctrl, text="Battle Board", font=GSM.Title_font).pack(anchor="w", padx=4, pady=(6, 2))

    _mon_btn = tk.Button(ctrl, text="+ Monster token", command=lambda: _add_token("monster"), width=16)
    _mon_btn.pack(anchor="w", padx=4, pady=2)
    _ply_btn = tk.Button(ctrl, text="+ Player token", command=lambda: _add_token("player"), width=16)
    _ply_btn.pack(anchor="w", padx=4, pady=2)
    # Ctrl+click adds one of every roster entry. "break" stops the normal command firing.
    _mon_btn.bind("<Control-Button-1>", lambda e: (_add_all_tokens("monster"), "break")[1])
    _ply_btn.bind("<Control-Button-1>", lambda e: (_add_all_tokens("player"), "break")[1])
    tk.Label(ctrl, text="(Ctrl+click: add one of each)", font=("Helvetica", 7), fg="#666").pack(
        anchor="w", padx=4
    )

    ttk.Separator(ctrl, orient="horizontal").pack(fill="x", padx=4, pady=4)

    tk.Label(ctrl, text="Legend:", font=("Helvetica", 8, "bold")).pack(anchor="w", padx=4)
    tk.Label(ctrl, text="● Monster", fg=_COLOR_MONSTER).pack(anchor="w", padx=8)
    tk.Label(ctrl, text="● Player", fg=_COLOR_PLAYER).pack(anchor="w", padx=8)
    tk.Label(ctrl, text="● Inactive", fg=_COLOR_INACTIVE).pack(anchor="w", padx=8)

    ttk.Separator(ctrl, orient="horizontal").pack(fill="x", padx=4, pady=4)

    info_var = tk.StringVar(value="Click a token\nto inspect.")
    tk.Label(
        ctrl, textvariable=info_var, justify="left",
        wraplength=_CTRL_W - 10, font=("Helvetica", 8)
    ).pack(anchor="w", fill="x", padx=4, pady=2)

    ttk.Separator(ctrl, orient="horizontal").pack(fill="x", padx=4, pady=4)

    tk.Button(ctrl, text="Resolve Board", command=lambda: _resolve_board(),
              bg="#3355cc", fg="white", width=14).pack(anchor="w", padx=4, pady=2)

    tk.Button(ctrl, text="Clear deactivated", command=lambda: _clear_deactivated(),
              width=14).pack(anchor="w", padx=4, pady=2)

    tk.Button(ctrl, text="Clear board", command=lambda: _clear_board(),
              fg="white", bg="#aa3333", width=14).pack(anchor="w", padx=4, pady=2)

    # ── canvas ────────────────────────────────────────────────────────────────
    canvas_frame = tk.Frame(board_frame)
    canvas_frame.grid(row=0, column=1, sticky="nsew", padx=_PAD, pady=_PAD)

    # Team bar above the canvas — drag a token onto a box to reassign its team.
    team_bar = tk.Frame(canvas_frame)
    team_bar.pack(side="top", fill="x", pady=(0, 4))

    canvas = tk.Canvas(canvas_frame, width=_CANVAS_W, height=_CANVAS_H, bg="white", cursor="crosshair")
    canvas.pack()

    # ── state ─────────────────────────────────────────────────────────────────
    # token_id → (oval_id, label_id, [hpbar_item_ids…])
    _token_canvas: dict[str, tuple[int, int, list[int]]] = {}
    _drag: dict = {"token_id": None, "offset_x": 0, "offset_y": 0, "initial_positions": {}}
    # token_ids: full selection set; primary_id: last-clicked (drives info panel & range display)
    _selected: dict = {"token_ids": set(), "primary_id": None}
    # monster_token_id → player_token_id (manually set or auto-assigned)
    _targets: dict[str, str | None] = {}
    _token_counter: list[int] = [0]
    _last_added: dict = {"display": None}   # remembers last pick in the add-token dialog
    _team_boxes: list = []                  # team-bar drop-target widgets (carry ._team_name)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _board() -> Board:
        return GSM.Board_state

    def _token_by_id(tid: str) -> Token | None:
        return next((t for t in _board().tokens if t.id == tid), None)

    def _cell_center(col: int, row: int) -> tuple[int, int]:
        return col * _CELL + _CELL // 2, row * _CELL + _CELL // 2

    def _nearest_cell(px: int, py: int) -> tuple[int, int]:
        col = max(0, min(_COLS - 1, px // _CELL))
        row = max(0, min(_ROWS - 1, py // _CELL))
        return col, row

    def _subspecies_color(data_ref: str, kind: str) -> str:
        """Deterministic per-name color shade within the monster (red) or player (blue) family."""
        seed = int(hashlib.md5(data_ref.encode()).hexdigest()[:6], 16) / 0xFFFFFF
        if kind == "monster":
            hue = ((seed * 60) - 30) / 360  # ±30° around red
            r, g, b = colorsys.hsv_to_rgb(hue, 0.68, 0.87)
        else:
            hue = (195 + seed * 65) / 360  # 195°–260°: sky-blue to blue-purple
            r, g, b = colorsys.hsv_to_rgb(hue, 0.50, 0.94)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def _token_color(token: Token) -> str:
        if not token.active:
            return _COLOR_INACTIVE
        return _subspecies_color(token.data_ref, token.kind)

    # ── teams ───────────────────────────────────────────────────────────────

    def _team_color(name: str) -> str:
        return next((t.color for t in _board().teams if t.name == name), "#888888")

    def _assign_team(team_name: str, tids: list[str]) -> None:
        for tid in tids:
            tok = _token_by_id(tid)
            if tok is not None:
                tok.team = team_name
        _refresh_targets()
        _refresh_team_bar()
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        if primary:
            _update_info(primary)
        _redraw_all()

    def _team_at_pointer(x_root: int, y_root: int) -> str | None:
        """If the screen point is over a team box, return that team's name."""
        w = canvas.winfo_containing(x_root, y_root)
        while w is not None:
            name = getattr(w, "_team_name", None)
            if name is not None:
                return name
            w = getattr(w, "master", None)
        return None

    def _add_team() -> None:
        name = simpledialog.askstring("Add team", "Team name:", parent=canvas)
        if not name:
            return
        name = name.strip()
        if not name or any(t.name == name for t in _board().teams):
            return
        color = _TEAM_PALETTE[len(_board().teams) % len(_TEAM_PALETTE)]
        _board().teams.append(Team(name, color))
        _refresh_team_bar()

    def _rename_team(old: str) -> None:
        new = simpledialog.askstring("Rename team", "New name:", initialvalue=old, parent=canvas)
        if not new:
            return
        new = new.strip()
        if not new or any(t.name == new for t in _board().teams):
            return
        for t in _board().teams:
            if t.name == old:
                t.name = new
        for tok in _board().tokens:
            if tok.team == old:
                tok.team = new
        _refresh_team_bar()
        _redraw_all()

    def _recolor_team(name: str) -> None:
        current = _team_color(name)
        chosen = colorchooser.askcolor(color=current, title=f"Color for {name}", parent=canvas)
        if not chosen or not chosen[1]:
            return
        for t in _board().teams:
            if t.name == name:
                t.color = chosen[1]
        _refresh_team_bar()
        _redraw_all()

    def _delete_team(name: str) -> None:
        teams = _board().teams
        if len(teams) <= 1:
            messagebox.showinfo("Teams", "Can't delete the last team.", parent=canvas)
            return
        fallback = next(t.name for t in teams if t.name != name)
        for tok in _board().tokens:
            if tok.team == name:
                tok.team = fallback
        _board().teams = [t for t in teams if t.name != name]
        _refresh_targets()
        _refresh_team_bar()
        _redraw_all()

    def _team_box_menu(event: tk.Event, name: str) -> None:
        menu = tk.Menu(canvas, tearoff=0)
        menu.add_command(label=f"Team: {name}", state="disabled")
        menu.add_separator()
        menu.add_command(label="Rename…", command=lambda: _rename_team(name))
        menu.add_command(label="Change color…", command=lambda: _recolor_team(name))
        menu.add_command(label="Delete", command=lambda: _delete_team(name))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _refresh_team_bar() -> None:
        for w in team_bar.winfo_children():
            w.destroy()
        _team_boxes.clear()
        tk.Label(team_bar, text="Teams (drag tokens here):",
                 font=("Helvetica", 8, "bold")).pack(side="left", padx=(2, 6))
        counts: dict[str, int] = {}
        for tok in _board().tokens:
            counts[tok.team] = counts.get(tok.team, 0) + 1
        for team in _board().teams:
            box = tk.Frame(team_bar, bg=team.color, bd=2, relief="raised")
            lbl = tk.Label(box, text=f"{team.name} ({counts.get(team.name, 0)})",
                           bg=team.color, fg="white", font=("Helvetica", 8, "bold"), padx=8, pady=5)
            lbl.pack()
            box.pack(side="left", padx=3)
            for w in (box, lbl):
                w._team_name = team.name
                w.bind("<Button-3>", lambda e, n=team.name: _team_box_menu(e, n))
            _team_boxes.append(box)
        tk.Button(team_bar, text="+ Team", command=_add_team).pack(side="left", padx=(8, 2))

    # ── targeting ─────────────────────────────────────────────────────────────

    def _auto_target(m_token: Token) -> str | None:
        """Return the ID of the best enemy-team target for m_token under current board settings."""
        board = _board()
        enemy_tokens = [t for t in board.tokens if t.team != m_token.team and t.active]
        if not enemy_tokens:
            return None
        enemy_tokens.sort(key=lambda t: distance_ft(m_token.pos, t.pos, board.diagonal_mode))
        if board.range_mode == "block":
            in_range = [t for t in enemy_tokens
                        if distance_ft(m_token.pos, t.pos, board.diagonal_mode) <= m_token.attack_range_ft]
            return in_range[0].id if in_range else None
        return enemy_tokens[0].id  # warn / none: nearest regardless of range

    def _refresh_targets() -> None:
        """Keep _targets consistent: drop refs that are gone/inactive/now-allied, auto-assign missing."""
        board = _board()
        # Invalidate stale assignments (target removed, deactivated, or moved to attacker's team)
        for mid in list(_targets.keys()):
            tgt = _targets[mid]
            if tgt is None:
                continue
            attacker = _token_by_id(mid)
            target = _token_by_id(tgt)
            if attacker is None or target is None or not target.active or target.team == attacker.team:
                _targets[mid] = None
        # Auto-assign active monsters with no valid target
        for m_token in board.tokens:
            if m_token.kind != "monster" or not m_token.active:
                continue
            if _targets.get(m_token.id) is None:
                _targets[m_token.id] = _auto_target(m_token)

    def _retarget_selected() -> None:
        """Cycle target(s) for selected monster(s) (R hotkey).

        Single selection: respects block/warn — only in-range targets cycle in block mode;
        shows warning if none are reachable.
        Multi-selection: computes average group position to order candidates, assigns the
        same target to all selected monsters; in block mode silently skips monsters that
        individually can't reach the chosen target (no warning shown).
        """
        board = _board()
        primary_id = _selected["primary_id"]
        if not primary_id:
            return
        primary_token = _token_by_id(primary_id)
        if primary_token is None or primary_token.kind != "monster":
            return

        selected_monster_tids = [
            tid for tid in _selected["token_ids"]
            if (t := _token_by_id(tid)) is not None and t.kind == "monster" and t.active
        ]
        is_multi = len(selected_monster_tids) > 1

        p_tokens = [t for t in board.tokens if t.team != primary_token.team and t.active]
        if not p_tokens:
            return

        if is_multi:
            # Sort players by distance from the group's average grid position
            sel_tokens = [_token_by_id(tid) for tid in selected_monster_tids]
            sel_tokens = [t for t in sel_tokens if t is not None]
            avg_pos = GridPosition(
                round(sum(t.pos.col for t in sel_tokens) / len(sel_tokens)),
                round(sum(t.pos.row for t in sel_tokens) / len(sel_tokens)),
            )
            p_tokens.sort(key=lambda t: distance_ft(avg_pos, t.pos, board.diagonal_mode))
            ids = [t.id for t in p_tokens]
        else:
            p_tokens.sort(key=lambda t: distance_ft(primary_token.pos, t.pos, board.diagonal_mode))
            if board.range_mode == "block":
                p_tokens = [
                    t for t in p_tokens
                    if distance_ft(primary_token.pos, t.pos, board.diagonal_mode) <= primary_token.attack_range_ft
                ]
                if not p_tokens:
                    messagebox.showinfo(
                        "Resolve Board",
                        f"Blocked by range — no valid targets for: {primary_token.data_ref}",
                    )
                    return
            ids = [t.id for t in p_tokens]

        # Advance one step past the primary token's current target
        current = _targets.get(primary_id)
        next_idx = (ids.index(current) + 1) % len(ids) if current in ids else 0
        chosen_id = ids[next_idx]
        chosen_token = _token_by_id(chosen_id)

        if is_multi:
            for sel_tid in selected_monster_tids:
                sel_token = _token_by_id(sel_tid)
                if sel_token is None:
                    continue
                # In block mode skip monsters that individually can't reach the chosen target
                if board.range_mode == "block" and chosen_token is not None:
                    if distance_ft(sel_token.pos, chosen_token.pos, board.diagonal_mode) > sel_token.attack_range_ft:
                        continue
                _targets[sel_tid] = chosen_id
        else:
            _targets[primary_id] = chosen_id

        _draw_target_lines()
        canvas.tag_raise("target_line")
        _raise_tokens()
        _update_info(_token_by_id(primary_id))

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw_grid() -> None:
        canvas.delete("grid")
        for c in range(_COLS + 1):
            canvas.create_line(c * _CELL, 0, c * _CELL, _CANVAS_H, fill=_COLOR_GRID, tags="grid")
        for r in range(_ROWS + 1):
            canvas.create_line(0, r * _CELL, _CANVAS_W, r * _CELL, fill=_COLOR_GRID, tags="grid")

    def _draw_target_lines() -> None:
        canvas.delete("target_line")
        board = _board()
        for m_token in board.tokens:
            if not m_token.active or m_token.kind != "monster":
                continue
            target_id = _targets.get(m_token.id)
            if not target_id:
                continue
            p_token = _token_by_id(target_id)
            if p_token is None or not p_token.active:
                continue
            mx, my = _cell_center(m_token.pos.col, m_token.pos.row)
            px, py = _cell_center(p_token.pos.col, p_token.pos.row)
            dist = distance_ft(m_token.pos, p_token.pos, board.diagonal_mode)
            in_range = dist <= m_token.attack_range_ft
            color = _COLOR_TARGET_IN if in_range else _COLOR_TARGET_OUT
            canvas.create_line(
                mx, my, px, py,
                fill=color, width=1, dash=(5, 3),
                arrow="last", arrowshape=(8, 10, 4),
                tags="target_line",
            )

    def _draw_range_highlight_if_selected() -> None:
        canvas.delete("range_hl")
        tid = _selected["primary_id"]
        if not tid:
            return
        token = _token_by_id(tid)
        if not token:
            return
        rng = token.highlight_range_ft
        for c in range(_COLS):
            for r in range(_ROWS):
                if distance_ft(token.pos, GridPosition(c, r), _board().diagonal_mode) <= rng:
                    canvas.create_rectangle(
                        c * _CELL, r * _CELL, (c + 1) * _CELL, (r + 1) * _CELL,
                        fill=_COLOR_RANGE_HL, outline="", tags="range_hl"
                    )

    def _draw_flank_highlight_if_selected() -> None:
        canvas.delete("flank_hl")
        tid = _selected["primary_id"]
        if not tid:
            return
        token = _token_by_id(tid)
        if not token:
            return
        board = _board()
        for target in board.tokens:
            if target.team == token.team:
                continue
            if is_flanking(token, target, board):
                cx, cy = _cell_center(target.pos.col, target.pos.row)
                canvas.create_oval(
                    cx - _OVAL_R - 4, cy - _OVAL_R - 4,
                    cx + _OVAL_R + 4, cy + _OVAL_R + 4,
                    outline=_COLOR_FLANK_HL, width=3, tags="flank_hl"
                )

    def _draw_hp_bar(token: Token, cx: int, cy: int) -> list[int]:
        """Draw HP bar below the token oval; return list of created canvas item IDs."""
        if token.max_hp <= 0:
            return []
        bar_x0 = cx - _OVAL_R
        bar_y0 = cy + _OVAL_R + 2
        bar_x1 = cx + _OVAL_R
        bar_y1 = bar_y0 + _BAR_H
        ids: list[int] = []
        bg_id = canvas.create_rectangle(bar_x0, bar_y0, bar_x1, bar_y1,
                                        fill="#555555", outline="", tags="hpbar")
        ids.append(bg_id)
        ratio = max(0.0, min(1.0, token.hp / token.max_hp))
        fill_w = int(_OVAL_R * 2 * ratio)
        if fill_w > 0:
            color = "#44cc44" if ratio > 0.5 else ("#ccaa00" if ratio > 0.25 else "#cc3333")
            fill_id = canvas.create_rectangle(bar_x0, bar_y0, bar_x0 + fill_w, bar_y1,
                                              fill=color, outline="", tags="hpbar")
            ids.append(fill_id)
        return ids

    def _draw_tokens() -> None:
        for oid, lid, bar_ids in _token_canvas.values():
            canvas.delete(oid)
            canvas.delete(lid)
            for bid in bar_ids:
                canvas.delete(bid)
        _token_canvas.clear()

        for token in _board().tokens:
            cx, cy = _cell_center(token.pos.col, token.pos.row)
            color = _token_color(token)
            is_sel = token.id in _selected["token_ids"]
            oid = canvas.create_oval(
                cx - _OVAL_R, cy - _OVAL_R, cx + _OVAL_R, cy + _OVAL_R,
                fill=color,
                outline=_COLOR_SELECTED if is_sel else "black",
                width=3 if is_sel else 1,
                tags="token",
            )
            lid = canvas.create_text(
                cx, cy, text=token.data_ref[:6], font=("Helvetica", 6), fill="black", tags="token_label"
            )
            bar_ids = _draw_hp_bar(token, cx, cy)
            # Team-color dot at the token's top-right corner (fill stays species color).
            ddx, ddy = cx + int(_OVAL_R * 0.8), cy - int(_OVAL_R * 0.8)
            dot_id = canvas.create_oval(
                ddx - _TEAM_DOT_R, ddy - _TEAM_DOT_R, ddx + _TEAM_DOT_R, ddy + _TEAM_DOT_R,
                fill=_team_color(token.team), outline="white", width=1, tags="token",
            )
            bar_ids = list(bar_ids) + [dot_id]
            _token_canvas[token.id] = (oid, lid, bar_ids)

            for item_id in (oid, lid):
                canvas.tag_bind(item_id, "<Button-1>",
                                 lambda e, tid=token.id: _on_token_click(e, tid))
                canvas.tag_bind(item_id, "<Double-Button-1>",
                                 lambda e, tid=token.id: _on_token_double_click(e, tid))
                canvas.tag_bind(item_id, "<B1-Motion>",
                                 lambda e, tid=token.id: _on_token_drag(e, tid))
                canvas.tag_bind(item_id, "<ButtonRelease-1>",
                                 lambda e, tid=token.id: _on_token_drop(e, tid))
                canvas.tag_bind(item_id, "<Button-3>",
                                 lambda e, tid=token.id: _on_token_right_click(e, tid))

    def _update_selection_visuals() -> None:
        """Update oval outlines in-place without destroying/recreating token canvas items."""
        for t in _board().tokens:
            ids = _token_canvas.get(t.id)
            if ids is None:
                continue
            oid, _, _ = ids
            is_sel = t.id in _selected["token_ids"]
            canvas.itemconfig(oid,
                              outline=_COLOR_SELECTED if is_sel else "black",
                              width=3 if is_sel else 1)

    def _raise_tokens() -> None:
        canvas.tag_raise("token")
        canvas.tag_raise("token_label")

    def _redraw_all() -> None:
        # Layer order: range_hl → flank_hl → grid → target_lines → tokens
        _draw_range_highlight_if_selected()
        _draw_flank_highlight_if_selected()
        _draw_grid()
        _draw_target_lines()
        _draw_tokens()
        _raise_tokens()

    def _redraw_highlights_only() -> None:
        """Redraw highlights + grid WITHOUT destroying token items (preserves drag bindings)."""
        _draw_range_highlight_if_selected()
        _draw_flank_highlight_if_selected()
        _draw_grid()
        canvas.tag_raise("target_line")
        _raise_tokens()

    # ── token interaction ─────────────────────────────────────────────────────

    def _on_token_click(event: tk.Event, tid: str) -> None:
        ctrl_held = bool(event.state & 0x4)
        if ctrl_held:
            if tid in _selected["token_ids"]:
                _selected["token_ids"].discard(tid)
                if _selected["primary_id"] == tid:
                    _selected["primary_id"] = next(iter(_selected["token_ids"]), None)
            else:
                _selected["token_ids"].add(tid)
                _selected["primary_id"] = tid
        else:
            _selected["token_ids"] = {tid}
            _selected["primary_id"] = tid

        _drag["token_id"] = tid
        _drag["offset_x"] = event.x
        _drag["offset_y"] = event.y
        # Snapshot positions of all selected tokens at drag start
        _drag["initial_positions"] = {
            sel_tid: GridPosition(t.pos.col, t.pos.row)
            for sel_tid in _selected["token_ids"]
            if (t := _token_by_id(sel_tid)) is not None
        }

        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        _update_info(primary)
        canvas.focus_set()
        _update_selection_visuals()
        _redraw_highlights_only()

    def _on_token_double_click(event: tk.Event, tid: str) -> None:
        """Open the roster editor for this token's monster/player object."""
        token = _token_by_id(tid)
        if token is None:
            return
        if token.kind == "monster":
            obj = next((m for m in GSM.Monster_obj_list if m.name_str.get() == token.data_ref), None)
            if obj:
                from tabs.MonsterCreation import OpenMonsterWindow
                OpenMonsterWindow(obj, GSM.RelPosMonsters)
        else:
            obj = next((p for p in GSM.Target_obj_list if p.name_str.get() == token.data_ref), None)
            if obj:
                from tabs.PlayerCreation import OpenPlayerWindow
                OpenPlayerWindow(obj, GSM.RelPosTargets)

    def _toggle_active_selected() -> None:
        """Toggle active/inactive on all selected tokens (hotkey D)."""
        if not _selected["token_ids"]:
            return
        for tid in list(_selected["token_ids"]):
            token = _token_by_id(tid)
            if token:
                token.active = not token.active
        _refresh_targets()
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        _update_info(primary)
        _redraw_all()

    def _remove_selected() -> None:
        """Remove all selected tokens (hotkey Delete/BackSpace)."""
        ids_to_remove = set(_selected["token_ids"])
        if not ids_to_remove:
            return
        _board().tokens = [t for t in _board().tokens if t.id not in ids_to_remove]
        for tid in ids_to_remove:
            _targets.pop(tid, None)
        _selected["token_ids"].clear()
        _selected["primary_id"] = None
        _refresh_targets()
        _refresh_team_bar()
        _update_info(None)
        _redraw_all()

    def _on_token_drag(event: tk.Event, tid: str) -> None:
        if _drag["token_id"] != tid:
            return
        dx = event.x - _drag["offset_x"]
        dy = event.y - _drag["offset_y"]
        for sel_tid in _selected["token_ids"]:
            ids = _token_canvas.get(sel_tid)
            if ids is None:
                continue
            oid, lid, bar_ids = ids
            canvas.move(oid, dx, dy)
            canvas.move(lid, dx, dy)
            for bid in bar_ids:
                canvas.move(bid, dx, dy)
        _drag["offset_x"] = event.x
        _drag["offset_y"] = event.y

    def _on_token_drop(event: tk.Event, tid: str) -> None:
        if _drag["token_id"] != tid:
            return
        _drag["token_id"] = None

        # Dropped onto a team box → reassign team(s) instead of moving.
        team_name = _team_at_pointer(event.x_root, event.y_root)
        if team_name is not None:
            tids = list(_selected["token_ids"]) or [tid]
            _assign_team(team_name, tids)  # redraw snaps token visuals back (positions unchanged)
            return

        new_col, new_row = _nearest_cell(event.x, event.y)
        init_pos = _drag["initial_positions"].get(tid)
        if init_pos is not None:
            dcol = new_col - init_pos.col
            drow = new_row - init_pos.row
            for sel_tid, sel_init in _drag["initial_positions"].items():
                token = _token_by_id(sel_tid)
                if token is None:
                    continue
                token.pos = GridPosition(
                    max(0, min(_COLS - 1, sel_init.col + dcol)),
                    max(0, min(_ROWS - 1, sel_init.row + drow)),
                )
        else:
            token = _token_by_id(tid)
            if token:
                token.pos = GridPosition(new_col, new_row)
        # Re-evaluate targets after movement (positions changed)
        _refresh_targets()
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        if primary:
            _update_info(primary)
        _redraw_all()

    def _on_token_right_click(event: tk.Event, tid: str) -> None:
        # If the right-clicked token isn't in the current selection, single-select it
        if tid not in _selected["token_ids"]:
            _selected["token_ids"] = {tid}
            _selected["primary_id"] = tid
            _update_selection_visuals()

        token = _token_by_id(tid)
        if token is None:
            return

        is_multi = len(_selected["token_ids"]) > 1
        n = len(_selected["token_ids"])
        primary = _token_by_id(_selected["primary_id"]) or token

        menu = tk.Menu(canvas, tearoff=0)
        if is_multi:
            menu.add_command(label=f"{n} tokens selected", state="disabled")
        else:
            menu.add_command(label=f"{token.data_ref} ({token.kind})", state="disabled")
        menu.add_separator()

        # HP
        if is_multi:
            menu.add_command(label="Set HP…", command=_edit_hp_selected)
        else:
            menu.add_command(label="Set HP…", command=lambda: _set_hp(token))
        menu.add_separator()

        # Conditions — label driven by primary token's state; applies to all selected
        cond_menu = tk.Menu(menu, tearoff=0)
        for cond in Condition:
            has_cond = cond in primary.conditions
            label = f"✓ {cond.value}" if has_cond else f"  {cond.value}"
            if is_multi:
                cond_menu.add_command(label=label, command=lambda c=cond: _toggle_condition_selected(c))
            else:
                cond_menu.add_command(label=label, command=lambda c=cond, t=token: _toggle_condition(t, c))
        menu.add_cascade(label="Conditions", menu=cond_menu)
        menu.add_separator()

        # Assign to team — applies to all selected tokens
        team_menu = tk.Menu(menu, tearoff=0)
        for team in _board().teams:
            checked = (not is_multi) and token.team == team.name
            label = f"✓ {team.name}" if checked else f"  {team.name}"
            team_menu.add_command(
                label=label,
                command=lambda n=team.name: _assign_team(n, list(_selected["token_ids"])),
            )
        menu.add_cascade(label="Assign to team", menu=team_menu)
        menu.add_separator()

        # Activate / Deactivate
        if is_multi:
            menu.add_command(label="Toggle active", command=_toggle_active_selected)
        else:
            menu.add_command(
                label="Deactivate" if token.active else "Activate",
                command=lambda: _toggle_active(token),
            )
        menu.add_separator()

        # Remove
        if is_multi:
            menu.add_command(label=f"Remove {n} tokens", command=_remove_selected)
        else:
            menu.add_command(label="Remove token", command=lambda: _remove_token(tid))

        # Mass saving throw — shown when any selected token is a monster
        has_monsters = any(
            _token_by_id(t) is not None and _token_by_id(t).kind == "monster"
            for t in _selected["token_ids"]
        )
        if has_monsters:
            menu.add_separator()
            menu.add_command(label="Mass saving throw…", command=_mass_save_selected)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ── HP editing ────────────────────────────────────────────────────────────

    def _parse_hp_input(raw: str, current_hp: int) -> int | None:
        """Parse '+N', '-N', or 'N'; return new absolute HP or None on bad input."""
        raw = raw.strip()
        try:
            if raw.startswith("+"):
                return current_hp + int(raw[1:])
            if raw.startswith("-"):
                return current_hp - int(raw[1:])
            return int(raw)
        except ValueError:
            return None

    def _clamp_hp(new_hp: int, max_hp: int) -> int:
        return max(0, min(max_hp, new_hp)) if max_hp > 0 else max(0, new_hp)

    def _set_hp(token: Token) -> None:
        raw = simpledialog.askstring(
            "Set HP",
            f"HP for {token.data_ref}  (max {token.max_hp if token.max_hp > 0 else '—'}):\n"
            "+N to add,  -N to subtract,  N to set absolute.",
            initialvalue=str(token.hp), parent=canvas,
        )
        if raw is None:
            return
        new_hp = _parse_hp_input(raw, token.hp)
        if new_hp is None:
            return
        token.hp = _clamp_hp(new_hp, token.max_hp)
        if token.hp == 0 and GSM.Auto_disable_zero_hp_bool.get():
            token.active = False
        _update_info(token)
        _redraw_all()

    def _edit_hp_selected() -> None:
        """H hotkey: single token → per-token dialog; multiple → apply same operation to all."""
        if not _selected["token_ids"]:
            return
        count = len(_selected["token_ids"])
        primary_id = _selected["primary_id"]
        if count == 1 and primary_id:
            token = _token_by_id(primary_id)
            if token:
                _set_hp(token)
            return
        primary = _token_by_id(primary_id) if primary_id else None
        name_hint = f"{primary.data_ref} +{count - 1} others" if primary else f"{count} tokens"
        raw = simpledialog.askstring(
            "Set HP",
            f"HP for {name_hint}:\n+N to add,  -N to subtract,  N to set absolute.",
            initialvalue="", parent=canvas,
        )
        if raw is None:
            return
        for tid in _selected["token_ids"]:
            token = _token_by_id(tid)
            if token is None:
                continue
            new_hp = _parse_hp_input(raw, token.hp)
            if new_hp is None:
                continue
            token.hp = _clamp_hp(new_hp, token.max_hp)
            if token.hp == 0 and GSM.Auto_disable_zero_hp_bool.get():
                token.active = False
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        _update_info(primary)
        _redraw_all()

    def _toggle_condition(token: Token, cond: Condition) -> None:
        if cond not in token.conditions and token.kind == "monster":
            monster_obj = next(
                (m for m in GSM.Monster_obj_list if m.name_str.get() == token.data_ref), None
            )
            if monster_obj is not None and monster_obj.condition_immunities_vars.get(cond.value, tk.BooleanVar()).get():
                messagebox.showwarning(
                    "Condition Immunity",
                    f"{token.data_ref} is immune to {cond.value}.\nApplying anyway.",
                )
        token.conditions.discard(cond) if cond in token.conditions else token.conditions.add(cond)
        _update_info(token)
        _redraw_all()

    def _toggle_condition_selected(cond: Condition) -> None:
        """Toggle a condition on all selected tokens, state driven by primary token."""
        primary = _token_by_id(_selected["primary_id"])
        adding = cond not in (primary.conditions if primary else set())
        if adding:
            immune = [
                t.data_ref for tid in _selected["token_ids"]
                if (t := _token_by_id(tid)) and t.kind == "monster"
                and (obj := next((m for m in GSM.Monster_obj_list if m.name_str.get() == t.data_ref), None))
                and obj.condition_immunities_vars.get(cond.value, tk.BooleanVar()).get()
            ]
            if immune:
                messagebox.showwarning(
                    "Condition Immunity",
                    f"Immune to {cond.value}: {', '.join(immune)}.\nApplying anyway.",
                )
        for tid in list(_selected["token_ids"]):
            t = _token_by_id(tid)
            if t is None:
                continue
            t.conditions.add(cond) if adding else t.conditions.discard(cond)
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        _update_info(primary)
        _redraw_all()

    def _toggle_active(token: Token) -> None:
        token.active = not token.active
        _refresh_targets()
        _update_info(token)
        _redraw_all()

    def _mass_save_selected() -> None:
        """Load selected monster tokens into the Mass Saves tab and switch to it."""
        monster_tokens = [
            t for t in _board().tokens
            if t.id in _selected["token_ids"] and t.kind == "monster"
        ]
        if not monster_tokens:
            return
        groups: dict[str, int] = {}
        for t in monster_tokens:
            groups[t.data_ref] = groups.get(t.data_ref, 0) + 1
        if GSM.Load_mass_saves is not None:
            GSM.Load_mass_saves(groups)
        GSM.Notebook.select(GSM.Mass_roll_frame)

    def _remove_token(tid: str) -> None:
        _board().tokens = [t for t in _board().tokens if t.id != tid]
        _targets.pop(tid, None)
        _selected["token_ids"].discard(tid)
        if _selected["primary_id"] == tid:
            _selected["primary_id"] = next(iter(_selected["token_ids"]), None)
        _refresh_targets()
        _refresh_team_bar()
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        _update_info(primary)
        _redraw_all()

    # ── info panel ────────────────────────────────────────────────────────────

    def _update_info(token: Token | None) -> None:
        if token is None:
            info_var.set("Click a token\nto inspect.")
            return
        board = _board()
        conds = ", ".join(c.value for c in token.conditions) or "none"
        status = "active" if token.active else "inactive"
        hp_str = f"{token.hp}/{token.max_hp}" if token.max_hp > 0 else str(token.hp)
        range_str = f"{token.attack_range_ft}ft"
        if token.ignore_ranged_in_melee:
            range_str += " (xbw)"
        enemies = [t for t in board.tokens if t.team != token.team and t.active]
        if enemies:
            nearest = min(enemies, key=lambda t: distance_ft(token.pos, t.pos, board.diagonal_mode))
            roll_mod = compute_roll_type_modifiers(token, nearest, board, GSM.Adv_mode.get())
            in_melee_str = "yes" if ranged_in_melee(token, board) else "no"
        else:
            roll_mod = "Normal"
            in_melee_str = "no"
        lines = [
            token.data_ref,
            f"HP: {hp_str}  [{status}]",
            f"Team: {token.team}",
            f"Pos: ({token.pos.col},{token.pos.row})",
            f"Conds: {conds}",
            f"Range: {range_str}",
            f"Roll mod: {roll_mod}",
            f"In melee: {in_melee_str}",
            f"HL range: {token.highlight_range_ft}ft",
        ]
        if token.kind == "monster":
            target_id = _targets.get(token.id)
            p_token = _token_by_id(target_id) if target_id else None
            if p_token:
                dist = distance_ft(token.pos, p_token.pos, board.diagonal_mode)
                in_rng = dist <= token.attack_range_ft
                rng_tag = "" if in_rng else " ⚠OOR"
                lines.append(f"Target: {p_token.data_ref} ({dist:.0f}ft){rng_tag}")
            else:
                lines.append("Target: none")
        extra = len(_selected["token_ids"]) - 1
        if extra > 0:
            lines.append(f"+{extra} also selected")
        info_var.set("\n".join(lines))

    # ── add token ─────────────────────────────────────────────────────────────

    def _popup_at_mouse(window: tk.Toplevel) -> None:
        """Position a Toplevel dialog centered on the current mouse pointer."""
        window.update_idletasks()
        w = window.winfo_reqwidth()
        h = window.winfo_reqheight()
        x = canvas.winfo_pointerx() - w // 2
        y = canvas.winfo_pointery() - h // 2
        window.geometry(f"+{x}+{y}")

    def _add_token(kind: str, fixed_pos: GridPosition | None = None) -> None:
        obj_list = GSM.Monster_obj_list if kind == "monster" else GSM.Target_obj_list
        if not obj_list:
            return
        top = tk.Toplevel(canvas)
        top.title(f"Add {kind} token")
        top.resizable(False, False)
        tk.Label(top, text="Select:").pack(padx=8, pady=4)
        listbox = tk.Listbox(top, width=24, height=min(8, len(obj_list)))
        for obj in obj_list:
            listbox.insert("end", obj.name_str.get())
        listbox.selection_set(0)
        listbox.pack(padx=8, pady=4)

        def _confirm() -> None:
            sel = listbox.curselection()
            if not sel:
                top.destroy()
                return
            selected_obj = obj_list[sel[0]]
            pos = fixed_pos if fixed_pos is not None else _find_free_cell(kind)
            top.destroy()
            _place_token_from_obj(kind, selected_obj, pos)

        listbox.bind("<Return>", lambda e: _confirm())
        listbox.bind("<Double-Button-1>", lambda e: _confirm())
        tk.Button(top, text="Add", command=_confirm).pack(pady=4)
        _popup_at_mouse(top)
        top.grab_set()

    def _place_token_from_obj(kind: str, obj, pos: GridPosition) -> None:
        """Create a Token from a roster object and add it at pos."""
        name = obj.name_str.get()
        _token_counter[0] += 1
        tid = f"{kind[0]}_{_token_counter[0]}"
        max_hp = obj.max_hp_int.get() if hasattr(obj, "max_hp_int") else 0
        atk_range = obj.attack_range_ft_int.get() if hasattr(obj, "attack_range_ft_int") else 5
        ignore_pen = obj.ignore_ranged_in_melee_bool.get() if hasattr(obj, "ignore_ranged_in_melee_bool") else False
        hl_range = obj.highlight_range_ft_int.get() if hasattr(obj, "highlight_range_ft_int") else 5
        token = Token(
            id=tid, kind=kind, data_ref=name, pos=pos,
            hp=max_hp, max_hp=max_hp,
            attack_range_ft=atk_range,
            ignore_ranged_in_melee=ignore_pen,
            highlight_range_ft=hl_range,
        )
        _board().tokens.append(token)
        _refresh_targets()
        _refresh_team_bar()
        _redraw_all()

    def _add_token_at_pos(col: int, row: int) -> None:
        """Single combined list: players (alpha) then monsters (alpha). One click to place."""
        entries: list[tuple[str, str, object]] = []
        for obj in sorted(GSM.Target_obj_list, key=lambda o: o.name_str.get()):
            entries.append((f"[P] {obj.name_str.get()}", "player", obj))
        for obj in sorted(GSM.Monster_obj_list, key=lambda o: o.name_str.get()):
            entries.append((f"[M] {obj.name_str.get()}", "monster", obj))
        if not entries:
            return

        top = tk.Toplevel(canvas)
        top.title(f"Add token at ({col}, {row})")
        top.resizable(False, False)
        tk.Label(top, text=f"Place at ({col}, {row}) — [P]=player  [M]=monster").pack(padx=8, pady=(8, 2))

        listbox = tk.Listbox(top, width=26, height=min(12, len(entries)),
                             selectmode="single", exportselection=False)
        for display, _, _ in entries:
            listbox.insert("end", display)

        # Preselect the last-added entry; fall back to index 0
        preselect = 0
        if _last_added["display"] is not None:
            for i, (display, _, _) in enumerate(entries):
                if display == _last_added["display"]:
                    preselect = i
                    break
        listbox.selection_set(preselect)
        listbox.see(preselect)

        listbox.pack(padx=8, pady=4)
        listbox.focus_set()

        def _confirm() -> None:
            sel = listbox.curselection()
            if not sel:
                top.destroy()
                return
            display, kind, obj = entries[sel[0]]
            _last_added["display"] = display
            top.destroy()
            _place_token_from_obj(kind, obj, GridPosition(col, row))

        listbox.bind("<Return>", lambda e: _confirm())
        listbox.bind("<Double-Button-1>", lambda e: _confirm())
        tk.Button(top, text="Add", command=_confirm).pack(pady=(0, 6))
        _popup_at_mouse(top)
        top.grab_set()

    def _add_all_tokens(kind: str) -> None:
        """Ctrl+click 'Add': drop one copy of every roster entry of this kind."""
        obj_list = GSM.Monster_obj_list if kind == "monster" else GSM.Target_obj_list
        for obj in obj_list:
            _place_token_from_obj(kind, obj, _find_free_cell(kind))

    def _find_free_cell(kind: str) -> GridPosition:
        start_col = 0 if kind == "monster" else _COLS - 1
        step = 1 if kind == "monster" else -1
        occupied = {(t.pos.col, t.pos.row) for t in _board().tokens}
        for r in range(_ROWS):
            for dc in range(_COLS):
                c = start_col + dc * step
                if 0 <= c < _COLS and (c, r) not in occupied:
                    return GridPosition(c, r)
        return GridPosition(start_col, 0)

    # ── clear ─────────────────────────────────────────────────────────────────

    def _clear_board() -> None:
        _board().tokens.clear()
        _targets.clear()
        _selected["token_ids"].clear()
        _selected["primary_id"] = None
        _refresh_team_bar()
        _update_info(None)
        _redraw_all()

    def _clear_deactivated() -> None:
        """Remove every inactive token (dead/disabled), keeping active ones."""
        removed = {t.id for t in _board().tokens if not t.active}
        if not removed:
            return
        _board().tokens = [t for t in _board().tokens if t.active]
        for tid in removed:
            _targets.pop(tid, None)
        _selected["token_ids"] -= removed
        if _selected["primary_id"] in removed:
            _selected["primary_id"] = next(iter(_selected["token_ids"]), None)
        _refresh_targets()
        _refresh_team_bar()
        primary = _token_by_id(_selected["primary_id"]) if _selected["primary_id"] else None
        _update_info(primary)
        _redraw_all()

    # ── Resolve Board ─────────────────────────────────────────────────────────

    def _defender_data(p_token: Token) -> PlayerData | None:
        """Build a defense view for a target token (player or enemy-team monster).

        Players use their own PlayerData. Enemy monsters are adapted into a
        PlayerData defense view (AC/HP/conditions; no imposed roll / adamantine)
        so the combat engine can resolve monster-vs-monster attacks unchanged.
        """
        if p_token.kind == "player":
            obj = next((p for p in GSM.Target_obj_list if p.name_str.get() == p_token.data_ref), None)
            return obj.to_data() if obj else None
        obj = next((m for m in GSM.Monster_obj_list if m.name_str.get() == p_token.data_ref), None)
        if obj is None:
            return None
        md = obj.to_data()
        return PlayerData(
            name=md.name,
            ac=md.ac,
            max_hp=md.max_hp,
            imposed_roll_type="Normal",
            adamantine=False,
            passive_perception=md.passive_perception,
            conditions=md.conditions,
        )

    def _defender_damage_mods(p_token: Token) -> tuple[list[str], list[str], list[str]]:
        """(resistances, immunities, vulnerabilities) for a defender token (monsters only).

        Returns empty lists when the global 'ignore damage type modifiers' toggle is on.
        """
        if GSM.Ignore_resistances_bool.get():
            return [], [], []
        if p_token.kind != "monster":
            return [], [], []
        obj = next((m for m in GSM.Monster_obj_list if m.name_str.get() == p_token.data_ref), None)
        if obj is None:
            return [], [], []
        md = obj.to_data()
        return md.damage_resistances, md.damage_immunities, md.damage_vulnerabilities

    def _resolve_board() -> None:
        from engine.combat import CombatSettings, compute_single_attack

        board = _board()
        settings = CombatSettings(
            meets_it_beats_it=GSM.Meets_it_beats_it_bool.get(),
            crits_double_dmg=GSM.Crits_double_dmg_bool.get(),
            crits_extra_die_is_max=GSM.Crits_extra_die_is_max_bool.get(),
            nat1_always_miss=GSM.Nat1_always_miss_bool.get(),
            adv_combine=GSM.Adv_combine_bool.get(),
            adv_mode=GSM.Adv_mode.get(),
        )

        pairs = []
        skipped_blocked: list[str] = []
        for m_token in board.tokens:
            if not m_token.active or m_token.kind != "monster":
                continue
            monster_obj = next(
                (m for m in GSM.Monster_obj_list if m.name_str.get() == m_token.data_ref), None
            )
            if monster_obj is None:
                continue

            # Use the manually-assigned (or auto-assigned) target
            target_id = _targets.get(m_token.id)
            p_token = _token_by_id(target_id) if target_id else None
            if p_token is None or not p_token.active:
                skipped_blocked.append(m_token.data_ref)
                continue

            # Defender may be a player OR an enemy-team monster — resolve a defense view.
            defender_data = _defender_data(p_token)
            if defender_data is None:
                continue

            dist = distance_ft(m_token.pos, p_token.pos, board.diagonal_mode)
            if board.range_mode == "block" and dist > m_token.attack_range_ft:
                skipped_blocked.append(m_token.data_ref)
                continue
            out_of_range = dist > m_token.attack_range_ft

            pairs.append((m_token, p_token, monster_obj, defender_data, out_of_range))

        if skipped_blocked:
            names = ", ".join(skipped_blocked)
            messagebox.showinfo("Resolve Board", f"Blocked by range — no valid targets for: {names}")

        if not pairs:
            if not skipped_blocked:
                messagebox.showinfo("Resolve Board", "No active monster→target pairs found on board.")
            return

        pairs.sort(key=lambda p: (p[1].data_ref, p[0].data_ref))

        results = []
        for m_token, p_token, monster_obj, player_data, out_of_range in pairs:
            monster_data = monster_obj.to_data()
            board_mod = compute_roll_type_modifiers(m_token, p_token, board, settings.adv_mode)
            tohit_bonus = flanking_to_hit_bonus(m_token, p_token, board)
            result = compute_single_attack(
                monster_data, player_data, settings,
                board_tohit_bonus=tohit_bonus,
                board_roll_type_mod=board_mod,
            )
            total_dmg = sum(r.dmg1 + r.dmg2 for r in result.rolls if r.is_hit)
            results.append((m_token, p_token, result, total_dmg, board_mod,
                            player_data.imposed_roll_type, out_of_range, tohit_bonus))

        _show_resolve_dialog(results)

    def _show_resolve_dialog(results: list) -> None:
        dlg = tk.Toplevel(canvas)
        dlg.title("Board Combat Results")
        dlg.resizable(False, False)

        tk.Label(dlg, text="Board Combat Results", font=GSM.Title_font).pack(padx=10, pady=(8, 4))

        outer = tk.Frame(dlg)
        outer.pack(padx=10, pady=4, fill="both")

        apply_vars: list[tuple[tk.BooleanVar, Token, int]] = []
        row_idx = 0

        _F8 = ("Helvetica", 8)
        _F8B = ("Helvetica", 8, "bold")

        for m_token, p_token, result, total_dmg, board_mod, player_imposed, out_of_range, tohit_bonus in results:
            mods_str = f"board: {board_mod}"
            if player_imposed != "Normal":
                mods_str += f" | imposes: {player_imposed}"
            if tohit_bonus:
                mods_str += f" | +{tohit_bonus} flank"
            header = f"{m_token.data_ref} → {p_token.data_ref}   [{mods_str}]"
            if out_of_range:
                header += "  ⚠ OUT OF RANGE"
            hdr_color = "#cc6600" if out_of_range else "black"
            tk.Label(outer, text=header, font=_F8B, anchor="w", fg=hdr_color).grid(
                row=row_idx, column=0, columnspan=3, sticky="w", padx=4, pady=(6, 1)
            )
            row_idx += 1

            for r in result.rolls:
                roll_type_tag = f" [{r.roll_type}]" if r.roll_type != "Normal" else ""
                crit_tag = " (CRIT)" if r.is_crit else ""
                outcome = "CRIT" if r.is_crit else ("MISS" if not r.is_hit else "HIT")

                dice_frame = tk.Frame(outer)
                tk.Label(dice_frame, text=f"  [{r.attack_name}]{roll_type_tag}  d20=",
                         font=_F8, anchor="w").pack(side="left")
                tk.Label(dice_frame, text=str(r.all_d20s[0] if r.all_d20s else r.d20),
                         font=_F8B).pack(side="left")
                for dropped in (r.all_d20s[1:] if r.all_d20s else []):
                    tk.Label(dice_frame, text=f"|{dropped}", fg="#aaaaaa", font=_F8).pack(side="left")
                tk.Label(dice_frame, text=f"{crit_tag} → total {r.total}",
                         font=_F8, anchor="w").pack(side="left")
                dice_frame.grid(row=row_idx, column=0, sticky="w", padx=4, pady=1)

                outcome_color = "#cc3333" if outcome == "MISS" else ("#cc7700" if outcome == "CRIT" else "#228822")
                tk.Label(outer, text=outcome, fg=outcome_color, font=_F8B, width=5).grid(
                    row=row_idx, column=1, padx=2, pady=1
                )
                if r.is_hit:
                    parts = [f"{r.dmg1} {r.dmg_type_1}"]
                    if r.dmg2 > 0:
                        parts.append(f"{r.dmg2} {r.dmg_type_2}")
                    dmg_str = " + ".join(parts) + f" = {r.dmg1 + r.dmg2}"
                    force_save, save_dc, save_type = r.save_info
                    if force_save:
                        dmg_str += f"  | DC {save_dc} {save_type} save"
                else:
                    dmg_str = "—"
                tk.Label(outer, text=dmg_str, anchor="w", font=_F8).grid(
                    row=row_idx, column=2, sticky="w", padx=4, pady=1
                )
                row_idx += 1

            # Apply the defender's resistances/immunities/vulnerabilities (monsters only).
            resist, immune, vulnerable = _defender_damage_mods(p_token)
            applied_dmg, dmg_breakdown = resolve_typed_damage(result.rolls, resist, immune, vulnerable)

            hp_str = (f"HP: {p_token.hp}/{p_token.max_hp}" if p_token.max_hp > 0
                      else f"HP: {p_token.hp}")
            total_label = f"  Total damage: {dmg_breakdown}    ({hp_str})"
            tk.Label(outer, text=total_label, font=("Helvetica", 9, "bold"), anchor="w").grid(
                row=row_idx, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 1)
            )
            if applied_dmg > 0:
                var = tk.BooleanVar(value=True)
                tk.Checkbutton(outer, text="Apply", variable=var).grid(
                    row=row_idx, column=2, padx=4, pady=1
                )
                apply_vars.append((var, p_token, applied_dmg))
            row_idx += 1

            ttk.Separator(outer, orient="horizontal").grid(
                row=row_idx, column=0, columnspan=3, sticky="ew", padx=4, pady=2
            )
            row_idx += 1

        def _apply_and_close() -> None:
            for av, pt, dmg in apply_vars:
                if av.get():
                    pt.hp = max(0, pt.hp - dmg)
                    if pt.hp == 0 and GSM.Auto_disable_zero_hp_bool.get():
                        pt.active = False
            dlg.destroy()
            _redraw_all()

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Apply checked & close", command=_apply_and_close,
                  bg="#3355cc", fg="white").pack(side="left", padx=4)
        tk.Button(btn_frame, text="Close", command=dlg.destroy).pack(side="left", padx=4)

    # ── canvas-level bindings ─────────────────────────────────────────────────

    def _on_canvas_click(event: tk.Event) -> None:
        """Click on empty canvas clears multi-selection."""
        token_tags = {"token", "token_label", "hpbar"}
        for item in canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2):
            if set(canvas.gettags(item)) & token_tags:
                return  # hit a token — its own handler manages selection
        _selected["token_ids"].clear()
        _selected["primary_id"] = None
        _update_info(None)
        _update_selection_visuals()
        _redraw_highlights_only()

    def _on_canvas_double_click(event: tk.Event) -> None:
        """Double-click on an empty tile → ask monster or player, place there."""
        token_tags = {"token", "token_label", "hpbar"}
        for item in canvas.find_overlapping(event.x - 3, event.y - 3, event.x + 3, event.y + 3):
            if set(canvas.gettags(item)) & token_tags:
                return  # hit a token — its own double-click handler fires
        col, row = _nearest_cell(event.x, event.y)
        _add_token_at_pos(col, row)

    canvas.bind("<Button-1>", _on_canvas_click)
    canvas.bind("<Double-Button-1>", _on_canvas_double_click)
    canvas.bind("<d>", lambda e: _toggle_active_selected())
    canvas.bind("<D>", lambda e: _toggle_active_selected())
    canvas.bind("<h>", lambda e: _edit_hp_selected())
    canvas.bind("<H>", lambda e: _edit_hp_selected())
    canvas.bind("<r>", lambda e: _retarget_selected())
    canvas.bind("<R>", lambda e: _retarget_selected())
    canvas.bind("<Return>", lambda e: _resolve_board())
    canvas.bind("<Delete>", lambda e: _remove_selected())
    canvas.bind("<BackSpace>", lambda e: _remove_selected())

    # ── board settings sync ───────────────────────────────────────────────────

    def _sync_board_settings(*_) -> None:
        b = _board()
        b.diagonal_mode = GSM.Board_diagonal_mode.get()
        b.flank_geometry = GSM.Board_flank_geometry.get()
        b.flank_benefit = GSM.Board_flank_benefit.get()
        b.range_mode = GSM.Board_range_mode.get()

    GSM.Board_diagonal_mode.trace_add("write", _sync_board_settings)
    GSM.Board_flank_geometry.trace_add("write", _sync_board_settings)
    GSM.Board_flank_benefit.trace_add("write", _sync_board_settings)
    GSM.Board_range_mode.trace_add("write", _sync_board_settings)

    # ── initial draw ──────────────────────────────────────────────────────────
    _sync_board_settings()
    _refresh_team_bar()
    _redraw_all()
