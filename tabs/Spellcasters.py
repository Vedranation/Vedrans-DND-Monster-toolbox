import tkinter as tk
from tkinter import messagebox

from utilities import RelativePositionTracker
from GlobalStateManager import GSM

_COL_W = 165  # pixels per caster column

_SCHOOLS = [
    "", "Abjuration", "Conjuration", "Divination", "Enchantment",
    "Evocation", "Illusion", "Necromancy", "Transmutation", "Other",
]


# ── shared helpers ────────────────────────────────────────────────────────────

def _popup_near_mouse(window: tk.Toplevel) -> None:
    window.update_idletasks()
    w = window.winfo_reqwidth()
    h = window.winfo_reqheight()
    x = window.winfo_pointerx() - w // 2
    y = window.winfo_pointery() - h // 2
    window.geometry(f"+{x}+{y}")


def _sorted_library() -> list[dict]:
    return sorted(GSM.Spell_library, key=lambda s: (s.get("level", 0), s.get("name", "").lower()))


def _spell_label(spell: dict) -> str:
    lv = spell.get("level", 0)
    return f"Lv{'C' if lv == 0 else lv}  {spell.get('name', '')}"


# ── global spell library window ───────────────────────────────────────────────

def _open_global_spell_library(preselect_name: str | None = None) -> None:
    top = tk.Toplevel()
    top.title("Global Spell Library")
    top.resizable(True, True)
    top.geometry("780x620")

    _LEVEL_FILTERS = ["All", "0 (Cantrip)"] + [str(i) for i in range(1, 10)]
    _filter_var = tk.StringVar(value="All")
    _sel_lib_idx: list[int] = [-1]

    # ── left panel ────────────────────────────────────────────────────────
    left = tk.Frame(top, width=215, relief="groove", bd=1)
    left.pack(side="left", fill="y", padx=(8, 4), pady=8)
    left.pack_propagate(False)

    tk.Label(left, text="Filter by level:").pack(anchor="w", padx=4, pady=(6, 0))
    tk.OptionMenu(left, _filter_var, *_LEVEL_FILTERS, command=lambda _: _refresh()).pack(
        anchor="w", padx=4
    )
    tk.Label(left, text="Spells:", font=("Helvetica", 8, "bold")).pack(anchor="w", padx=4, pady=(8, 0))

    lb_frame = tk.Frame(left)
    lb_frame.pack(fill="both", expand=True, padx=4, pady=(0, 8))
    lb_scroll = tk.Scrollbar(lb_frame, orient="vertical")
    lb = tk.Listbox(lb_frame, yscrollcommand=lb_scroll.set, activestyle="dotbox", width=24)
    lb_scroll.config(command=lb.yview)
    lb_scroll.pack(side="right", fill="y")
    lb.pack(side="left", fill="both", expand=True)

    # ── right panel ───────────────────────────────────────────────────────
    right = tk.Frame(top)
    right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)
    right.columnconfigure(1, weight=1)
    right.rowconfigure(9, weight=1)  # description row expands

    def _row_label(row: int, text: str, anchor: str = "w") -> None:
        tk.Label(right, text=text).grid(row=row, column=0, sticky=anchor, pady=3, padx=(0, 6))

    # Row 0 — Name
    _row_label(0, "Name *")
    name_var = tk.StringVar()
    tk.Entry(right, textvariable=name_var, width=36).grid(
        row=0, column=1, columnspan=2, sticky="ew", pady=3)

    # Row 1 — Level
    _row_label(1, "Level *")
    level_var = tk.IntVar(value=1)
    tk.OptionMenu(right, level_var, *range(0, 10)).grid(row=1, column=1, sticky="w", pady=3)

    # Row 2 — School
    _row_label(2, "School")
    school_var = tk.StringVar(value="")
    tk.OptionMenu(right, school_var, *_SCHOOLS).grid(row=2, column=1, sticky="w", pady=3)

    # Row 3 — Casting time
    _row_label(3, "Casting time")
    casting_var = tk.StringVar()
    tk.Entry(right, textvariable=casting_var, width=22).grid(
        row=3, column=1, columnspan=2, sticky="w", pady=3)

    # Row 4 — Range
    _row_label(4, "Range")
    range_var = tk.StringVar()
    tk.Entry(right, textvariable=range_var, width=22).grid(
        row=4, column=1, columnspan=2, sticky="w", pady=3)

    # Row 5 — Duration + Concentration
    _row_label(5, "Duration")
    duration_var = tk.StringVar()
    concentration_var = tk.BooleanVar()
    tk.Entry(right, textvariable=duration_var, width=22).grid(row=5, column=1, sticky="w", pady=3)
    tk.Checkbutton(right, text="Concentration", variable=concentration_var).grid(
        row=5, column=2, sticky="w", pady=3)

    # Row 6 — Components V S M
    _row_label(6, "Components")
    comp_v, comp_s, comp_m = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
    comp_row = tk.Frame(right)
    comp_row.grid(row=6, column=1, columnspan=2, sticky="w")
    tk.Checkbutton(comp_row, text="V", variable=comp_v).pack(side="left")
    tk.Checkbutton(comp_row, text="S", variable=comp_s).pack(side="left")
    tk.Checkbutton(comp_row, text="M", variable=comp_m,
                   command=lambda: _toggle_m_cost()).pack(side="left")

    # Row 7 — M material cost (gated on M being checked)
    _row_label(7, "M cost")
    material_cost_var = tk.StringVar()
    material_consumed_var = tk.BooleanVar()
    cost_entry = tk.Entry(right, textvariable=material_cost_var, width=18, state="disabled")
    cost_entry.grid(row=7, column=1, sticky="w", pady=3)
    gp_label = tk.Label(right, text="gp")
    gp_label.grid(row=7, column=1, sticky="e", padx=(0, 60), pady=3)
    consumed_cb = tk.Checkbutton(right, text="Consumed", variable=material_consumed_var,
                                  state="disabled")
    consumed_cb.grid(row=7, column=2, sticky="w", pady=3)

    def _toggle_m_cost() -> None:
        if comp_m.get():
            cost_entry.config(state="normal")
            consumed_cb.config(state="normal")
        else:
            cost_entry.config(state="disabled")
            consumed_cb.config(state="disabled")
            material_cost_var.set("")
            material_consumed_var.set(False)

    # Row 8 — Description label (top-aligned)
    _row_label(8, "Description", anchor="nw")

    # Row 9 — Description text box (expandable)
    desc_frame = tk.Frame(right)
    desc_frame.grid(row=8, column=1, columnspan=2, rowspan=2, sticky="nsew", pady=3)
    right.rowconfigure(8, weight=0)
    right.rowconfigure(9, weight=1)
    desc_scroll = tk.Scrollbar(desc_frame)
    desc_text = tk.Text(desc_frame, width=38, height=11, wrap="word",
                        yscrollcommand=desc_scroll.set, font=("Arial", 10))
    desc_scroll.config(command=desc_text.yview)
    desc_scroll.pack(side="right", fill="y")
    desc_text.pack(side="left", fill="both", expand=True)

    # Row 10 — Button row
    btn_row = tk.Frame(right)
    btn_row.grid(row=10, column=0, columnspan=3, pady=(8, 0))

    # ── form helpers ──────────────────────────────────────────────────────
    def _clear_form() -> None:
        name_var.set("")
        level_var.set(1)
        school_var.set("")
        casting_var.set("")
        range_var.set("")
        duration_var.set("")
        concentration_var.set(False)
        comp_v.set(False); comp_s.set(False); comp_m.set(False)
        material_cost_var.set(""); material_consumed_var.set(False)
        _toggle_m_cost()
        desc_text.delete("1.0", "end")
        _sel_lib_idx[0] = -1
        lb.selection_clear(0, "end")

    def _load_to_form(spell: dict) -> None:
        name_var.set(spell.get("name", ""))
        level_var.set(spell.get("level", 1))
        school_var.set(spell.get("school", ""))
        casting_var.set(spell.get("casting_time", ""))
        range_var.set(spell.get("range", ""))
        duration_var.set(spell.get("duration", ""))
        concentration_var.set(spell.get("concentration", False))
        comp_v.set(spell.get("component_v", False))
        comp_s.set(spell.get("component_s", False))
        comp_m.set(spell.get("component_m", False))
        _toggle_m_cost()  # enable/disable cost fields based on M value
        material_cost_var.set(spell.get("material_cost", ""))
        material_consumed_var.set(spell.get("material_consumed", False))
        desc_text.delete("1.0", "end")
        desc_text.insert("1.0", spell.get("description", ""))

    def _form_to_dict() -> dict | None:
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing field", "Spell name is required.", parent=top)
            return None
        return {
            "name": name,
            "level": level_var.get(),
            "school": school_var.get(),
            "casting_time": casting_var.get().strip(),
            "range": range_var.get().strip(),
            "duration": duration_var.get().strip(),
            "concentration": concentration_var.get(),
            "component_v": comp_v.get(),
            "component_s": comp_s.get(),
            "component_m": comp_m.get(),
            "material_cost": material_cost_var.get().strip() if comp_m.get() else "",
            "material_consumed": material_consumed_var.get() if comp_m.get() else False,
            "description": desc_text.get("1.0", "end-1c").strip(),
        }

    # ── listbox helpers ───────────────────────────────────────────────────
    def _filtered_spells() -> list[dict]:
        fl = _filter_var.get()
        spells = _sorted_library()
        if fl == "All":
            return spells
        lv = int(fl.split()[0])
        return [s for s in spells if s.get("level", 0) == lv]

    def _refresh(select_name: str | None = None) -> None:
        filtered = _filtered_spells()
        lb.delete(0, "end")
        for sp in filtered:
            lb.insert("end", _spell_label(sp))
        if select_name:
            for i, sp in enumerate(filtered):
                if sp.get("name") == select_name:
                    lb.selection_set(i)
                    lb.see(i)
                    break

    def _on_select(_event=None) -> None:
        sel = lb.curselection()
        if not sel:
            return
        filtered = _filtered_spells()
        spell = filtered[sel[0]]
        _sel_lib_idx[0] = next(
            (i for i, s in enumerate(GSM.Spell_library) if s is spell), -1
        )
        _load_to_form(spell)

    def _save_spell() -> None:
        spell = _form_to_dict()
        if spell is None:
            return
        if _sel_lib_idx[0] >= 0:
            GSM.Spell_library[_sel_lib_idx[0]] = spell
        else:
            GSM.Spell_library.append(spell)
        _refresh(select_name=spell["name"])

    def _delete_spell() -> None:
        if _sel_lib_idx[0] < 0:
            messagebox.showwarning("Nothing selected", "Select a spell to delete first.", parent=top)
            return
        name = GSM.Spell_library[_sel_lib_idx[0]].get("name", "")
        if not messagebox.askyesno("Delete spell", f"Delete '{name}'?", parent=top):
            return
        GSM.Spell_library.pop(_sel_lib_idx[0])
        _clear_form()
        _refresh()

    lb.bind("<<ListboxSelect>>", _on_select)
    lb.bind("<Double-Button-1>", _on_select)

    tk.Button(btn_row, text="New", command=_clear_form, width=10).pack(side="left", padx=4)
    tk.Button(btn_row, text="Save / Update", command=_save_spell, width=14,
              bg="#336633", fg="white").pack(side="left", padx=4)
    tk.Button(btn_row, text="Delete", command=_delete_spell, width=10,
              bg="#aa3333", fg="white").pack(side="left", padx=4)
    tk.Button(btn_row, text="Close", command=top.destroy, width=10).pack(side="left", padx=4)

    _refresh(select_name=preselect_name)
    if preselect_name:
        # Also load the spell into the form
        for sp in GSM.Spell_library:
            if sp.get("name") == preselect_name:
                _sel_lib_idx[0] = GSM.Spell_library.index(sp)
                _load_to_form(sp)
                break
    _popup_near_mouse(top)


