import tkinter as tk
from tkinter import ttk

from GlobalStateManager import GSM
from engine.constants import (
    ALL_CONDITIONS as _ALL_CONDITIONS,
    CREATURE_SIZES as _CREATURE_SIZES,
    CREATURE_TYPES as _CREATURE_TYPES,
)
from engine.models import AttackSpec, MonsterData
from persistence.appstate import (
    attack_spec_to_dict as _attack_spec_to_dict,
    dict_to_attack_spec as _dict_to_attack_spec,
)

class MonsterStats:
    def __init__(self):
        self.name_str: str = tk.StringVar()
        # to hit modifiers and multiattack
        self.n_attacks: int = tk.IntVar(value=1)
        self.to_hit_mod: int = tk.IntVar(value=5)
        self.roll_type: str = tk.StringVar(value="Normal")  # Normal
        self.ac_int = tk.IntVar(value=13)
        self.max_hp_int = tk.IntVar(value=10)
        # dmg 1
        self.dmg_type_1: str = tk.StringVar(value="bludgeoning")
        self.dmg_n_die_1: int = tk.IntVar(value=1)
        self.dmg_die_type_1: str = tk.StringVar(value="d6")
        self.dmg_flat_1: int = tk.IntVar(value=3)
        # dmg 2
        self.dmg_type_2: str = tk.StringVar(value="fire")
        self.dmg_die_type_2: str = tk.StringVar(value="d4")
        self.dmg_n_die_2: int = tk.IntVar(value=0)
        self.dmg_flat_2: int = tk.IntVar(value=0)
        # force saving throw on hit
        self.on_hit_force_saving_throw_bool: bool = tk.BooleanVar(value=False)  # False
        self.on_hit_save_dc: int = tk.IntVar(value=13)
        self.on_hit_save_type: str = tk.StringVar(value="STR")
        # extra abilities
        self.reroll_1_on_hit: bool = tk.BooleanVar(value=False)  # once rerolls a 1 TO HIT (halfing luck)
        self.reroll_1_2_dmg: bool = tk.BooleanVar(value=False)  # GW fighting style - reroll 1 or 2 on DMG once
        self.brutal_critical: bool = tk.BooleanVar(value=False)  # On crit, rolls an extra dmg die
        self.crit_number: int = tk.IntVar(value=20)  # Usually 20, in case you want crit on 19 or 18
        self.savage_attacker: bool = tk.BooleanVar(value=False)  # Once per turn, roll dmg twice and use higher number
        self.bane: bool = tk.BooleanVar(value=False)
        self.bless: bool = tk.BooleanVar(value=False)

        # board / range
        self.attack_range_ft_int = tk.IntVar(value=5)
        self.ignore_ranged_in_melee_bool = tk.BooleanVar(value=False)
        self.highlight_range_ft_int = tk.IntVar(value=5)

        # speed
        self.walking_speed_int = tk.IntVar(value=20)
        self.flying_speed_int = tk.IntVar(value=0)
        self.climbing_speed_int = tk.IntVar(value=0)
        self.burrowing_speed_int = tk.IntVar(value=0)
        self.swimming_speed_int = tk.IntVar(value=0)

        # creature info
        self.creature_type_str = tk.StringVar(value="")
        self.creature_size_str = tk.StringVar(value="Medium")

        # senses (ft, 0 = none)
        self.darkvision_int = tk.IntVar(value=0)
        self.blindsight_int = tk.IntVar(value=0)
        self.tremorsense_int = tk.IntVar(value=0)
        self.truesight_int = tk.IntVar(value=0)

        # damage resistances / immunities / condition immunities
        self.damage_resistances_vars: dict[str, tk.BooleanVar] = {
            dt: tk.BooleanVar(value=False) for dt in GSM.Dmg_types
        }
        self.damage_immunities_vars: dict[str, tk.BooleanVar] = {
            dt: tk.BooleanVar(value=False) for dt in GSM.Dmg_types
        }
        self.damage_vulnerabilities_vars: dict[str, tk.BooleanVar] = {
            dt: tk.BooleanVar(value=False) for dt in GSM.Dmg_types
        }
        self.condition_immunities_vars: dict[str, tk.BooleanVar] = {
            c: tk.BooleanVar(value=False) for c in _ALL_CONDITIONS
        }

        # initiative
        self.initiative_mod_int = tk.IntVar(value=0)

        # saving throws
        self.savingthrow_str_mod_int = tk.IntVar(value=1)
        self.savingthrow_str_roll_type_str = tk.StringVar(value="Normal")
        self.savingthrow_dex_mod_int = tk.IntVar(value=-2)
        self.savingthrow_dex_roll_type_str = tk.StringVar(value="Normal")
        self.savingthrow_con_mod_int = tk.IntVar(value=3)
        self.savingthrow_con_roll_type_str = tk.StringVar(value="Normal")
        self.savingthrow_int_mod_int = tk.IntVar(value=-4)
        self.savingthrow_int_roll_type_str = tk.StringVar(value="Normal")
        self.savingthrow_wis_mod_int = tk.IntVar(value=-2)
        self.savingthrow_wis_roll_type_str = tk.StringVar(value="Normal")
        self.savingthrow_cha_mod_int = tk.IntVar(value=-3)
        self.savingthrow_cha_roll_type_str = tk.StringVar(value="Normal")
        self.passiveperception_int = tk.IntVar(value=8)

        # attack name shown in the sequence listbox
        self.attack_name_str = tk.StringVar(value="Attack")
        # list of attack-spec dicts (one per entry in the sequence)
        self._attack_specs: list[dict] = []
        self._current_attack_idx: int = 0

        "Monsters Frame display widgets in row like dmg types"
        self._my_button = None  # Stores his own button
        self._monster_dmg1_extra_text_label2 = None
        self._monster_dmg2_extra_text_label2 = None

    def __str__(self):
        return self.name_str.get()

    def _current_to_dict(self) -> dict:
        return {
            "name": self.attack_name_str.get(),
            "to_hit_mod": self.to_hit_mod.get(),
            "roll_type": self.roll_type.get(),
            "n_attacks": self.n_attacks.get(),
            "dmg_n_die_1": self.dmg_n_die_1.get(),
            "dmg_die_type_1": self.dmg_die_type_1.get(),
            "dmg_flat_1": self.dmg_flat_1.get(),
            "dmg_type_1": self.dmg_type_1.get(),
            "dmg_n_die_2": self.dmg_n_die_2.get(),
            "dmg_die_type_2": self.dmg_die_type_2.get(),
            "dmg_flat_2": self.dmg_flat_2.get(),
            "dmg_type_2": self.dmg_type_2.get(),
            "crit_number": self.crit_number.get(),
            "brutal_critical": self.brutal_critical.get(),
            "savage_attacker": self.savage_attacker.get(),
            "reroll_1_on_hit": self.reroll_1_on_hit.get(),
            "reroll_1_2_dmg": self.reroll_1_2_dmg.get(),
            "bane": self.bane.get(),
            "bless": self.bless.get(),
            "on_hit_force_save": self.on_hit_force_saving_throw_bool.get(),
            "on_hit_save_dc": self.on_hit_save_dc.get(),
            "on_hit_save_type": self.on_hit_save_type.get(),
        }

    def _dict_to_current(self, d: dict) -> None:
        self.attack_name_str.set(d.get("name", "Attack"))
        self.to_hit_mod.set(d.get("to_hit_mod", 5))
        self.roll_type.set(d.get("roll_type", "Normal"))
        self.n_attacks.set(d.get("n_attacks", 1))
        self.dmg_n_die_1.set(d.get("dmg_n_die_1", 1))
        self.dmg_die_type_1.set(d.get("dmg_die_type_1", "d6"))
        self.dmg_flat_1.set(d.get("dmg_flat_1", 3))
        self.dmg_type_1.set(d.get("dmg_type_1", "bludgeoning"))
        self.dmg_n_die_2.set(d.get("dmg_n_die_2", 0))
        self.dmg_die_type_2.set(d.get("dmg_die_type_2", "d4"))
        self.dmg_flat_2.set(d.get("dmg_flat_2", 0))
        self.dmg_type_2.set(d.get("dmg_type_2", "fire"))
        self.crit_number.set(d.get("crit_number", 20))
        self.brutal_critical.set(d.get("brutal_critical", False))
        self.savage_attacker.set(d.get("savage_attacker", False))
        self.reroll_1_on_hit.set(d.get("reroll_1_on_hit", False))
        self.reroll_1_2_dmg.set(d.get("reroll_1_2_dmg", False))
        self.bane.set(d.get("bane", False))
        self.bless.set(d.get("bless", False))
        # support both new key and old save-format key
        self.on_hit_force_saving_throw_bool.set(
            d.get("on_hit_force_save", d.get("on_hit_force_saving_throw_bool", False))
        )
        self.on_hit_save_dc.set(d.get("on_hit_save_dc", 13))
        self.on_hit_save_type.set(d.get("on_hit_save_type", "STR"))

    def to_data(self) -> MonsterData:
        if self._attack_specs:
            self._attack_specs[self._current_attack_idx] = self._current_to_dict()
        else:
            self._attack_specs = [self._current_to_dict()]
        return MonsterData(
            name=self.name_str.get(),
            ac=self.ac_int.get(),
            max_hp=self.max_hp_int.get(),
            attack_range_ft=self.attack_range_ft_int.get(),
            ignore_ranged_in_melee=self.ignore_ranged_in_melee_bool.get(),
            highlight_range_ft=self.highlight_range_ft_int.get(),
            attacks=[_dict_to_attack_spec(d) for d in self._attack_specs],
            saving_throws={
                "STR": (self.savingthrow_str_mod_int.get(), self.savingthrow_str_roll_type_str.get()),
                "DEX": (self.savingthrow_dex_mod_int.get(), self.savingthrow_dex_roll_type_str.get()),
                "CON": (self.savingthrow_con_mod_int.get(), self.savingthrow_con_roll_type_str.get()),
                "INT": (self.savingthrow_int_mod_int.get(), self.savingthrow_int_roll_type_str.get()),
                "WIS": (self.savingthrow_wis_mod_int.get(), self.savingthrow_wis_roll_type_str.get()),
                "CHA": (self.savingthrow_cha_mod_int.get(), self.savingthrow_cha_roll_type_str.get()),
            },
            speeds={
                "walk": self.walking_speed_int.get(),
                "fly": self.flying_speed_int.get(),
                "climb": self.climbing_speed_int.get(),
                "burrow": self.burrowing_speed_int.get(),
                "swim": self.swimming_speed_int.get(),
            },
            passive_perception=self.passiveperception_int.get(),
            initiative_mod=self.initiative_mod_int.get(),
            creature_type=self.creature_type_str.get(),
            creature_size=self.creature_size_str.get(),
            senses={
                "darkvision": self.darkvision_int.get(),
                "blindsight": self.blindsight_int.get(),
                "tremorsense": self.tremorsense_int.get(),
                "truesight": self.truesight_int.get(),
            },
            damage_resistances=[dt for dt, var in self.damage_resistances_vars.items() if var.get()],
            damage_immunities=[dt for dt, var in self.damage_immunities_vars.items() if var.get()],
            damage_vulnerabilities=[dt for dt, var in self.damage_vulnerabilities_vars.items() if var.get()],
            condition_immunities={c for c, var in self.condition_immunities_vars.items() if var.get()},
        )

    def from_data(self, d: MonsterData) -> None:
        self.name_str.set(d.name)
        self.ac_int.set(d.ac)
        self.max_hp_int.set(d.max_hp)
        self.attack_range_ft_int.set(d.attack_range_ft)
        self.ignore_ranged_in_melee_bool.set(d.ignore_ranged_in_melee)
        self.highlight_range_ft_int.set(d.highlight_range_ft)
        self.passiveperception_int.set(d.passive_perception)
        self._attack_specs = [_attack_spec_to_dict(atk) for atk in d.attacks] if d.attacks else [self._current_to_dict()]
        self._current_attack_idx = 0
        self._dict_to_current(self._attack_specs[0])
        for stat, (mod, rt) in d.saving_throws.items():
            getattr(self, f"savingthrow_{stat.lower()}_mod_int").set(mod)
            getattr(self, f"savingthrow_{stat.lower()}_roll_type_str").set(rt)
        self.walking_speed_int.set(d.speeds.get("walk", 0))
        self.flying_speed_int.set(d.speeds.get("fly", 0))
        self.climbing_speed_int.set(d.speeds.get("climb", 0))
        self.burrowing_speed_int.set(d.speeds.get("burrow", 0))
        self.swimming_speed_int.set(d.speeds.get("swim", 0))
        self.initiative_mod_int.set(d.initiative_mod)
        self.creature_type_str.set(d.creature_type)
        self.creature_size_str.set(d.creature_size)
        self.darkvision_int.set(d.senses.get("darkvision", 0))
        self.blindsight_int.set(d.senses.get("blindsight", 0))
        self.tremorsense_int.set(d.senses.get("tremorsense", 0))
        self.truesight_int.set(d.senses.get("truesight", 0))
        for dt, var in self.damage_resistances_vars.items():
            var.set(dt in d.damage_resistances)
        for dt, var in self.damage_immunities_vars.items():
            var.set(dt in d.damage_immunities)
        for dt, var in self.damage_vulnerabilities_vars.items():
            var.set(dt in d.damage_vulnerabilities)
        for c, var in self.condition_immunities_vars.items():
            var.set(c in d.condition_immunities)


