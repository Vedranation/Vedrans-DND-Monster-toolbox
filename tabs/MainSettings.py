import tkinter as tk
from tkinter import messagebox

from GlobalStateManager import GSM
from persistence.appstate import (
    deserialize_monster,
    deserialize_player,
    serialize_monster,
    serialize_player,
)
from persistence.preset import delete_preset, list_presets, load_preset, save_preset
from tabs.MonsterCreation import PreservePreviousMonsters
from tabs.PlayerCreation import PreservePreviousTargets

# Module-level references set by Settings() so Save/Load can read the active name.
_preset_name_var: tk.StringVar | None = None
_preset_menu: tk.OptionMenu | None = None
_status_var: tk.StringVar | None = None


def _refresh_preset_menu() -> None:
    if _preset_menu is None or _preset_name_var is None:
        return
    names = list_presets() or ["preset1"]
    menu = _preset_menu["menu"]
    menu.delete(0, "end")
    for name in names:
        menu.add_command(label=name, command=lambda n=name: _preset_name_var.set(n))
    if _preset_name_var.get() not in names:
        _preset_name_var.set(names[0])


def Settings(RelPosSettings) -> None:
    global _preset_name_var, _preset_menu, _status_var

    # Main settings text
    main_settings_text_label = tk.Label(GSM.Settings_frame, text="Main settings", font=GSM.Title_font)
    main_settings_text_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.same("y"))

    # Meets it beats it checkbox
    checkbox_label = tk.Checkbutton(
        GSM.Settings_frame,
        text="Attack roll = AC is hit (meets it beats it)",
        variable=GSM.Meets_it_beats_it_bool,
        onvalue=True,
        offvalue=False,
    )
    checkbox_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # Extra crit die is max possible roll
    def EnableDisableMaxDiceRoll() -> None:
        if not GSM.Crits_double_dmg_bool.get():
            Checkbox_CritExtraDiceMaxDmg.config(state="normal")
        else:
            Checkbox_CritExtraDiceMaxDmg.config(state="disabled")
            GSM.Crits_extra_die_is_max_bool.set(False)

    Checkbox_CritExtraDiceMaxDmg = tk.Checkbutton(
        GSM.Settings_frame,
        text="Crit extra roll is max possible",
        variable=GSM.Crits_extra_die_is_max_bool,
        onvalue=True,
        offvalue=False,
    )
    Checkbox_CritExtraDiceMaxDmg.place(
        x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y)
    )
    Checkbox_CritExtraDiceMaxDmg.config(state="disabled")
    GSM.Load_widgets_mainsettings_dict["Checkbox_CritExtraDiceMaxDmg"] = Checkbox_CritExtraDiceMaxDmg

    # Crits double dice checkbox
    checkbox_label2 = tk.Checkbutton(
        GSM.Settings_frame,
        text="Crits double TOTAL dmg instead of dice",
        variable=GSM.Crits_double_dmg_bool,
        onvalue=True,
        offvalue=False,
        command=EnableDisableMaxDiceRoll,
    )
    checkbox_label2.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # Nat1 always miss
    checkbox_label4 = tk.Checkbutton(
        GSM.Settings_frame, text="NAT 1 always miss", variable=GSM.Nat1_always_miss_bool, onvalue=True, offvalue=False
    )
    checkbox_label4.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # (Dis)advantages combine into super (dis)advantages
    checkbox_label5 = tk.Checkbutton(
        GSM.Settings_frame,
        text="2 Advantages combine into 1 Super Advantage",
        variable=GSM.Adv_combine_bool,
        onvalue=True,
        offvalue=False,
    )
    checkbox_label5.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # Adv/disadv stacking mode
    tk.Label(GSM.Settings_frame, text="Adv/Disadv stacking:").place(
        x=RelPosSettings.reset("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y)
    )
    tk.OptionMenu(GSM.Settings_frame, GSM.Adv_mode, "RAW", "Arithmetic").place(
        x=RelPosSettings.increase("x", 140), y=RelPosSettings.increase("y", -4)
    )

    # Auto-disable 0 HP tokens
    tk.Checkbutton(
        GSM.Settings_frame,
        text="Automatically disable 0 HP tokens",
        variable=GSM.Auto_disable_zero_hp_bool,
        onvalue=True,
        offvalue=False,
    ).place(x=RelPosSettings.reset("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # Ignore monster damage resistances / immunities
    tk.Checkbutton(
        GSM.Settings_frame,
        text="Ignore monster damage resistances/immunities/vulnerabilities",
        variable=GSM.Ignore_resistances_bool,
        onvalue=True,
        offvalue=False,
    ).place(x=RelPosSettings.reset("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # ── Preset name entry + dropdown ──────────────────────────────────────────
    _preset_name_var = tk.StringVar(value="preset1")

    preset_label = tk.Label(GSM.Settings_frame, text="Preset name:")
    preset_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y * 1.5))

    preset_name_entry = tk.Entry(GSM.Settings_frame, textvariable=_preset_name_var, width=14)
    preset_name_entry.place(x=RelPosSettings.increase("x", 80), y=RelPosSettings.same("y"))

    initial_names = list_presets() or ["preset1"]
    _preset_menu = tk.OptionMenu(GSM.Settings_frame, _preset_name_var, *initial_names)
    _preset_menu.place(x=RelPosSettings.increase("x", 100), y=RelPosSettings.increase("y", -4))

    # ── Save / Load / Delete buttons ──────────────────────────────────────────
    RelPosSettings.reset("x")
    save_button = tk.Button(
        GSM.Settings_frame, text="Save preset", state="normal", command=Save, background="green"
    )
    save_button.place(
        x=RelPosSettings.increase("x", 10), y=RelPosSettings.increase("y", RelPosSettings.constant_y * 1.5)
    )

    load_button = tk.Button(
        GSM.Settings_frame, text="Load preset", state="normal", command=Load, background="green"
    )
    load_button.place(x=RelPosSettings.increase("x", 80), y=RelPosSettings.same("y"))

    delete_button = tk.Button(
        GSM.Settings_frame, text="Delete preset", state="normal", command=Delete, background="#cc4444", fg="white"
    )
    delete_button.place(x=RelPosSettings.increase("x", 80), y=RelPosSettings.same("y"))

    _status_var = tk.StringVar(value="")
    tk.Label(GSM.Settings_frame, textvariable=_status_var, fg="#226622",
             font=("Helvetica", 8)).place(
        x=RelPosSettings.reset("x"), y=RelPosSettings.increase("y", 20)
    )

    # ── Board settings ───────────────────────────────────────────────────────
    RelPosSettings.reset("x")
    board_title = tk.Label(GSM.Settings_frame, text="Board settings", font=GSM.Title_font)
    board_title.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", 35))

    for _lbl, _var, _opts in [
        ("Diagonal movement:", GSM.Board_diagonal_mode, ["standard", "5-10-5"]),
        ("Flanking geometry:", GSM.Board_flank_geometry, ["hard", "soft"]),
        ("Flank benefit:", GSM.Board_flank_benefit, ["advantage", "+2"]),
        ("Range check:", GSM.Board_range_mode, ["warn", "block"]),
    ]:
        tk.Label(GSM.Settings_frame, text=_lbl).place(
            x=RelPosSettings.reset("x"), y=RelPosSettings.increase("y", 28)
        )
        tk.OptionMenu(GSM.Settings_frame, _var, *_opts).place(
            x=RelPosSettings.increase("x", 140), y=RelPosSettings.increase("y", -4)
        )


def _build_save_data() -> dict:
    return {
        "Meets_it_beats_it_bool": GSM.Meets_it_beats_it_bool.get(),
        "Crits_double_dmg_bool": GSM.Crits_double_dmg_bool.get(),
        "Crits_extra_die_is_max_bool": GSM.Crits_extra_die_is_max_bool.get(),
        "Nat1_always_miss_bool": GSM.Nat1_always_miss_bool.get(),
        "Adv_combine_bool": GSM.Adv_combine_bool.get(),
        "Adv_mode": GSM.Adv_mode.get(),
        "Auto_disable_zero_hp_bool": GSM.Auto_disable_zero_hp_bool.get(),
        "Ignore_resistances_bool": GSM.Ignore_resistances_bool.get(),
        "Board_diagonal_mode": GSM.Board_diagonal_mode.get(),
        "Board_flank_geometry": GSM.Board_flank_geometry.get(),
        "Board_flank_benefit": GSM.Board_flank_benefit.get(),
        "Board_range_mode": GSM.Board_range_mode.get(),
        "spell_library": GSM.Spell_library,
        "N_casters_int": GSM.N_casters_int.get(),
        "N_targets_int": GSM.N_targets_int.get(),
        "Target_obj_list": [serialize_player(p.to_data()) for p in GSM.Target_obj_list],
        "N_monsters_int": GSM.N_monsters_int.get(),
        "Monster_obj_list": [serialize_monster(m.to_data()) for m in GSM.Monster_obj_list],
    }


def _apply_loaded_data(loaded_data: dict) -> None:
    GSM.Meets_it_beats_it_bool.set(loaded_data["Meets_it_beats_it_bool"])
    GSM.Crits_double_dmg_bool.set(loaded_data["Crits_double_dmg_bool"])
    if not GSM.Crits_double_dmg_bool.get():
        GSM.Load_widgets_mainsettings_dict["Checkbox_CritExtraDiceMaxDmg"].config(state="normal")
    else:
        GSM.Load_widgets_mainsettings_dict["Checkbox_CritExtraDiceMaxDmg"].config(state="disabled")
    GSM.Crits_extra_die_is_max_bool.set(loaded_data["Crits_extra_die_is_max_bool"])
    GSM.Nat1_always_miss_bool.set(loaded_data["Nat1_always_miss_bool"])
    GSM.Adv_combine_bool.set(loaded_data["Adv_combine_bool"])
    if "Adv_mode" in loaded_data:
        GSM.Adv_mode.set(loaded_data["Adv_mode"])
    if "Auto_disable_zero_hp_bool" in loaded_data:
        GSM.Auto_disable_zero_hp_bool.set(loaded_data["Auto_disable_zero_hp_bool"])
    if "Ignore_resistances_bool" in loaded_data:
        GSM.Ignore_resistances_bool.set(loaded_data["Ignore_resistances_bool"])
    if "Board_diagonal_mode" in loaded_data:
        GSM.Board_diagonal_mode.set(loaded_data["Board_diagonal_mode"])
    if "Board_flank_geometry" in loaded_data:
        GSM.Board_flank_geometry.set(loaded_data["Board_flank_geometry"])
    if "Board_flank_benefit" in loaded_data:
        GSM.Board_flank_benefit.set(loaded_data["Board_flank_benefit"])
    if "Board_range_mode" in loaded_data:
        GSM.Board_range_mode.set(loaded_data["Board_range_mode"])

    if "spell_library" in loaded_data:
        GSM.Spell_library.clear()
        GSM.Spell_library.extend(loaded_data["spell_library"])

    GSM.N_targets_int.set(loaded_data["N_targets_int"])
    PreservePreviousTargets(GSM.N_targets_int.get(), GSM.RelPosTargets)
    for i, playerObj in enumerate(GSM.Target_obj_list[: GSM.N_targets_int.get()]):
        if i < len(loaded_data["Target_obj_list"]):
            playerObj.from_data(deserialize_player(loaded_data["Target_obj_list"][i]))
            playerObj._my_button.config(text=playerObj.name_str.get())

    GSM.N_monsters_int.set(loaded_data["N_monsters_int"])
    PreservePreviousMonsters(GSM.N_monsters_int.get(), GSM.RelPosMonsters)
    for i, monsterObj in enumerate(GSM.Monster_obj_list[: GSM.N_monsters_int.get()]):
        if i < len(loaded_data["Monster_obj_list"]):
            monsterObj.from_data(deserialize_monster(loaded_data["Monster_obj_list"][i]))
            monsterObj._my_button.config(text=monsterObj.name_str.get())


def _set_status(msg: str) -> None:
    if _status_var is not None:
        _status_var.set(msg)


def Save() -> None:
    name = _preset_name_var.get().strip() if _preset_name_var else "preset1"
    if not name:
        name = "preset1"
    save_preset(name, _build_save_data())
    _refresh_preset_menu()
    _set_status(f"Saved '{name}'.")


def Load() -> None:
    name = _preset_name_var.get().strip() if _preset_name_var else "preset1"
    try:
        loaded_data = load_preset(name)
    except FileNotFoundError:
        messagebox.showerror("Load failed", f"Preset '{name}' not found.")
        _set_status(f"Load failed: '{name}' not found.")
        return
    _apply_loaded_data(loaded_data)
    _set_status(f"Loaded '{name}'.")


def Delete() -> None:
    name = _preset_name_var.get().strip() if _preset_name_var else ""
    if not name:
        return
    if not messagebox.askyesno("Delete preset", f"Delete preset '{name}'?"):
        return
    delete_preset(name)
    _refresh_preset_menu()
    _set_status(f"Deleted '{name}'.")
