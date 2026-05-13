"""Battle Board tab — Tkinter Canvas grid with drag-and-drop tokens."""

from __future__ import annotations

import colorsys
import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from engine.board import Board, GridPosition, Token, distance_ft, is_flanking, ranged_in_melee
from engine.conditions import Condition
from engine.inference import compute_roll_type_modifiers, flanking_to_hit_bonus, suggest_targets
from GlobalStateManager import GSM

_CELL = 25          # pixels per grid cell
_COLS = 20
_ROWS = 20
_CANVAS_W = _COLS * _CELL
_CANVAS_H = _ROWS * _CELL
_CTRL_W = 160       # left control panel width
_PAD = 5

_COLOR_MONSTER = "#e05555"
_COLOR_PLAYER = "#7aaaf0"
_COLOR_INACTIVE = "#aaaaaa"
_COLOR_RANGE_HL = "#ffffaa"
_COLOR_FLANK_HL = "#aaffaa"
_COLOR_GRID = "#cccccc"
_OVAL_R = 10        # token oval radius in pixels
_BAR_H = 4          # HP bar height in pixels


def BattleBoard(board_frame: tk.Frame) -> None:
    """Build the Battle Board tab UI inside board_frame."""
    board_frame.columnconfigure(0, weight=0)
    board_frame.columnconfigure(1, weight=1)
    board_frame.rowconfigure(0, weight=1)

    # ── left control panel ────────────────────────────────────────────────────
    ctrl = tk.Frame(board_frame, width=_CTRL_W, relief="groove", bd=1)
    ctrl.grid(row=0, column=0, sticky="ns", padx=_PAD, pady=_PAD)
    ctrl.grid_propagate(False)

    tk.Label(ctrl, text="Battle Board", font=GSM.Title_font).pack(anchor="w", padx=4, pady=(6, 2))

    tk.Button(ctrl, text="+ Monster token", command=lambda: _add_token("monster"), width=16).pack(
        anchor="w", padx=4, pady=2
    )
    tk.Button(ctrl, text="+ Player token", command=lambda: _add_token("player"), width=16).pack(
        anchor="w", padx=4, pady=2
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
    ).pack(anchor="w", padx=4, pady=2)

    ttk.Separator(ctrl, orient="horizontal").pack(fill="x", padx=4, pady=4)

    tk.Button(ctrl, text="Resolve Board", command=lambda: _resolve_board(),
              bg="#3355cc", fg="white", width=14).pack(anchor="w", padx=4, pady=2)

    tk.Button(ctrl, text="Clear board", command=lambda: _clear_board(),
              fg="white", bg="#aa3333", width=14).pack(anchor="w", padx=4, pady=2)

    # ── canvas ────────────────────────────────────────────────────────────────
    canvas_frame = tk.Frame(board_frame)
    canvas_frame.grid(row=0, column=1, sticky="nsew", padx=_PAD, pady=_PAD)

    canvas = tk.Canvas(canvas_frame, width=_CANVAS_W, height=_CANVAS_H, bg="white", cursor="crosshair")
    canvas.pack()

    # ── state ─────────────────────────────────────────────────────────────────
    # token_id → (oval_id, label_id, [hpbar_item_ids…])
    _token_canvas: dict[str, tuple[int, int, list[int]]] = {}
    _drag: dict = {"token_id": None, "offset_x": 0, "offset_y": 0}
    _selected: dict = {"token_id": None}
    _token_counter: list[int] = [0]

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

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw_grid() -> None:
        canvas.delete("grid")
        for c in range(_COLS + 1):
            canvas.create_line(c * _CELL, 0, c * _CELL, _CANVAS_H, fill=_COLOR_GRID, tags="grid")
        for r in range(_ROWS + 1):
            canvas.create_line(0, r * _CELL, _CANVAS_W, r * _CELL, fill=_COLOR_GRID, tags="grid")

    def _draw_range_highlight_if_selected() -> None:
        canvas.delete("range_hl")
        tid = _selected["token_id"]
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
        tid = _selected["token_id"]
        if not tid:
            return
        token = _token_by_id(tid)
        if not token:
            return
        board = _board()
        for target in board.tokens:
            if target.kind == token.kind:
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
            oid = canvas.create_oval(
                cx - _OVAL_R, cy - _OVAL_R, cx + _OVAL_R, cy + _OVAL_R,
                fill=color, outline="black", width=1, tags="token"
            )
            lid = canvas.create_text(
                cx, cy, text=token.data_ref[:6], font=("Helvetica", 6), fill="black", tags="token_label"
            )
            bar_ids = _draw_hp_bar(token, cx, cy)
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

    def _raise_tokens() -> None:
        canvas.tag_raise("token")
        canvas.tag_raise("token_label")

    def _redraw_all() -> None:
        _draw_grid()
        _draw_range_highlight_if_selected()
        _draw_flank_highlight_if_selected()
        _draw_tokens()
        _raise_tokens()

    def _redraw_highlights_only() -> None:
        """Redraw grid + highlights WITHOUT destroying token items (preserves drag bindings)."""
        _draw_grid()
        _draw_range_highlight_if_selected()
        _draw_flank_highlight_if_selected()
        _raise_tokens()

    # ── token interaction ─────────────────────────────────────────────────────

    def _on_token_click(event: tk.Event, tid: str) -> None:
        _selected["token_id"] = tid
        _drag["token_id"] = tid
        _drag["offset_x"] = event.x
        _drag["offset_y"] = event.y
        _update_info(_token_by_id(tid))
        canvas.focus_set()  # allow hotkeys (e.g. D) to fire on canvas
        # Only redraw highlights — do NOT call _redraw_all (would destroy drag bindings)
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
        """Toggle active/inactive on the currently selected token (hotkey D)."""
        tid = _selected["token_id"]
        if tid is None:
            return
        token = _token_by_id(tid)
        if token:
            _toggle_active(token)

    def _remove_selected() -> None:
        """Remove the currently selected token (hotkey Delete/BackSpace)."""
        tid = _selected["token_id"]
        if tid:
            _remove_token(tid)

    def _on_token_drag(event: tk.Event, tid: str) -> None:
        if _drag["token_id"] != tid:
            return
        ids = _token_canvas.get(tid)
        if ids is None:
            return
        oid, lid, bar_ids = ids
        dx = event.x - _drag["offset_x"]
        dy = event.y - _drag["offset_y"]
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
        col, row = _nearest_cell(event.x, event.y)
        token = _token_by_id(tid)
        if token:
            token.pos = GridPosition(col, row)
            _update_info(token)  # refresh info panel after move
        _redraw_all()

    def _on_token_right_click(event: tk.Event, tid: str) -> None:
        token = _token_by_id(tid)
        if token is None:
            return
        menu = tk.Menu(canvas, tearoff=0)
        menu.add_command(label=f"{token.data_ref} ({token.kind})", state="disabled")
        menu.add_separator()
        menu.add_command(label="Set HP…", command=lambda: _set_hp(token))
        menu.add_separator()

        cond_menu = tk.Menu(menu, tearoff=0)
        for cond in Condition:
            label = f"✓ {cond.value}" if cond in token.conditions else f"  {cond.value}"
            cond_menu.add_command(label=label,
                                  command=lambda c=cond, t=token: _toggle_condition(t, c))
        menu.add_cascade(label="Conditions", menu=cond_menu)
        menu.add_separator()

        menu.add_command(
            label="Deactivate" if token.active else "Activate",
            command=lambda: _toggle_active(token)
        )
        menu.add_separator()
        menu.add_command(label="Remove token", command=lambda: _remove_token(tid))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _set_hp(token: Token) -> None:
        val = simpledialog.askinteger(
            "Set HP", f"HP for {token.data_ref} (max {token.max_hp}):",
            initialvalue=token.hp, parent=canvas
        )
        if val is not None:
            token.hp = val
            if val == 0 and GSM.Auto_disable_zero_hp_bool.get():
                token.active = False
            _update_info(token)
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

    def _toggle_active(token: Token) -> None:
        token.active = not token.active
        _update_info(token)
        _redraw_all()

    def _remove_token(tid: str) -> None:
        _board().tokens = [t for t in _board().tokens if t.id != tid]
        if _selected["token_id"] == tid:
            _selected["token_id"] = None
            _update_info(None)
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
        enemies = [t for t in board.tokens if t.kind != token.kind and t.active]
        if enemies:
            nearest = min(enemies, key=lambda t: distance_ft(token.pos, t.pos, board.diagonal_mode))
            roll_mod = compute_roll_type_modifiers(token, nearest, board, GSM.Adv_mode.get())
            in_melee_str = "yes" if ranged_in_melee(token, board) else "no"
        else:
            roll_mod = "Normal"
            in_melee_str = "no"
        info_var.set("\n".join([
            token.data_ref,
            f"HP: {hp_str}  [{status}]",
            f"Pos: ({token.pos.col},{token.pos.row})",
            f"Conds: {conds}",
            f"Range: {range_str}",
            f"Roll mod: {roll_mod}",
            f"In melee: {in_melee_str}",
            f"HL range: {token.highlight_range_ft}ft",
        ]))

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
        _redraw_all()

    def _add_token_at_pos(col: int, row: int) -> None:
        """Single combined list: players (alpha) then monsters (alpha). One click to place."""
        # Build sorted entries: players first, then monsters
        entries: list[tuple[str, str, object]] = []  # (display, kind, obj)
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
        listbox.selection_set(0)
        listbox.pack(padx=8, pady=4)
        listbox.focus_set()

        def _confirm() -> None:
            sel = listbox.curselection()
            if not sel:
                top.destroy()
                return
            _, kind, obj = entries[sel[0]]
            top.destroy()
            _place_token_from_obj(kind, obj, GridPosition(col, row))

        listbox.bind("<Return>", lambda e: _confirm())
        listbox.bind("<Double-Button-1>", lambda e: _confirm())
        tk.Button(top, text="Add", command=_confirm).pack(pady=(0, 6))
        _popup_at_mouse(top)
        top.grab_set()

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
        _selected["token_id"] = None
        _update_info(None)
        _redraw_all()

    # ── Resolve Board ─────────────────────────────────────────────────────────

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
            p_tokens = [t for t in board.tokens if t.kind == "player" and t.active]
            if not p_tokens:
                continue
            p_tokens.sort(key=lambda t: distance_ft(m_token.pos, t.pos, board.diagonal_mode))

            atk_range = m_token.attack_range_ft
            range_mode = board.range_mode

            if range_mode == "block":
                in_range = [
                    t for t in p_tokens
                    if distance_ft(m_token.pos, t.pos, board.diagonal_mode) <= atk_range
                ]
                if not in_range:
                    skipped_blocked.append(m_token.data_ref)
                    continue
                p_token = in_range[0]
                out_of_range = False
            else:
                p_token = p_tokens[0]
                dist = distance_ft(m_token.pos, p_token.pos, board.diagonal_mode)
                out_of_range = (range_mode == "warn") and (dist > atk_range)

            player_obj = next(
                (p for p in GSM.Target_obj_list if p.name_str.get() == p_token.data_ref), None
            )
            if player_obj is None:
                continue
            pairs.append((m_token, p_token, monster_obj, player_obj, out_of_range))


        if skipped_blocked:
            names = ", ".join(skipped_blocked)
            messagebox.showinfo("Resolve Board", f"Blocked by range — no valid targets for: {names}")

        if not pairs:
            if not skipped_blocked:
                messagebox.showinfo("Resolve Board", "No active monster→player pairs found on board.")
            return

        # Sort: player name first, then monster name — groups same-target attacks together
        pairs.sort(key=lambda p: (p[1].data_ref, p[0].data_ref))

        results = []
        for m_token, p_token, monster_obj, player_obj, out_of_range in pairs:
            monster_data = monster_obj.to_data()
            player_data = player_obj.to_data()
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
            # ── header row ────────────────────────────────────────────────────
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

            # ── per-roll rows ─────────────────────────────────────────────────
            for r in result.rolls:
                roll_type_tag = f" [{r.roll_type}]" if r.roll_type != "Normal" else ""
                crit_tag = " (CRIT)" if r.is_crit else ""
                outcome = "CRIT" if r.is_crit else ("MISS" if not r.is_hit else "HIT")

                # dice display: kept die normal, dropped dice in grey
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

            # ── total + apply ─────────────────────────────────────────────────
            hp_str = (f"HP: {p_token.hp}/{p_token.max_hp}" if p_token.max_hp > 0
                      else f"HP: {p_token.hp}")
            total_label = f"  Total damage: {total_dmg}    ({hp_str})"
            tk.Label(outer, text=total_label, font=("Helvetica", 9, "bold"), anchor="w").grid(
                row=row_idx, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 1)
            )
            if total_dmg > 0:
                var = tk.BooleanVar(value=True)
                tk.Checkbutton(outer, text="Apply", variable=var).grid(
                    row=row_idx, column=2, padx=4, pady=1
                )
                apply_vars.append((var, p_token, total_dmg))
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

    def _on_canvas_double_click(event: tk.Event) -> None:
        """Double-click on an empty tile → ask monster or player, place there."""
        token_tags = {"token", "token_label", "hpbar"}
        for item in canvas.find_overlapping(event.x - 3, event.y - 3, event.x + 3, event.y + 3):
            if set(canvas.gettags(item)) & token_tags:
                return  # hit a token — its own double-click handler fires
        col, row = _nearest_cell(event.x, event.y)
        _add_token_at_pos(col, row)

    canvas.bind("<Double-Button-1>", _on_canvas_double_click)
    canvas.bind("<d>", lambda e: _toggle_active_selected())
    canvas.bind("<D>", lambda e: _toggle_active_selected())
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
    _redraw_all()