def ClearMonsterUI(RelPosMonsters) -> None:
    RelPosMonsters.set("y", 80)
    RelPosMonsters.reset("x")
    for widget in GSM.Monsters_widgets_list:
        widget.destroy()
    GSM.Monsters_widgets_list.clear()


def CreateMonsterUI(monster_obj, new_window, RelPosMonsters) -> None:
    # Initialise _attack_specs lazily on first window open.
    if not monster_obj._attack_specs:
        monster_obj._attack_specs = [monster_obj._current_to_dict()]
        monster_obj._current_attack_idx = 0

    # ── Attack details (left column, starts at y=10) ──────────────────────────
    attack_title_label = tk.Label(new_window, text="Attack details:", font=GSM.Title_font)
    attack_title_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))
    # Name
    monster_name_label = tk.Label(new_window, text="Monsters name:", font=GSM.Target_font)
    monster_name_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
    monster_name_entry = tk.Entry(new_window, borderwidth=2, textvariable=monster_obj.name_str, width=18)
    monster_name_entry.place(x=RelPosMonsters.increase("x", 98), y=RelPosMonsters.same("y"))
    # AC
    target_ac_text_label = tk.Label(new_window, text="AC:", font=GSM.Target_font)
    target_ac_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 30))
    target_ac_spinbox = ttk.Spinbox(new_window, width=3, textvariable=monster_obj.ac_int, from_=0, to=30)
    target_ac_spinbox.place(x=RelPosMonsters.increase("x", 29), y=RelPosMonsters.same("y"))
    # Max HP
    monster_maxhp_text_label = tk.Label(new_window, text="Max HP:", font=GSM.Target_font)
    monster_maxhp_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 30))
    monster_maxhp_spinbox = ttk.Spinbox(new_window, width=5, textvariable=monster_obj.max_hp_int, from_=0, to=9999)
    monster_maxhp_spinbox.place(x=RelPosMonsters.increase("x", 55), y=RelPosMonsters.same("y"))
    # Attack range
    monster_range_label = tk.Label(new_window, text="Attack range (ft):", font=GSM.Target_font)
    monster_range_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 30))
    monster_range_spinbox = ttk.Spinbox(
        new_window, width=4, textvariable=monster_obj.attack_range_ft_int, from_=5, to=600, increment=5
    )
    monster_range_spinbox.place(x=RelPosMonsters.increase("x", 110), y=RelPosMonsters.same("y"))
    monster_ignore_melee_checkbox = tk.Checkbutton(
        new_window, text="Ignore ranged-in-melee penalty",
        variable=monster_obj.ignore_ranged_in_melee_bool, onvalue=True, offvalue=False,
    )
    monster_ignore_melee_checkbox.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 26))
    # Board highlight range
    monster_hl_range_label = tk.Label(new_window, text="Board highlight (ft):", font=GSM.Target_font)
    monster_hl_range_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 26))
    monster_hl_range_spinbox = ttk.Spinbox(
        new_window, width=4, textvariable=monster_obj.highlight_range_ft_int, from_=5, to=600, increment=5
    )
    monster_hl_range_spinbox.place(x=RelPosMonsters.increase("x", 115), y=RelPosMonsters.same("y"))

    # Number of attacks
    monster_n_attacks_text_label = tk.Label(new_window, text="Number of attacks: ")
    monster_n_attacks_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
    monster_n_attacks_dropdown = tk.OptionMenu(new_window, monster_obj.n_attacks, *[1, 2, 3, 4])
    monster_n_attacks_dropdown.place(x=RelPosMonsters.increase("x", 110), y=RelPosMonsters.increase("y", -4))

    # To hit
    monster_to_hit_label = tk.Label(new_window, text="Monster to hit: +", font=GSM.Target_font)
    monster_to_hit_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
    monster_to_hit_spinbox = ttk.Spinbox(new_window, width=3, textvariable=monster_obj.to_hit_mod, from_=0, to=13)
    monster_to_hit_spinbox.place(x=RelPosMonsters.increase("x", 95), y=RelPosMonsters.same("y"))

    # Roll type (normal, adv, disadv...)
    monster_roll_type_text_label = tk.Label(new_window, text="Roll type: ")
    monster_roll_type_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 30))
    monster_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.roll_type, *GSM.Roll_types)
    monster_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 70), y=RelPosMonsters.increase("y", -4))

    "Dmg 1"
    monster_dmg1_text_label = tk.Label(new_window, text="Damage type 1:", font=GSM.Target_font)
    monster_dmg1_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
    monster_dmg1_number_dice_spinbox = ttk.Spinbox(
        new_window, textvariable=monster_obj.dmg_n_die_1, width=3, from_=0, to=10
    )
    monster_dmg1_number_dice_spinbox.place(x=RelPosMonsters.increase("x", 95), y=RelPosMonsters.same("y"))
    monster_dmg1_dice_type_dropdown = tk.OptionMenu(new_window, monster_obj.dmg_die_type_1, *GSM.Dice_types)
    monster_dmg1_dice_type_dropdown.place(x=RelPosMonsters.increase("x", 35), y=RelPosMonsters.increase("y", -5))

    def UpdateMonsterDmg1FlatText(selected_dmg_type) -> None:
        if monster_obj._monster_dmg1_extra_text_label2 is None:
            monster_obj._monster_dmg1_extra_text_label2 = tk.Label(new_window, text=monster_obj.dmg_type_1.get())
            current_box_xy = monster_dmg1_flat_text_label.place_info()
            current_box_x = int(current_box_xy["x"])
            current_box_y = int(current_box_xy["y"])
            monster_obj._monster_dmg1_extra_text_label2.place(x=current_box_x + 130, y=current_box_y)
        else:
            monster_obj._monster_dmg1_extra_text_label2.config(text=monster_obj.dmg_type_1.get())

    monster_dmg1_dmg_type_dropdown = tk.OptionMenu(
        new_window, monster_obj.dmg_type_1, *GSM.Dmg_types, command=UpdateMonsterDmg1FlatText
    )
    monster_dmg1_dmg_type_dropdown.place(x=RelPosMonsters.increase("x", 60), y=RelPosMonsters.same("y"))

    monster_dmg1_flat_text_label = tk.Label(new_window, text="Damage 1 flat: +", font=GSM.Target_font)
    monster_dmg1_flat_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 30))
    monster_dmg1_extra_spinbox = ttk.Spinbox(new_window, textvariable=monster_obj.dmg_flat_1, width=3, from_=-5, to=30)
    monster_dmg1_extra_spinbox.place(x=RelPosMonsters.increase("x", 95), y=RelPosMonsters.same("y"))

    "Dmg 2"
    monster_dmg2_text_label = tk.Label(new_window, text="Damage type 2:")
    monster_dmg2_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 40))
    monster_dmg2_n_dice_spinbox = ttk.Spinbox(new_window, textvariable=monster_obj.dmg_n_die_2, width=3, from_=0, to=10)
    monster_dmg2_n_dice_spinbox.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))
    monster_dmg2_dice_type_dropdown = tk.OptionMenu(new_window, monster_obj.dmg_die_type_2, *GSM.Dice_types)
    monster_dmg2_dice_type_dropdown.place(x=RelPosMonsters.increase("x", 35), y=RelPosMonsters.increase("y", -5))

    def UpdateMonsterDmg2FlatText(selected_dmg_type) -> None:
        if monster_obj._monster_dmg2_extra_text_label2 is None:
            monster_obj._monster_dmg2_extra_text_label2 = tk.Label(new_window, text=monster_obj.dmg_type_2.get())
            current_box_xy = monster_dmg2_flat_text_label.place_info()
            current_box_x = int(current_box_xy["x"])
            current_box_y = int(current_box_xy["y"])
            monster_obj._monster_dmg2_extra_text_label2.place(x=current_box_x + 130, y=current_box_y)
        else:
            monster_obj._monster_dmg2_extra_text_label2.config(text=monster_obj.dmg_type_2.get())

    monster_dmg2_dmg_type_dropdown = tk.OptionMenu(
        new_window, monster_obj.dmg_type_2, *GSM.Dmg_types, command=UpdateMonsterDmg2FlatText
    )
    monster_dmg2_dmg_type_dropdown.place(x=RelPosMonsters.increase("x", 60), y=RelPosMonsters.same("y"))

    monster_dmg2_flat_text_label = tk.Label(new_window, text="Damage 2 flat:  +")
    monster_dmg2_flat_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 30))
    monster_dmg2_extra_spinbox = ttk.Spinbox(new_window, textvariable=monster_obj.dmg_flat_2, width=3, from_=-5, to=30)
    monster_dmg2_extra_spinbox.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))

    # Force saving throw on hit:
    def EnableDisableForceSaveWidget():

        if monster_obj.on_hit_force_saving_throw_bool.get():
            monster_save_throw_dc_label.config(state="normal")
            monster_save_throw_dc_spinbox.config(state="normal")
            monster_save_throw_type_dropdown.config(state="normal")
        else:
            monster_save_throw_dc_label.config(state="disabled")
            monster_save_throw_dc_spinbox.config(state="disabled")
            monster_save_throw_type_dropdown.config(state="disabled")

    monster_force_save_throw_checkbox = tk.Checkbutton(
        new_window,
        text="On hit, force saving throw",
        variable=monster_obj.on_hit_force_saving_throw_bool,
        onvalue=True,
        offvalue=False,
        command=EnableDisableForceSaveWidget,
    )
    monster_force_save_throw_checkbox.place(
        x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y + 10)
    )

    monster_save_throw_dc_label = tk.Label(new_window, text="DC: ")
    monster_save_throw_dc_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 25))
    monster_save_throw_dc_spinbox = ttk.Spinbox(
        new_window, from_=5, to=32, textvariable=monster_obj.on_hit_save_dc, width=3
    )
    monster_save_throw_dc_spinbox.place(x=RelPosMonsters.increase("x", 35), y=RelPosMonsters.same("y"))
    monster_save_throw_dc_spinbox.unbind("<MouseWheel>")  # Disables mouse scroll on Windows/Mac OS
    monster_save_throw_type_dropdown = tk.OptionMenu(new_window, monster_obj.on_hit_save_type, *GSM.Saving_throw_types)
    monster_save_throw_type_dropdown.place(x=RelPosMonsters.increase("x", 32), y=RelPosMonsters.increase("y", -5))
    EnableDisableForceSaveWidget()

    # Halfling luck (reroll ones)
    monster_halfling_luck_checkbox = tk.Checkbutton(
        new_window,
        text="Halfling luck (reroll nat 1)",
        variable=monster_obj.reroll_1_on_hit,
        onvalue=True,
        offvalue=False,
    )
    monster_halfling_luck_checkbox.place(
        x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y + 8)
    )
    # Reroll 1 and 2 dmg die
    monster_reroll_1_2_dmg_checkbox = tk.Checkbutton(
        new_window,
        text="GWM (reroll 1 & 2 dmg dice)",
        variable=monster_obj.reroll_1_2_dmg,
        onvalue=True,
        offvalue=False,
    )
    monster_reroll_1_2_dmg_checkbox.place(
        x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y)
    )
    # Brutal critical
    monster_brutal_crit_checkbox = tk.Checkbutton(
        new_window,
        text="Brutal critical (add 1 extra dmg dice on crit)",
        variable=monster_obj.brutal_critical,
        onvalue=True,
        offvalue=False,
    )
    monster_brutal_crit_checkbox.place(
        x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y)
    )
    # Savage attacker
    monster_savage_attacker_checkbox = tk.Checkbutton(
        new_window,
        text="Savage attacker (Roll dmg dice twice and use higher)",
        variable=monster_obj.savage_attacker,
        onvalue=True,
        offvalue=False,
    )
    monster_savage_attacker_checkbox.place(
        x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y)
    )
    # Crit number
    monster_crit_number_text_label = tk.Label(new_window, text="Champion - crit on:")
    monster_crit_number_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 25))
    monster_crit_number_dropdown = tk.OptionMenu(new_window, monster_obj.crit_number, *[20, 19, 18, 17, 16])
    monster_crit_number_dropdown.place(x=RelPosMonsters.increase("x", 110), y=RelPosMonsters.increase("y", -4))

    # Bane
    monster_bane_checkbox = tk.Checkbutton(
        new_window, text="Bane (-1d4 to hit)", variable=monster_obj.bane, onvalue=True, offvalue=False
    )
    monster_bane_checkbox.place(
        x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y + 8)
    )
    # Bless
    monster_bless_checkbox = tk.Checkbutton(
        new_window, text="Bless (+1d4 to hit)", variable=monster_obj.bless, onvalue=True, offvalue=False
    )
    monster_bless_checkbox.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))

    # Capture the bottom of left column BEFORE saving throws resets y
    _content_end_y = RelPosMonsters.same("y")

    # ── Saving throws (right column, resets y to 10) ──────────────────────────
    RelPosMonsters.checkpoint_set("x", 330)
    info_title_label = tk.Label(new_window, text="Saving throws:", font=GSM.Title_font)
    info_title_label.place(x=RelPosMonsters.checkpoint_get("x"), y=RelPosMonsters.reset("y"))

    def SavingThrows() -> None:
        nonlocal new_window, RelPosMonsters
        spinbox_x_distance = 35
        # STR
        monster_str_save_text_label = tk.Label(new_window, text="STR:")
        monster_str_save_text_label.place(
            x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30)
        )
        monster_str_save_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=monster_obj.savingthrow_str_mod_int, from_=-10, to=20
        )
        monster_str_save_spinbox.place(
            x=RelPosMonsters.increase("x", spinbox_x_distance), y=RelPosMonsters.increase("y", 2)
        )
        monster_str_save_roll_type_dropdown = tk.OptionMenu(
            new_window, monster_obj.savingthrow_str_roll_type_str, *GSM.Roll_types
        )
        monster_str_save_roll_type_dropdown.place(
            x=RelPosMonsters.increase("x", 40), y=RelPosMonsters.increase("y", -5)
        )
        # DEX
        monster_dex_save_text_label = tk.Label(new_window, text="DEX:")
        monster_dex_save_text_label.place(
            x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30)
        )
        monster_dex_save_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=monster_obj.savingthrow_dex_mod_int, from_=-10, to=20
        )
        monster_dex_save_spinbox.place(
            x=RelPosMonsters.increase("x", spinbox_x_distance), y=RelPosMonsters.increase("y", 2)
        )
        monster_dex_save_roll_type_dropdown = tk.OptionMenu(
            new_window, monster_obj.savingthrow_dex_roll_type_str, *GSM.Roll_types
        )
        monster_dex_save_roll_type_dropdown.place(
            x=RelPosMonsters.increase("x", 40), y=RelPosMonsters.increase("y", -5)
        )
        # CON
        monster_con_save_text_label = tk.Label(new_window, text="CON:")
        monster_con_save_text_label.place(
            x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30)
        )
        monster_con_save_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=monster_obj.savingthrow_con_mod_int, from_=-10, to=20
        )
        monster_con_save_spinbox.place(
            x=RelPosMonsters.increase("x", spinbox_x_distance), y=RelPosMonsters.increase("y", 2)
        )
        monster_con_save_roll_type_dropdown = tk.OptionMenu(
            new_window, monster_obj.savingthrow_con_roll_type_str, *GSM.Roll_types
        )
        monster_con_save_roll_type_dropdown.place(
            x=RelPosMonsters.increase("x", 40), y=RelPosMonsters.increase("y", -5)
        )
        # INT
        monster_int_save_text_label = tk.Label(new_window, text="INT:")
        monster_int_save_text_label.place(
            x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30)
        )
        monster_int_save_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=monster_obj.savingthrow_int_mod_int, from_=-10, to=20
        )
        monster_int_save_spinbox.place(
            x=RelPosMonsters.increase("x", spinbox_x_distance), y=RelPosMonsters.increase("y", 2)
        )
        monster_int_save_roll_type_dropdown = tk.OptionMenu(
            new_window, monster_obj.savingthrow_int_roll_type_str, *GSM.Roll_types
        )
        monster_int_save_roll_type_dropdown.place(
            x=RelPosMonsters.increase("x", 40), y=RelPosMonsters.increase("y", -5)
        )
        # WIS
        monster_wis_save_text_label = tk.Label(new_window, text="WIS:")
        monster_wis_save_text_label.place(
            x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30)
        )
        monster_wis_save_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=monster_obj.savingthrow_wis_mod_int, from_=-10, to=20
        )
        monster_wis_save_spinbox.place(
            x=RelPosMonsters.increase("x", spinbox_x_distance), y=RelPosMonsters.increase("y", 2)
        )
        monster_wis_save_roll_type_dropdown = tk.OptionMenu(
            new_window, monster_obj.savingthrow_wis_roll_type_str, *GSM.Roll_types
        )
        monster_wis_save_roll_type_dropdown.place(
            x=RelPosMonsters.increase("x", 40), y=RelPosMonsters.increase("y", -5)
        )
        # CHA
        monster_cha_save_text_label = tk.Label(new_window, text="CHA:")
        monster_cha_save_text_label.place(
            x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30)
        )
        monster_cha_save_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=monster_obj.savingthrow_cha_mod_int, from_=-10, to=20
        )
        monster_cha_save_spinbox.place(
            x=RelPosMonsters.increase("x", spinbox_x_distance), y=RelPosMonsters.increase("y", 2)
        )
        monster_cha_save_roll_type_dropdown = tk.OptionMenu(
            new_window, monster_obj.savingthrow_cha_roll_type_str, *GSM.Roll_types
        )
        monster_cha_save_roll_type_dropdown.place(
            x=RelPosMonsters.increase("x", 40), y=RelPosMonsters.increase("y", -5)
        )

    SavingThrows()

    tk.Label(new_window, text="Initiative mod:", font=GSM.Target_font).place(x=330, y=220)
    ttk.Spinbox(new_window, width=3, textvariable=monster_obj.initiative_mod_int, from_=-10, to=20).place(x=428, y=220)

    # ── Creature Info (third column, x=660) ───────────────────────────────────
    _C3 = 660  # third column x anchor

    tk.Label(new_window, text="Creature Info:", font=GSM.Title_font).place(x=_C3, y=10)

    tk.Label(new_window, text="Type:", font=GSM.Target_font).place(x=_C3, y=38)
    tk.OptionMenu(new_window, monster_obj.creature_type_str, *_CREATURE_TYPES).place(x=_C3 + 40, y=34)

    tk.Label(new_window, text="Size:", font=GSM.Target_font).place(x=_C3, y=68)
    tk.OptionMenu(new_window, monster_obj.creature_size_str, *_CREATURE_SIZES).place(x=_C3 + 40, y=64)

    tk.Label(new_window, text="Speeds (ft):", font=GSM.Title_font).place(x=_C3, y=100)
    for _i, (_lbl, _var) in enumerate([
        ("Walk:", monster_obj.walking_speed_int),
        ("Fly:", monster_obj.flying_speed_int),
        ("Climb:", monster_obj.climbing_speed_int),
        ("Burrow:", monster_obj.burrowing_speed_int),
        ("Swim:", monster_obj.swimming_speed_int),
    ]):
        _y = 125 + _i * 25
        tk.Label(new_window, text=_lbl).place(x=_C3, y=_y)
        ttk.Spinbox(new_window, width=4, textvariable=_var, from_=0, to=120, increment=5).place(x=_C3 + 48, y=_y)

    tk.Label(new_window, text="Senses (ft):", font=GSM.Title_font).place(x=_C3, y=260)
    for _i, (_lbl, _var) in enumerate([
        ("Darkvision:", monster_obj.darkvision_int),
        ("Blindsight:", monster_obj.blindsight_int),
        ("Tremorsense:", monster_obj.tremorsense_int),
        ("Truesight:", monster_obj.truesight_int),
    ]):
        _y = 285 + _i * 25
        tk.Label(new_window, text=_lbl).place(x=_C3, y=_y)
        ttk.Spinbox(new_window, width=4, textvariable=_var, from_=0, to=300, increment=10).place(x=_C3 + 82, y=_y)

    tk.Label(new_window, text="Passive perception:", font=GSM.Target_font).place(x=_C3, y=398)
    ttk.Spinbox(new_window, width=3, textvariable=monster_obj.passiveperception_int, from_=0, to=30).place(
        x=_C3 + 118, y=398
    )

    def _open_dmg_popup(title: str, vars_dict: dict) -> None:
        popup = tk.Toplevel(new_window)
        popup.title(title)
        popup.geometry("320x420")
        popup.grab_set()
        tk.Label(popup, text=title, font=GSM.Title_font).place(x=10, y=10)
        dmg_keys = list(vars_dict.keys())
        for _i, _dt in enumerate(dmg_keys):
            _col, _row = divmod(_i, 9)
            tk.Checkbutton(popup, text=_dt, variable=vars_dict[_dt],
                           onvalue=True, offvalue=False).place(x=10 + _col * 155, y=38 + _row * 22)
        tk.Button(popup, text="Close", command=popup.destroy).place(x=130, y=385)

    def _open_cond_popup() -> None:
        popup = tk.Toplevel(new_window)
        popup.title("Condition Immunities")
        popup.geometry("330x260")
        popup.grab_set()
        tk.Label(popup, text="Condition Immunities", font=GSM.Title_font).place(x=10, y=10)
        cond_keys = list(monster_obj.condition_immunities_vars.keys())
        for _i, _c in enumerate(cond_keys):
            _col, _row = divmod(_i, 7)
            tk.Checkbutton(popup, text=_c, variable=monster_obj.condition_immunities_vars[_c],
                           onvalue=True, offvalue=False).place(x=10 + _col * 155, y=38 + _row * 22)
        tk.Button(popup, text="Close", command=popup.destroy).place(x=130, y=225)

    tk.Button(
        new_window, text="Damage Resistances...",
        command=lambda: _open_dmg_popup("Damage Resistances", monster_obj.damage_resistances_vars),
    ).place(x=_C3, y=428)
    tk.Button(
        new_window, text="Damage Immunities...",
        command=lambda: _open_dmg_popup("Damage Immunities", monster_obj.damage_immunities_vars),
    ).place(x=_C3, y=460)
    tk.Button(
        new_window, text="Damage Vulnerabilities...",
        command=lambda: _open_dmg_popup("Damage Vulnerabilities", monster_obj.damage_vulnerabilities_vars),
    ).place(x=_C3, y=492)
    tk.Button(
        new_window, text="Condition Immunities...",
        command=_open_cond_popup,
    ).place(x=_C3, y=524)

    _import_btn = tk.Button(
        new_window, text="Import 5etools JSON...",
        command=lambda: _open_import_popup(),
        background="#3366aa", fg="white",
    )
    _import_btn.place(x=_C3, y=557)

    # ── Close button (top-right) ──────────────────────────────────────────────
    # _on_close defined after attack panel so it can reference _trace_id
    close_button_placeholder_y = RelPosMonsters.reset("y")  # = 10

    # ── Attack sequence panel (below all content) ─────────────────────────────
    _atk_panel_y = _content_end_y + 22

    atk_panel_label = tk.Label(new_window, text="Attack sequence:", font=GSM.Title_font)
    atk_panel_label.place(x=10, y=_atk_panel_y)

    atk_listbox = tk.Listbox(new_window, height=3, width=18, selectmode="single", exportselection=False)
    atk_listbox.place(x=10, y=_atk_panel_y + 22)

    def _refresh_listbox():
        if not atk_listbox.winfo_exists():
            return
        atk_listbox.delete(0, "end")
        for spec in monster_obj._attack_specs:
            atk_listbox.insert("end", spec.get("name", "Attack"))
        atk_listbox.selection_clear(0, "end")
        atk_listbox.selection_set(monster_obj._current_attack_idx)
        atk_listbox.see(monster_obj._current_attack_idx)

    def _on_select(event):
        sel = atk_listbox.curselection()
        if not sel:
            return
        new_idx = sel[0]
        if new_idx == monster_obj._current_attack_idx:
            return
        monster_obj._attack_specs[monster_obj._current_attack_idx] = monster_obj._current_to_dict()
        monster_obj._current_attack_idx = new_idx
        monster_obj._dict_to_current(monster_obj._attack_specs[new_idx])

    atk_listbox.bind("<<ListboxSelect>>", _on_select)

    def _add_attack():
        monster_obj._attack_specs[monster_obj._current_attack_idx] = monster_obj._current_to_dict()
        new_spec = dict(monster_obj._attack_specs[monster_obj._current_attack_idx])
        new_spec["name"] = f"Attack {len(monster_obj._attack_specs) + 1}"
        monster_obj._attack_specs.append(new_spec)
        monster_obj._current_attack_idx = len(monster_obj._attack_specs) - 1
        monster_obj._dict_to_current(new_spec)
        _refresh_listbox()

    def _remove_attack():
        if len(monster_obj._attack_specs) <= 1:
            return
        monster_obj._attack_specs.pop(monster_obj._current_attack_idx)
        monster_obj._current_attack_idx = min(
            monster_obj._current_attack_idx, len(monster_obj._attack_specs) - 1
        )
        monster_obj._dict_to_current(monster_obj._attack_specs[monster_obj._current_attack_idx])
        _refresh_listbox()

    add_btn = tk.Button(new_window, text="+ Add", command=_add_attack, padx=2)
    add_btn.place(x=155, y=_atk_panel_y + 22)
    rem_btn = tk.Button(new_window, text="- Remove", command=_remove_attack, padx=2)
    rem_btn.place(x=155, y=_atk_panel_y + 48)

    atk_name_label = tk.Label(new_window, text="Name:")
    atk_name_label.place(x=240, y=_atk_panel_y + 26)
    atk_name_entry = tk.Entry(new_window, textvariable=monster_obj.attack_name_str, width=12)
    atk_name_entry.place(x=282, y=_atk_panel_y + 28)

    def _name_trace(*_):
        if not atk_listbox.winfo_exists():
            return
        monster_obj._attack_specs.__setitem__(
            monster_obj._current_attack_idx,
            {**monster_obj._attack_specs[monster_obj._current_attack_idx], "name": monster_obj.attack_name_str.get()},
        )
        _refresh_listbox()

    _trace_id = monster_obj.attack_name_str.trace_add("write", _name_trace)

    _refresh_listbox()

    # ── 5etools import popup ──────────────────────────────────────────────────
    def _open_import_popup() -> None:
        import json as _json
        from persistence.import_5etools import parse_5etools_monster

        popup = tk.Toplevel(new_window)
        popup.title("Import from 5etools JSON")
        popup.geometry("620x500")
        popup.grab_set()

        tk.Label(popup, text="Paste 5etools monster JSON:", font=GSM.Title_font).pack(
            anchor="w", padx=10, pady=(10, 2)
        )

        frame = tk.Frame(popup)
        frame.pack(fill="both", expand=True, padx=10, pady=4)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        text_box = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, height=20)
        text_box.pack(fill="both", expand=True)
        scrollbar.config(command=text_box.yview)

        status_var = tk.StringVar()
        tk.Label(popup, textvariable=status_var, fg="red", wraplength=580).pack(anchor="w", padx=10)

        def do_import() -> None:
            raw = text_box.get("1.0", "end").strip()
            if not raw:
                status_var.set("Paste JSON first.")
                return
            try:
                data = _json.loads(raw)
            except _json.JSONDecodeError as exc:
                status_var.set(f"JSON parse error: {exc}")
                return
            try:
                monster_data = parse_5etools_monster(data)
                monster_obj.from_data(monster_data)
                _refresh_listbox()
                popup.destroy()
            except Exception as exc:
                status_var.set(f"Import error: {exc}")

        btn_row = tk.Frame(popup)
        btn_row.pack(fill="x", padx=10, pady=6)
        tk.Button(btn_row, text="Import", command=do_import,
                  background="green", fg="white", padx=6).pack(side="left")
        tk.Button(btn_row, text="Cancel", command=popup.destroy, padx=6).pack(side="left", padx=6)

    # ── Close button ──────────────────────────────────────────────────────────
    def _on_close():
        monster_obj._attack_specs[monster_obj._current_attack_idx] = monster_obj._current_to_dict()
        monster_obj.attack_name_str.trace_remove("write", _trace_id)
        new_window.destroy()
        monster_obj._my_button.config(text=monster_obj.name_str.get())

    close_button = tk.Button(new_window, text="Save and exit", command=_on_close, background="red")
    close_button.place(x=RelPosMonsters.set("x", 900), y=close_button_placeholder_y)
    new_window.bind("<Return>", lambda event: close_button.invoke())
    new_window.protocol("WM_DELETE_WINDOW", _on_close)