# ── per-caster spell list window ──────────────────────────────────────────────

def _add_from_library_dialog(spell_data: dict, listboxes: dict, parent: tk.Toplevel) -> None:
    """Modal picker: select a library spell and add it to the matching level bucket."""
    if not GSM.Spell_library:
        messagebox.showinfo("Empty library", "No spells in the global library yet.", parent=parent)
        return

    dialog = tk.Toplevel(parent)
    dialog.title("Add from Library")
    dialog.resizable(False, False)

    tk.Label(dialog, text="Select a spell to add:").pack(padx=8, pady=(8, 4))

    lb_frame = tk.Frame(dialog)
    lb_frame.pack(fill="both", expand=True, padx=8)
    scroll = tk.Scrollbar(lb_frame, orient="vertical")
    pick_lb = tk.Listbox(lb_frame, yscrollcommand=scroll.set, height=18, width=34)
    scroll.config(command=pick_lb.yview)
    scroll.pack(side="right", fill="y")
    pick_lb.pack(side="left", fill="both", expand=True)

    sorted_spells = _sorted_library()
    for sp in sorted_spells:
        pick_lb.insert("end", _spell_label(sp))

    def _confirm() -> None:
        sel = pick_lb.curselection()
        if not sel:
            return
        spell = sorted_spells[sel[0]]
        lv = spell.get("level", 1)
        name = spell.get("name", "")
        spell_data.setdefault(lv, []).append(name)
        if lv in listboxes:
            listboxes[lv].insert("end", name)
        dialog.destroy()
        parent.grab_set()

    pick_lb.bind("<Double-Button-1>", lambda _e: _confirm())

    btn_row = tk.Frame(dialog)
    btn_row.pack(pady=8)
    tk.Button(btn_row, text="Add", command=_confirm, width=10,
              bg="#336633", fg="white").pack(side="left", padx=4)
    tk.Button(btn_row, text="Cancel",
              command=lambda: (dialog.destroy(), parent.grab_set()),
              width=10).pack(side="left", padx=4)

    _popup_near_mouse(dialog)
    dialog.grab_set()


