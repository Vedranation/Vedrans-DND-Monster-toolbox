import tkinter as tk
from tkinter import ttk

from GlobalStateManager import GSM
from utilities import RollDice


def MassRoll(RelPosMassroll, RelPosMonsters) -> None:
    RelPosMassroll.constant_y = 25

    def _roll_d20(rolltype: str) -> int:
        if rolltype == "Advantage":
            return max(RollDice("d20"), RollDice("d20"))
        if rolltype == "Disadvantage":
            return min(RollDice("d20"), RollDice("d20"))
        if rolltype == "Super Advantage":
            return max(RollDice("d20"), RollDice("d20"), RollDice("d20"))
        if rolltype == "Super Disadvantage":
            return min(RollDice("d20"), RollDice("d20"), RollDice("d20"))
        return RollDice("d20")

    _SAVE_ATTRS: dict[str, tuple[str, str]] = {
        "STR": ("savingthrow_str_mod_int", "savingthrow_str_roll_type_str"),
        "DEX": ("savingthrow_dex_mod_int", "savingthrow_dex_roll_type_str"),
        "CON": ("savingthrow_con_mod_int", "savingthrow_con_roll_type_str"),
        "INT": ("savingthrow_int_mod_int", "savingthrow_int_roll_type_str"),
        "WIS": ("savingthrow_wis_mod_int", "savingthrow_wis_roll_type_str"),
        "CHA": ("savingthrow_cha_mod_int", "savingthrow_cha_roll_type_str"),
    }

    # ── Mass Monster Saving Throws ────────────────────────────────────────────

    save_frame = tk.LabelFrame(GSM.Mass_roll_frame, text="Mass monster saving throw", font=GSM.Title_font)
    save_frame.place(x=5, y=5, width=400, height=270)
    save_frame.columnconfigure(1, weight=1)
    save_frame.rowconfigure(4, weight=1)

    tk.Label(save_frame, text="Save type:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
    _mass_save_type = tk.StringVar(value="CON")
    ttk.Combobox(
        save_frame, textvariable=_mass_save_type, values=GSM.Saving_throw_types, width=6, state="readonly"
    ).grid(row=0, column=1, sticky="w", padx=4, pady=3)

    tk.Label(save_frame, text="DC:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
    _mass_save_dc = tk.IntVar(value=13)
    ttk.Spinbox(save_frame, textvariable=_mass_save_dc, from_=1, to=30, width=4).grid(
        row=1, column=1, sticky="w", padx=4, pady=3
    )

    tk.Label(save_frame, text="Roll type:").grid(row=2, column=0, sticky="w", padx=4, pady=3)
    _mass_save_rt = tk.StringVar(value="Monster default")
    ttk.Combobox(
        save_frame, textvariable=_mass_save_rt,
        values=["Monster default", *GSM.Roll_types], width=14, state="readonly"
    ).grid(row=2, column=1, sticky="w", padx=4, pady=3)

    tk.Label(save_frame, text="Monsters:", font=GSM.Target_font).grid(
        row=3, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 0)
    )

    rows_container = tk.Frame(save_frame)
    rows_container.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=4)

    # Each entry: (name_var, count_var, combo, row_frame, result_var)
    _mass_save_rows: list[tuple[tk.StringVar, tk.IntVar, ttk.Combobox, tk.Frame, tk.StringVar]] = []

    def _monster_names() -> list[str]:
        return [m.name_str.get() for m in GSM.Monster_obj_list] or ["(none)"]

    def _add_mass_save_row() -> None:
        row_frame = tk.Frame(rows_container)
        row_frame.pack(fill="x", pady=1)

        name_var = tk.StringVar(value=_monster_names()[0])
        combo = ttk.Combobox(row_frame, textvariable=name_var, values=_monster_names(), width=12, state="readonly")
        combo.pack(side="left")

        tk.Label(row_frame, text="×").pack(side="left", padx=(3, 1))

        count_var = tk.IntVar(value=1)
        ttk.Spinbox(row_frame, textvariable=count_var, from_=0, to=50, width=3).pack(side="left")

        result_var = tk.StringVar()
        row_entry = (name_var, count_var, combo, row_frame, result_var)
        _mass_save_rows.append(row_entry)

        def _remove() -> None:
            _mass_save_rows.remove(row_entry)
            row_frame.destroy()

        tk.Button(row_frame, text="×", command=_remove, fg="red", width=1, relief="flat").pack(side="left", padx=2)
        tk.Label(row_frame, textvariable=result_var, font=("Courier", 9), anchor="w").pack(
            side="left", padx=(6, 0), fill="x", expand=True
        )

    _add_mass_save_row()
    _add_mass_save_row()

    _total_var = tk.StringVar()

    def _roll_mass_saves() -> None:
        monster_map = {m.name_str.get(): m for m in GSM.Monster_obj_list}
        which_save = _mass_save_type.get()
        dc = _mass_save_dc.get()
        rt_override = _mass_save_rt.get()
        mod_attr, rt_attr = _SAVE_ATTRS.get(which_save, _SAVE_ATTRS["CON"])
        total_pass = total_n = 0
        for name_var, count_var, combo, row_frame, result_var in _mass_save_rows:
            combo["values"] = _monster_names()
            name = name_var.get()
            count = count_var.get()
            mob = monster_map.get(name)
            if mob is None or count <= 0:
                result_var.set("")
                continue
            mod = getattr(mob, mod_attr).get()
            rt = getattr(mob, rt_attr).get() if rt_override == "Monster default" else rt_override
            passes = 0
            rolls: list[int] = []
            for _ in range(count):
                roll = _roll_d20(rt)
                total = roll + mod
                if not (roll == 1 and GSM.Nat1_always_miss_bool.get()) and total >= dc:
                    passes += 1
                rolls.append(total)
            rolls.sort(reverse=True)
            result_var.set(f"{passes}/{count}  {rolls}")
            total_pass += passes
            total_n += count
        _total_var.set(
            f"Total: {total_pass}/{total_n}  ({total_n - total_pass} fail)" if total_n else ""
        )

    def _load_monster_groups(groups: dict[str, int]) -> None:
        """Populate mass save rows from a {monster_name: count} dict (called from BoardTab)."""
        for _, _, _, row_frame, _ in list(_mass_save_rows):
            row_frame.destroy()
        _mass_save_rows.clear()
        _total_var.set("")
        names = _monster_names()
        for name, count in groups.items():
            _add_mass_save_row()
            name_var, count_var, combo, _, result_var = _mass_save_rows[-1]
            combo["values"] = names
            if name in names:
                name_var.set(name)
            count_var.set(count)
            result_var.set("")
        if not _mass_save_rows:
            _add_mass_save_row()

    GSM.Load_mass_saves = _load_monster_groups

    tk.Button(GSM.Mass_roll_frame, text="+ Add row", command=_add_mass_save_row, width=8).place(x=5, y=278)
    tk.Button(
        GSM.Mass_roll_frame, text="Roll mass saves", command=_roll_mass_saves, padx=4, background="grey"
    ).place(x=90, y=278)
    tk.Label(GSM.Mass_roll_frame, textvariable=_total_var, font=("Courier", 9), anchor="w").place(x=5, y=307)

    # TODO: Mass monster skill check — add once MonsterData tracks per-skill modifiers.
    # When implemented, add a new section mirroring Mass Monster Saving Throws above
    # but reading skill mods from MonsterData instead of saves.

    # ── Quick Monster Save ────────────────────────────────────────────────────

    def RollQuickMobSaveButton(current_button_y: int) -> None:
        for widget in GSM.Results_quick_mob_save_widgets_to_clear:
            widget.destroy()
        GSM.Results_quick_mob_save_widgets_to_clear.clear()

        monster_map = {monster.name_str.get(): monster for monster in GSM.Monster_obj_list}
        monster_obj = monster_map.get(GSM.Quick_save_which_mob_str.get(), None)
        which_save = GSM.Quick_save_which_save.get()
        if monster_obj is None:
            raise Exception("No monster selected for quick save throw")

        rolltype = GSM.Quick_monster_save_rolltype_str.get()
        mod_attr, rt_attr = _SAVE_ATTRS[which_save]
        modifier = getattr(monster_obj, mod_attr).get()
        if rolltype == "Monster default":
            rolltype = getattr(monster_obj, rt_attr).get()

        roll = _roll_d20(rolltype)
        roll_total = roll + modifier
        text_colour = "black"
        if roll == 1 and GSM.Nat1_always_miss_bool.get():
            roll_total = f"nat1 ({roll_total})"
            text_colour = "red"
        elif roll == 20:
            roll_total = f"nat20 ({roll_total})"
            text_colour = "green"

        quick_save_results_label = tk.Label(
            GSM.Mass_roll_frame, text=f"{monster_obj.name_str.get()} rolled a {roll_total}", fg=text_colour
        )
        quick_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.set("y", current_button_y + 30))
        GSM.Results_quick_mob_save_widgets_to_clear.append(quick_save_results_label)

    def QuickMonsterSave() -> None:
        quick_monster_save_label = tk.Label(
            GSM.Mass_roll_frame, text="Quick monster\nsaving throw", font=GSM.Title_font
        )
        quick_monster_save_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.set("y", 340))

        quick_monster_save_label2 = tk.Label(GSM.Mass_roll_frame, text="Which monster: ")
        quick_monster_save_label2.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 45))
        quick_monster_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Quick_save_which_mob_str, *GSM.Monster_obj_list)
        GSM.Quick_save_which_mob_str.set(GSM.Monster_obj_list[0])
        quick_monster_dropdown.place(x=RelPosMassroll.increase("x", 90), y=RelPosMassroll.increase("y", -4))
        GSM.OnTab_MassSaves_reset_widgets.append(
            [quick_monster_dropdown, GSM.RelPosMassroll.same("x"), GSM.RelPosMassroll.same("y"), "which_monster"]
        )

        quick_monster_save_label3 = tk.Label(GSM.Mass_roll_frame, text="Which save:")
        quick_monster_save_label3.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 35))
        select_save_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Quick_save_which_save, *GSM.Saving_throw_types)
        select_save_dropdown.place(x=RelPosMassroll.increase("x", 80), y=RelPosMassroll.increase("y", -4))

        quick_monster_rolltype_label = tk.Label(GSM.Mass_roll_frame, text="Roll type:")
        quick_monster_rolltype_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 35))
        quick_mob_save_rolltype_dropdown = tk.OptionMenu(
            GSM.Mass_roll_frame, GSM.Quick_monster_save_rolltype_str, *["Monster default", *GSM.Roll_types]
        )
        quick_mob_save_rolltype_dropdown.place(x=RelPosMassroll.increase("x", 70), y=RelPosMassroll.increase("y", -4))

        mob_quick_save_button = tk.Button(
            GSM.Mass_roll_frame,
            text="Roll save",
            state="normal",
            command=lambda: RollQuickMobSaveButton(int(mob_quick_save_button.place_info()["y"])),
            padx=9,
            background="grey",
        )
        mob_quick_save_button.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))

    QuickMonsterSave()

    # ── Party Skill Check ─────────────────────────────────────────────────────

    def PartySkillCheckRoll(button_pos) -> None:
        for widget in GSM.PartySkillCheckResults:
            widget.destroy()
        GSM.PartySkillCheckResults.clear()
        results = []
        for player in GSM.Target_obj_list:
            skill_mod = int(getattr(player, f"{GSM.WhichSkillToCheck.get().lower()}_mod_int").get())
            rolltype = str(getattr(player, f"{GSM.WhichSkillToCheck.get().lower()}_roll_type_str").get())
            roll = _roll_d20(rolltype)
            roll_total = roll + skill_mod
            if roll == 1 and GSM.Nat1_always_miss_bool.get():
                passed = "Nat1"
            elif roll == 20:
                passed = "Nat20"
            elif roll_total >= GSM.SkillCheckDC.get():
                passed = "Passed"
            else:
                passed = "Failed"
            results.append([player.name_str.get(), roll_total, passed])

        button_x = int(button_pos["x"])
        button_y = int(button_pos["y"])
        GSM.RelPosMassroll.checkpoint_set("x", button_x)
        GSM.RelPosMassroll.checkpoint_set("y", button_y + 30)
        for i, result in enumerate(results):
            if result[2] == "Nat1":
                text_colour2 = "red"
                text_colour3 = "gray"
            elif result[2] == "Nat20":
                text_colour2 = "green"
                text_colour3 = "black"
            elif result[2] == "Failed":
                text_colour2 = "gray"
                text_colour3 = "gray"
            else:
                text_colour2 = "black"
                text_colour3 = "black"

            lbl1 = tk.Label(GSM.Mass_roll_frame, text=str(result[0]), fg=text_colour3)
            lbl1.place(x=GSM.RelPosMassroll.checkpoint_get("x"), y=GSM.RelPosMassroll.checkpoint_get("y") + 20 * i)
            GSM.PartySkillCheckResults.append(lbl1)

            lbl2 = tk.Label(GSM.Mass_roll_frame, text=str(result[1]), fg=text_colour2)
            lbl2.place(x=GSM.RelPosMassroll.checkpoint_get("x") + 80, y=GSM.RelPosMassroll.checkpoint_get("y") + 20 * i)
            GSM.PartySkillCheckResults.append(lbl2)

            lbl3 = tk.Label(GSM.Mass_roll_frame, text=str(result[2]), fg=text_colour3)
            lbl3.place(x=GSM.RelPosMassroll.checkpoint_get("x") + 120, y=GSM.RelPosMassroll.checkpoint_get("y") + 20 * i)
            GSM.PartySkillCheckResults.append(lbl3)

    def PartySkillCheckUI() -> None:
        RelPosMassroll.checkpoint_set("x", 580)
        skillcheck_label = tk.Label(GSM.Mass_roll_frame, text="Party skill check", font=GSM.Title_font)
        skillcheck_label.place(
            x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.reset("y")
        )

        select_skill_label = tk.Label(GSM.Mass_roll_frame, text="Select skill: ")
        select_skill_label.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 37))

        select_skill_dropdown = tk.OptionMenu(
            GSM.Mass_roll_frame, GSM.WhichSkillToCheck, *["Perception", "Investigation", "Arcana", "Insight", "Stealth"]
        )
        select_skill_dropdown.place(x=RelPosMassroll.increase("x", 60), y=RelPosMassroll.increase("y", -4))

        select_skill_label2 = tk.Label(GSM.Mass_roll_frame, text="DC:")
        select_skill_label2.place(
            x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.increase("y", 33)
        )
        dc_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, textvariable=GSM.SkillCheckDC, width=3, from_=5, to=30)
        dc_spinbox.place(x=RelPosMassroll.increase("x", 30), y=RelPosMassroll.increase("y", 2))

        rollskillcheck_button = tk.Button(
            GSM.Mass_roll_frame,
            text="Party skill check",
            state="normal",
            command=lambda: PartySkillCheckRoll(rollskillcheck_button.place_info()),
            padx=9,
            background="grey",
        )
        rollskillcheck_button.place(
            x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.increase("y", 28)
        )

    PartySkillCheckUI()