def CreateMonsterObject(RelPosMonsters) -> None:
    ClearMonsterUI(RelPosMonsters)
    for j, monsterObj in enumerate(GSM.Monster_obj_list):
        if monsterObj.name_str.get():  # string not empty
            pass
        else:
            monsterObj.name_str.set(f"Zombie {j + 1}")

        # Button to open the new window
        monsterObj._my_button = tk.Button(
            GSM.Monsters_frame,
            text=monsterObj.name_str.get(),
            command=lambda m=monsterObj: OpenMonsterWindow(m, RelPosMonsters),
        )
        monsterObj._my_button.place(x=RelPosMonsters.same("x"), y=RelPosMonsters.increase("y", 40))
        GSM.Monsters_widgets_list.append(monsterObj._my_button)


def PreservePreviousMonsters(n_monsters, RelPosMonsters) -> None:
    current_count = len(GSM.Monster_obj_list)
    preserve_data = []

    # Preserve existing data
    for monster_obj in GSM.Monster_obj_list:
        preserve_data.append(monster_obj.name_str.get())
    # Adjust the number of MonsterStats objects
    if n_monsters < current_count:
        GSM.Monster_obj_list = GSM.Monster_obj_list[:n_monsters]
    elif n_monsters > current_count:
        for i in range(current_count, n_monsters):
            monsterObj = MonsterStats()
            GSM.Monster_obj_list.append(monsterObj)

    # Redraw labels and entries
    for i in range(n_monsters):
        # Repopulate entries with preserved data if exists
        if i < len(preserve_data):
            GSM.Monster_obj_list[i].name_str.set(preserve_data[i])
    CreateMonsterObject(RelPosMonsters)


def OpenMonsterWindow(monster_obj, RelPosMonsters) -> None:
    # Create a new Toplevel window
    new_window = tk.Toplevel(GSM.Monsters_frame)
    new_window.title("Monster Details")
    new_window.geometry("1000x840")

    CreateMonsterUI(monster_obj, new_window, RelPosMonsters)


def CreateMonster(RelPosMonsters) -> None:
    "Setup"
    # Monster settings text
    monster_settings_text_label = tk.Label(GSM.Monsters_frame, text="Monster creation", font=GSM.Title_font)
    monster_settings_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))

    # Number of monsters
    n_monsters_label = tk.Label(GSM.Monsters_frame, text="How many monsters:")
    n_monsters_label.place(x=RelPosMonsters.same("x"), y=RelPosMonsters.increase("y", 35))
    n_monsters_dropdown = tk.OptionMenu(
        GSM.Monsters_frame,
        GSM.N_monsters_int,
        *[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        command=lambda value: PreservePreviousMonsters(value, RelPosMonsters),
    )

    n_monsters_dropdown.place(x=RelPosMonsters.increase("x", 120), y=RelPosMonsters.increase("y", -4))

    PreservePreviousMonsters(GSM.N_monsters_int.get(), RelPosMonsters)