def _open_spell_list(caster_index: int) -> None:
    name_entry = GSM.Spell_caster_name_entries.get(caster_index)
    caster_name = name_entry.get().strip() if name_entry else ""
    caster_name = caster_name or f"Caster {caster_index + 1}"

    top = tk.Toplevel()
    top.title(f"Spells — {caster_name}")
    top.resizable(False, False)

    spell_data = GSM.Spell_caster_spells.setdefault(caster_index, {})
    listboxes: dict[int, tk.Listbox] = {}

    header = tk.Frame(top)
    header.pack(fill="x", padx=8, pady=(8, 0))
    tk.Button(
        header, text="Add from Library",
        command=lambda: _add_from_library_dialog(spell_data, listboxes, top),
        bg="#335588", fg="white",
    ).pack(side="left")

    outer = tk.Frame(top)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, width=380)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_configure(_e):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner.bind("<Configure>", _on_configure)

    def _open_in_library(spell_name: str) -> None:
        """Open global library with the named spell pre-selected."""
        if any(s.get("name") == spell_name for s in GSM.Spell_library):
            _open_global_spell_library(preselect_name=spell_name)

    for lvl in range(1, 10):
        spells = spell_data.setdefault(lvl, [])

        frame = tk.LabelFrame(inner, text=f"Spell Level {lvl}", padx=6, pady=4)
        frame.pack(fill="x", padx=8, pady=4)

        lb = tk.Listbox(frame, height=4, width=28, selectmode="single")
        lb.pack(side="left", fill="y")
        listboxes[lvl] = lb
        for sp in spells:
            lb.insert("end", sp)

        # Double-click: open spell in global library if it exists there
        lb.bind("<Double-Button-1>", lambda e, lb_ref=lb: _open_in_library(
            lb_ref.get(lb_ref.nearest(e.y)) if lb_ref.size() else ""
        ))

        right = tk.Frame(frame)
        right.pack(side="left", padx=6, fill="y")

        entry_var = tk.StringVar()
        entry = tk.Entry(right, textvariable=entry_var, width=22)
        entry.pack(pady=(0, 4))

        def _add(lv=lvl, ev=entry_var, lb_ref=lb):
            name = ev.get().strip()
            if not name:
                return
            lb_ref.insert("end", name)
            spell_data.setdefault(lv, []).append(name)
            ev.set("")

        def _remove(lv=lvl, lb_ref=lb):
            sel = lb_ref.curselection()
            if not sel:
                return
            idx = sel[0]
            lb_ref.delete(idx)
            if lv in spell_data and idx < len(spell_data[lv]):
                spell_data[lv].pop(idx)

        entry.bind("<Return>", lambda e, lv=lvl, ev=entry_var, lb_ref=lb: _add(lv, ev, lb_ref))
        tk.Button(right, text="Add", command=_add, width=10).pack()
        tk.Button(right, text="Remove", command=_remove, width=10).pack(pady=(4, 0))

    tk.Button(top, text="Close", command=top.destroy, width=10).pack(pady=6)

    top.update_idletasks()
    canvas.configure(height=min(inner.winfo_reqheight() + 20, 530))
    _popup_near_mouse(top)
    top.grab_set()


