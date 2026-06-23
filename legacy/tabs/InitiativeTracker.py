"""Initiative Tracker tab — turn-order list for D&D 5e combat."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from engine.initiative import InitiativeEntry, roll_initiative, sort_entries
from GlobalStateManager import GSM

_entries: list[InitiativeEntry] = []
_current_idx: int = 0   # index of the active combatant


def InitiativeTracker(tracker_frame: ttk.Frame) -> None:
    """Build the Initiative Tracker tab inside tracker_frame."""

    # ── header ────────────────────────────────────────────────────────────────
    tk.Label(tracker_frame, text="Initiative Tracker", font=GSM.Title_font).place(x=10, y=8)

    # ── treeview list ─────────────────────────────────────────────────────────
    columns = ("init", "name", "type", "active")
    tree = ttk.Treeview(tracker_frame, columns=columns, show="headings", height=16, selectmode="browse")
    tree.heading("init", text="Init")
    tree.heading("name", text="Name")
    tree.heading("type", text="Type")
    tree.heading("active", text="Status")
    tree.column("init", width=40, anchor="center")
    tree.column("name", width=130)
    tree.column("type", width=70, anchor="center")
    tree.column("active", width=60, anchor="center")
    tree.place(x=10, y=38, width=330, height=320)

    scrollbar = ttk.Scrollbar(tracker_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.place(x=340, y=38, height=320)

    # Highlight active combatant with a tag
    tree.tag_configure("active_turn", background="#cce8ff")
    tree.tag_configure("inactive_entry", foreground="#999999")

    # ── add entry panel ───────────────────────────────────────────────────────
    add_frame = tk.LabelFrame(tracker_frame, text="Add entry", width=200, height=120)
    add_frame.place(x=360, y=38)
    add_frame.grid_propagate(False)

    tk.Label(add_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
    name_var = tk.StringVar(value="")
    tk.Entry(add_frame, textvariable=name_var, width=14).grid(row=0, column=1, padx=4, pady=2)

    tk.Label(add_frame, text="Initiative:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
    init_var = tk.IntVar(value=10)
    tk.Spinbox(add_frame, from_=-10, to=40, textvariable=init_var, width=5).grid(row=1, column=1, padx=4, pady=2)

    type_var = tk.StringVar(value="monster")
    tk.Radiobutton(add_frame, text="Monster", variable=type_var, value="monster").grid(
        row=2, column=0, sticky="w", padx=4
    )
    tk.Radiobutton(add_frame, text="Player", variable=type_var, value="player").grid(
        row=2, column=1, sticky="w", padx=4
    )

    def _add_entry() -> None:
        name = name_var.get().strip()
        if not name:
            return
        entry = InitiativeEntry(
            name=name,
            initiative=init_var.get(),
            is_player=type_var.get() == "player",
        )
        _entries.append(entry)
        _refresh_tree()

    tk.Button(add_frame, text="Add", command=_add_entry, width=8).grid(
        row=3, column=0, columnspan=2, pady=4
    )

    # ── roll for all panel ────────────────────────────────────────────────────
    roll_frame = tk.LabelFrame(tracker_frame, text="Roll initiative", width=200, height=90)
    roll_frame.place(x=360, y=165)
    roll_frame.grid_propagate(False)

    tk.Label(roll_frame, text="Mod:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
    roll_mod_var = tk.IntVar(value=0)
    tk.Spinbox(roll_frame, from_=-10, to=20, textvariable=roll_mod_var, width=5).grid(row=0, column=1, padx=4, pady=2)

    def _roll_for_all() -> None:
        for entry in _entries:
            if entry.is_active:
                entry.initiative = roll_initiative(roll_mod_var.get())
        _sort_and_refresh()

    tk.Button(roll_frame, text="Roll for all active", command=_roll_for_all, width=16).grid(
        row=1, column=0, columnspan=2, pady=4
    )

    # ── monster quick-add panel ───────────────────────────────────────────────
    quick_frame = tk.LabelFrame(tracker_frame, text="Quick-add from roster", width=200, height=110)
    quick_frame.place(x=360, y=265)
    quick_frame.grid_propagate(False)

    def _add_all_monsters() -> None:
        for m_obj in GSM.Monster_obj_list:
            name = m_obj.name_str.get()
            init_val = roll_initiative(m_obj.initiative_mod_int.get())
            _entries.append(InitiativeEntry(name=name, initiative=init_val, is_player=False))
        _sort_and_refresh()

    def _add_all_players() -> None:
        for p_obj in GSM.Target_obj_list:
            name = p_obj.name_str.get()
            init_val = roll_initiative(p_obj.initiative_mod_int.get())
            _entries.append(InitiativeEntry(name=name, initiative=init_val, is_player=True))
        _sort_and_refresh()

    tk.Button(quick_frame, text="Add all monsters", command=_add_all_monsters, width=16).grid(
        row=0, column=0, columnspan=2, padx=4, pady=6
    )
    tk.Button(quick_frame, text="Add all players", command=_add_all_players, width=16).grid(
        row=1, column=0, columnspan=2, padx=4, pady=2
    )

    # ── navigation buttons ────────────────────────────────────────────────────
    nav_frame = tk.Frame(tracker_frame)
    nav_frame.place(x=10, y=368)

    def _prev_turn() -> None:
        global _current_idx
        active = [i for i, e in enumerate(_entries) if e.is_active]
        if not active:
            return
        pos = active.index(_current_idx) if _current_idx in active else 0
        _current_idx = active[(pos - 1) % len(active)]
        _refresh_tree()

    def _next_turn() -> None:
        global _current_idx
        active = [i for i, e in enumerate(_entries) if e.is_active]
        if not active:
            return
        pos = active.index(_current_idx) if _current_idx in active else -1
        _current_idx = active[(pos + 1) % len(active)]
        _refresh_tree()

    tk.Button(nav_frame, text="◀ Prev", command=_prev_turn, width=8).grid(row=0, column=0, padx=2)
    tk.Button(nav_frame, text="Next ▶", command=_next_turn, width=8).grid(row=0, column=1, padx=2)

    # ── action buttons ────────────────────────────────────────────────────────
    action_frame = tk.Frame(tracker_frame)
    action_frame.place(x=200, y=368)

    def _remove_selected() -> None:
        global _current_idx
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        _entries.pop(idx)
        if _current_idx >= len(_entries):
            _current_idx = max(0, len(_entries) - 1)
        _refresh_tree()

    def _toggle_selected_active() -> None:
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        _entries[idx].is_active = not _entries[idx].is_active
        _refresh_tree()

    def _sort_and_refresh() -> None:
        _entries[:] = sort_entries(_entries)
        _refresh_tree()

    def _clear_all() -> None:
        global _current_idx
        _entries.clear()
        _current_idx = 0
        _refresh_tree()

    tk.Button(action_frame, text="Sort", command=_sort_and_refresh, width=6).grid(row=0, column=0, padx=2)
    tk.Button(action_frame, text="Toggle", command=_toggle_selected_active, width=6).grid(row=0, column=1, padx=2)
    tk.Button(action_frame, text="Remove", command=_remove_selected, width=6).grid(row=0, column=2, padx=2)
    tk.Button(action_frame, text="Clear", command=_clear_all, fg="white", bg="#aa3333", width=6).grid(
        row=0, column=3, padx=2
    )

    # ── inline edit: double-click initiative ──────────────────────────────────

    def _on_double_click(event: tk.Event) -> None:
        region = tree.identify("region", event.x, event.y)
        col = tree.identify_column(event.x)
        if region != "cell" or col != "#1":  # only "init" column
            return
        sel = tree.selection()
        if not sel:
            return
        row_id = sel[0]
        idx = tree.index(row_id)
        entry = _entries[idx]
        bbox = tree.bbox(row_id, col)
        if not bbox:
            return
        x, y, w, h = bbox
        edit_var = tk.StringVar(value=str(entry.initiative))
        edit_entry = tk.Entry(tree, textvariable=edit_var, width=4, justify="center")
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.focus_set()

        def _commit(*_) -> None:
            try:
                entry.initiative = int(edit_var.get())
            except ValueError:
                pass
            edit_entry.destroy()
            _refresh_tree()

        edit_entry.bind("<Return>", _commit)
        edit_entry.bind("<FocusOut>", _commit)

    tree.bind("<Double-1>", _on_double_click)

    # ── refresh ───────────────────────────────────────────────────────────────

    def _refresh_tree() -> None:
        tree.delete(*tree.get_children())
        for i, entry in enumerate(_entries):
            kind = "Player" if entry.is_player else "Monster"
            status = "active" if entry.is_active else "inactive"
            tags = []
            if i == _current_idx and entry.is_active:
                tags.append("active_turn")
            if not entry.is_active:
                tags.append("inactive_entry")
            tree.insert("", "end", values=(entry.initiative, entry.name, kind, status), tags=tags)