# ── spell slot checkbox grid ──────────────────────────────────────────────────

def DrawSpellBoxes(caster_lv: int, index: int) -> None:
    """Redraw spell slot checkboxes for caster column `index`."""
    for widget in GSM.Spell_checkboxes_dict.get(index, []):
        widget.destroy()
    GSM.Spell_checkboxes_dict[index] = []

    pos = RelativePositionTracker()
    col = index * _COL_W

    def _lbl(text: str, x: int, y: int) -> None:
        w = tk.Label(GSM.Spell_caster_frame, text=text)
        w.place(x=x + col, y=y)
        GSM.Spell_checkboxes_dict[index].append(w)

    def _chk(x: int, y: int) -> None:
        w = tk.Checkbutton(GSM.Spell_caster_frame)
        w.place(x=x + col, y=y)
        GSM.Spell_checkboxes_dict[index].append(w)

    if caster_lv >= 1:
        _lbl("Level 1:", pos.reset("x"), pos.set("y", 165))
        _chk(pos.set("x", 47), pos.same("y"))
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 2:
        _chk(pos.increase("x", 20), pos.same("y"))
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 3:
        _lbl("Level 2:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 4:
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 5:
        _lbl("Level 3:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 6:
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 7:
        _lbl("Level 4:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
    if caster_lv >= 8:
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 9:
        _chk(pos.increase("x", 20), pos.same("y"))
        _lbl("Level 5:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
    if caster_lv >= 10:
        _chk(pos.increase("x", 20), pos.same("y"))
    if caster_lv >= 11:
        _lbl("Level 6:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
    if caster_lv >= 13:
        _lbl("Level 7:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
    if caster_lv >= 15:
        _lbl("Level 8:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
    if caster_lv >= 17:
        _lbl("Level 9:", pos.reset("x"), pos.increase("y", 20))
        _chk(pos.set("x", 47), pos.same("y"))
    if caster_lv >= 18:
        _chk(pos.set("x", 87), pos.increase("y", -80))
    if caster_lv >= 19:
        _chk(pos.set("x", 67), pos.increase("y", 20))
    if caster_lv == 20:
        _chk(pos.set("x", 67), pos.increase("y", 20))


# ── per-caster header ─────────────────────────────────────────────────────────

def _create_caster_header(i: int) -> None:
    col = i * _COL_W
    header_widgets: list = []

    lv_var = tk.IntVar(value=1)
    GSM.Spell_caster_level_vars[i] = lv_var

    name_label = tk.Label(GSM.Spell_caster_frame, text="Name:")
    name_label.place(x=5 + col, y=80)
    header_widgets.append(name_label)

    name_entry = tk.Entry(GSM.Spell_caster_frame, borderwidth=2, width=15)
    name_entry.place(x=52 + col, y=80)
    header_widgets.append(name_entry)
    GSM.Spell_caster_name_entries[i] = name_entry

    lv_label = tk.Label(GSM.Spell_caster_frame, text="Level:")
    lv_label.place(x=5 + col, y=115)
    header_widgets.append(lv_label)

    lv_dropdown = tk.OptionMenu(
        GSM.Spell_caster_frame,
        lv_var,
        *range(1, 21),
        command=lambda lv, idx=i: DrawSpellBoxes(lv, idx),
    )
    lv_dropdown.place(x=50 + col, y=111)
    header_widgets.append(lv_dropdown)

    spells_btn = tk.Button(
        GSM.Spell_caster_frame,
        text="Spells",
        command=lambda idx=i: _open_spell_list(idx),
        width=7,
    )
    spells_btn.place(x=107 + col, y=113)
    header_widgets.append(spells_btn)

    GSM.Spell_caster_header_widgets[i] = header_widgets


# ── public API ────────────────────────────────────────────────────────────────

def CreateSpellCasters(n_casters: int, _rel_pos=None) -> None:
    """Incrementally add or remove caster columns. Existing casters are preserved."""
    old_n = len(GSM.Spell_caster_header_widgets)

    for i in range(n_casters, old_n):
        for w in GSM.Spell_caster_header_widgets.pop(i, []):
            w.destroy()
        for w in GSM.Spell_checkboxes_dict.pop(i, []):
            w.destroy()
        GSM.Spell_caster_level_vars.pop(i, None)
        GSM.Spell_caster_name_entries.pop(i, None)

    for i in range(old_n, n_casters):
        _create_caster_header(i)
        DrawSpellBoxes(1, i)


def SpellCasters(RelPosSpellCast) -> None:
    tk.Label(GSM.Spell_caster_frame, text="Spell casters", font=GSM.Title_font).place(
        x=RelPosSpellCast.reset("x"), y=RelPosSpellCast.reset("y")
    )
    tk.Label(GSM.Spell_caster_frame, text="How many spell casters:").place(
        x=RelPosSpellCast.same("x"), y=RelPosSpellCast.increase("y", 35)
    )
    tk.OptionMenu(
        GSM.Spell_caster_frame,
        GSM.N_casters_int,
        *[1, 2, 3, 4, 5],
        command=lambda value: CreateSpellCasters(value),
    ).place(x=RelPosSpellCast.increase("x", 135), y=RelPosSpellCast.increase("y", -4))

    tk.Button(
        GSM.Spell_caster_frame,
        text="Global Spell Library",
        command=_open_global_spell_library,
        bg="#554488", fg="white",
    ).place(x=RelPosSpellCast.increase("x", 90), y=RelPosSpellCast.same("y"))

    CreateSpellCasters(GSM.N_casters_int.get())
