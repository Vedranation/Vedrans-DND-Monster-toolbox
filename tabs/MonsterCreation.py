import tkinter as tk
from tkinter import StringVar, ttk

from GlobalStateManager import GSM

class MonsterStats():
    def __init__(self, index):
        self.name_str: str = tk.StringVar()
        self.name_str.set("Zombie " + str(index+1))
        #to hit modifiers and multiattack
        self.n_attacks: int = tk.IntVar(value=1)
        self.to_hit_mod: int = tk.IntVar(value=5)
        self.roll_type: str = tk.StringVar(value="Normal")  # Normal
        self.ac_int = tk.IntVar(value=13)
        #dmg 1
        self.dmg_type_1: str = tk.StringVar(value="bludgeoning")
        self.dmg_n_die_1: int = tk.IntVar(value=1)
        self.dmg_die_type_1: str = tk.StringVar(value="d6")
        self.dmg_flat_1: int = tk.IntVar(value=3)
        #dmg 2
        self.dmg_type_2: str = tk.StringVar(value="fire")
        self.dmg_die_type_2: str = tk.StringVar(value="d4")
        self.dmg_n_die_2: int = tk.IntVar(value=0)
        self.dmg_flat_2: int = tk.IntVar(value=0)
        #force saving throw on hit
        self.on_hit_force_saving_throw_bool: bool = tk.BooleanVar(value=False) #False
        self.on_hit_save_dc: int = tk.IntVar(value=13)
        self.on_hit_save_type: str = tk.StringVar(value="STR")
        #extra abilities
        self.reroll_1_on_hit: bool = tk.BooleanVar(value=False) #once rerolls a 1 TO HIT (halfing luck)
        self.reroll_1_2_dmg: bool = tk.BooleanVar(value=False) #GW fighting style - reroll 1 or 2 on DMG once
        self.brutal_critical: bool = tk.BooleanVar(value=False) #On crit, rolls an extra dmg die
        self.crit_number: int = tk.IntVar(value=20) #Usually 20, in case you want crit on 19 or 18
        self.savage_attacker: bool = tk.BooleanVar(value=False) #Once per turn, roll dmg twice and use higher number
        self.bane: bool = tk.BooleanVar(value=False)
        self.bless: bool = tk.BooleanVar(value=False)

        #speed
        self.walking_speed_int: IntVar = tk.IntVar(value=20)
        self.flying_speed_int: IntVar = tk.IntVar(value=0)
        self.climbing_speed_int: IntVar = tk.IntVar(value=0)
        self.burrowing_speed_int: IntVar = tk.IntVar(value=0)

        #saving throws
        self.savingthrow_str_mod_int: IntVar = tk.IntVar(value=1)
        self.savingthrow_str_roll_type_str = tk.StringVar(value="Normal")
        self.savingthrow_dex_mod_int: IntVar = tk.IntVar(value=-2)
        self.savingthrow_dex_roll_type_str: StringVar = tk.StringVar(value="Normal")
        self.savingthrow_con_mod_int: IntVar = tk.IntVar(value=3)
        self.savingthrow_con_roll_type_str: StringVar = tk.StringVar(value="Normal")
        self.savingthrow_int_mod_int: IntVar = tk.IntVar(value=-4)
        self.savingthrow_int_roll_type_str: StringVar = tk.StringVar(value="Normal")
        self.savingthrow_wis_mod_int: IntVar = tk.IntVar(value=-2)
        self.savingthrow_wis_roll_type_str: StringVar = tk.StringVar(value="Normal")
        self.savingthrow_cha_mod_int: IntVar = tk.IntVar(value=-3)
        self.savingthrow_cha_roll_type_str: StringVar = tk.StringVar(value="Normal")
        self.passiveperception_int: IntVar = tk.IntVar(value=8)

        'Monsters Frame display widgets in row like dmg types'
        self._my_button = None #Stores his own button
        self._monster_dmg1_extra_text_label2 = None
        self._monster_dmg2_extra_text_label2 = None
    def __str__(self):
        return self.name_str.get()

#TODO: Add ability to make complex attacks, like 2x claw and 1x bite

def CreateMonster(RelPosMonsters) -> None:

    def ClearMonsterUI() -> None:
        RelPosMonsters.set("y", 80)
        RelPosMonsters.reset("x")
        GSM.Monsters_list.clear()
        for widget in GSM.Monsters_widgets_list:
            widget.destroy()
        GSM.Monsters_widgets_list.clear()

    def CreateMonsterUI(monster_obj, new_window) -> None:
        attack_title_label = tk.Label(new_window, text="Attack details:", font=GSM.Title_font)
        attack_title_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))
        # Name
        monster_name_label = tk.Label(new_window, text="Monsters name:")
        monster_name_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
        monster_name_entry = tk.Entry(new_window, borderwidth=2, textvariable=monster_obj.name_str, width=18)
        monster_name_entry.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))

        # Number of attacks
        monster_n_attacks_text_label = tk.Label(new_window, text="Number of attacks: ")
        monster_n_attacks_text_label.place(x=RelPosMonsters.reset("x"),
                                           y=RelPosMonsters.increase("y", 35))
        monster_n_attacks_dropdown = tk.OptionMenu(new_window, monster_obj.n_attacks, *[1, 2, 3, 4])
        monster_n_attacks_dropdown.place(x=RelPosMonsters.increase("x", 110),
                                         y=RelPosMonsters.increase("y", -4))

        # To hit
        monster_to_hit_label = tk.Label(new_window, text="Monster to hit: +")
        monster_to_hit_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
        monster_to_hit_entry = tk.Entry(new_window, borderwidth=2, textvariable=monster_obj.to_hit_mod, width=3)
        monster_to_hit_entry.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))

        # Roll type (normal, adv, disadv...)
        monster_roll_type_text_label = tk.Label(new_window, text="Roll type: ")
        monster_roll_type_text_label.place(x=RelPosMonsters.reset("x"),
                                           y=RelPosMonsters.increase("y", 30))
        monster_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.roll_type, *GSM.Roll_types)
        monster_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 70),
                                         y=RelPosMonsters.increase("y", -4))

        'Dmg 1'
        monster_dmg1_text_label = tk.Label(new_window, text="Damage type 1:")
        monster_dmg1_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 35))
        monster_dmg1_number_dice_entry = tk.Entry(new_window, borderwidth=2, textvariable=monster_obj.dmg_n_die_1,
                                                  width=3)
        monster_dmg1_number_dice_entry.place(x=RelPosMonsters.increase("x", 93),
                                             y=RelPosMonsters.same("y"))
        monster_dmg1_dice_type_dropdown = tk.OptionMenu(new_window, monster_obj.dmg_die_type_1, *GSM.Dice_types)
        monster_dmg1_dice_type_dropdown.place(x=RelPosMonsters.increase("x", 27),
                                              y=RelPosMonsters.increase("y", -5))

        def UpdateMonsterDmg1FlatText(selected_dmg_type) -> None:
            if monster_obj._monster_dmg1_extra_text_label2 is None:
                monster_obj._monster_dmg1_extra_text_label2 = tk.Label(new_window, text=monster_obj.dmg_type_1.get())
                current_box_xy = monster_dmg1_flat_text_label.place_info()
                current_box_x = int(current_box_xy["x"])
                current_box_y = int(current_box_xy["y"])
                monster_obj._monster_dmg1_extra_text_label2.place(x=current_box_x + 120, y=current_box_y)
            else:
                monster_obj._monster_dmg1_extra_text_label2.config(text=monster_obj.dmg_type_1.get())

        monster_dmg1_dmg_type_dropdown = tk.OptionMenu(new_window, monster_obj.dmg_type_1, *GSM.Dmg_types,
                                                       command=UpdateMonsterDmg1FlatText)
        monster_dmg1_dmg_type_dropdown.place(x=RelPosMonsters.increase("x", 60),
                                             y=RelPosMonsters.same("y"))

        monster_dmg1_flat_text_label = tk.Label(new_window, text="Damage 1 flat:  +")
        monster_dmg1_flat_text_label.place(x=RelPosMonsters.reset("x"),
                                           y=RelPosMonsters.increase("y", 30))
        monster_dmg1_extra_entry = tk.Entry(new_window, borderwidth=2, textvariable=monster_obj.dmg_flat_1,
                                            width=3)
        monster_dmg1_extra_entry.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))

        'Dmg 2'
        monster_dmg2_text_label = tk.Label(new_window, text="Damage type 2:")
        monster_dmg2_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 40))
        monster_dmg2_n_dice_entry = tk.Entry(new_window, borderwidth=2,
                                             textvariable=monster_obj.dmg_n_die_2, width=3)
        monster_dmg2_n_dice_entry.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))
        monster_dmg2_dice_type_dropdown = tk.OptionMenu(new_window, monster_obj.dmg_die_type_2,
                                                        *GSM.Dice_types)
        monster_dmg2_dice_type_dropdown.place(x=RelPosMonsters.increase("x", 27),
                                              y=RelPosMonsters.increase("y", -5))

        def UpdateMonsterDmg2FlatText(selected_dmg_type) -> None:
            if monster_obj._monster_dmg2_extra_text_label2 is None:
                monster_obj._monster_dmg2_extra_text_label2 = tk.Label(new_window, text=monster_obj.dmg_type_2.get())
                current_box_xy = monster_dmg2_flat_text_label.place_info()
                current_box_x = int(current_box_xy["x"])
                current_box_y = int(current_box_xy["y"])
                monster_obj._monster_dmg2_extra_text_label2.place(x=current_box_x + 120, y=current_box_y)
            else:
                monster_obj._monster_dmg2_extra_text_label2.config(text=monster_obj.dmg_type_2.get())

        monster_dmg2_dmg_type_dropdown = tk.OptionMenu(new_window, monster_obj.dmg_type_2, *GSM.Dmg_types,
                                                       command=UpdateMonsterDmg2FlatText)
        monster_dmg2_dmg_type_dropdown.place(x=RelPosMonsters.increase("x", 60),
                                             y=RelPosMonsters.same("y"))

        monster_dmg2_flat_text_label = tk.Label(new_window, text="Damage 2 flat:  +")
        monster_dmg2_flat_text_label.place(x=RelPosMonsters.reset("x"),
                                           y=RelPosMonsters.increase("y", 30))
        monster_dmg2_extra_entry = tk.Entry(new_window, borderwidth=2, textvariable=monster_obj.dmg_flat_2,
                                            width=3)
        monster_dmg2_extra_entry.place(x=RelPosMonsters.increase("x", 93), y=RelPosMonsters.same("y"))

        # Force saving throw on hit:
        def EnableDisableForceSaveWidget():
            if monster_obj.on_hit_force_saving_throw_bool.get():
                monster_save_throw_dc_label.config(state="normal")
                monster_save_throw_dc_entry.config(state="normal")
                monster_save_throw_type_dropdown.config(state="normal")
            else:
                monster_save_throw_dc_label.config(state="disabled")
                monster_save_throw_dc_entry.config(state="disabled")
                monster_save_throw_type_dropdown.config(state="disabled")

        monster_force_save_throw_checkbox = tk.Checkbutton(new_window, text='On hit, force saving throw',
                                                           variable=monster_obj.on_hit_force_saving_throw_bool, onvalue=True, offvalue=False, command=EnableDisableForceSaveWidget)
        monster_force_save_throw_checkbox.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", RelPosMonsters.constant_y+10))

        monster_save_throw_dc_label = tk.Label(new_window, text="DC: ")
        monster_save_throw_dc_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 25))
        monster_save_throw_dc_label.config(state="disabled")
        monster_save_throw_dc_entry = tk.Entry(new_window, borderwidth=2,
                                               textvariable=monster_obj.on_hit_save_dc, width=3)
        monster_save_throw_dc_entry.place(x=RelPosMonsters.increase("x", 35), y=RelPosMonsters.same("y"))
        monster_save_throw_dc_entry.config(state="disabled")
        monster_save_throw_type_dropdown = tk.OptionMenu(new_window, monster_obj.on_hit_save_type,
                                                         *GSM.Saving_throw_types)
        monster_save_throw_type_dropdown.place(x=RelPosMonsters.increase("x", 27),
                                              y=RelPosMonsters.increase("y", -5))
        monster_save_throw_type_dropdown.config(state="disabled")

        # Halfling luck (reroll ones)
        monster_halfling_luck_checkbox = tk.Checkbutton(new_window, text='Halfling luck (reroll nat 1)',
                                                        variable=monster_obj.reroll_1_on_hit,
                                                        onvalue=True, offvalue=False)
        monster_halfling_luck_checkbox.place(x=RelPosMonsters.reset("x"),
                                                y=RelPosMonsters.increase("y", RelPosMonsters.constant_y + 8))
        # Reroll 1 and 2 dmg die
        monster_reroll_1_2_dmg_checkbox = tk.Checkbutton(new_window, text='GWM (reroll 1 & 2 dmg dice)',
                                                         variable=monster_obj.reroll_1_2_dmg,
                                                         onvalue=True, offvalue=False)
        monster_reroll_1_2_dmg_checkbox.place(x=RelPosMonsters.reset("x"),
                                             y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        # Brutal critical
        monster_brutal_crit_checkbox = tk.Checkbutton(new_window, text='Brutal critical (add 1 extra dmg dice on crit)',
                                                      variable=monster_obj.brutal_critical,
                                                      onvalue=True, offvalue=False)
        monster_brutal_crit_checkbox.place(x=RelPosMonsters.reset("x"),
                                              y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        # Savage attacker
        monster_savage_attacker_checkbox = tk.Checkbutton(new_window,
                                                          text='Savage attacker (Roll dmg dice twice and use higher)',
                                                          variable=monster_obj.savage_attacker,
                                                          onvalue=True, offvalue=False)
        monster_savage_attacker_checkbox.place(x=RelPosMonsters.reset("x"),
                                           y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        # Crit number
        monster_crit_number_text_label = tk.Label(new_window, text="Champion - crit on:")
        monster_crit_number_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.increase("y", 25))
        monster_crit_number_dropdown = tk.OptionMenu(new_window, monster_obj.crit_number, *[20, 19, 18, 17, 16])
        monster_crit_number_dropdown.place(x=RelPosMonsters.increase("x", 110),
                                             y=RelPosMonsters.increase("y", -4))

        # Bane
        monster_bane_checkbox = tk.Checkbutton(new_window, text='Bane (-1d4 to hit)', variable=monster_obj.bane,
                                                          onvalue=True, offvalue=False)
        monster_bane_checkbox.place(x=RelPosMonsters.reset("x"),
                                               y=RelPosMonsters.increase("y", RelPosMonsters.constant_y + 8))
        # Bless
        monster_bless_checkbox = tk.Checkbutton(new_window, text='Bless (+1d4 to hit)', variable=monster_obj.bless,
                                               onvalue=True, offvalue=False)
        monster_bless_checkbox.place(x=RelPosMonsters.reset("x"),
                                    y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))

        #Information for DM (speeds, saving throws, pp etc)
        RelPosMonsters.checkpoint_set("x", 330)
        info_title_label = tk.Label(new_window, text="Saving throws:", font=GSM.Title_font)
        info_title_label.place(x=RelPosMonsters.checkpoint_get("x"), y=RelPosMonsters.reset("y"))
        def SavingThrows() -> None:
            #Just grouped saving throws so they can be compressed
            nonlocal new_window, RelPosMonsters
            spinbox_x_distance = 35
            # STR
            monster_str_save_text_label = tk.Label(new_window, text="STR:")
            monster_str_save_text_label.place(x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")), y=RelPosMonsters.increase("y", 30))
            monster_str_save_spinbox = ttk.Spinbox(new_window, width=3, textvariable=monster_obj.savingthrow_str_mod_int,
                                                    from_=-10, to=20)
            monster_str_save_spinbox.place(x=RelPosMonsters.increase("x", spinbox_x_distance),
                                            y=RelPosMonsters.increase("y", 2))
            monster_str_save_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.savingthrow_str_roll_type_str,
                                                                 *GSM.Roll_types)
            monster_str_save_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 40),
                                                       y=RelPosMonsters.increase("y", -5))
            # DEX
            monster_dex_save_text_label = tk.Label(new_window, text="DEX:")
            monster_dex_save_text_label.place(x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")),
                                              y=RelPosMonsters.increase("y", 30))
            monster_dex_save_spinbox = ttk.Spinbox(new_window, width=3,
                                                   textvariable=monster_obj.savingthrow_dex_mod_int,
                                                   from_=-10, to=20)
            monster_dex_save_spinbox.place(x=RelPosMonsters.increase("x", spinbox_x_distance),
                                           y=RelPosMonsters.increase("y", 2))
            monster_dex_save_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.savingthrow_dex_roll_type_str,
                                                                *GSM.Roll_types)
            monster_dex_save_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 40),
                                                      y=RelPosMonsters.increase("y", -5))
            # CON
            monster_con_save_text_label = tk.Label(new_window, text="CON:")
            monster_con_save_text_label.place(x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")),
                                              y=RelPosMonsters.increase("y", 30))
            monster_con_save_spinbox = ttk.Spinbox(new_window, width=3,
                                                   textvariable=monster_obj.savingthrow_con_mod_int,
                                                   from_=-10, to=20)
            monster_con_save_spinbox.place(x=RelPosMonsters.increase("x", spinbox_x_distance),
                                           y=RelPosMonsters.increase("y", 2))
            monster_con_save_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.savingthrow_con_roll_type_str,
                                                                *GSM.Roll_types)
            monster_con_save_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 40),
                                                      y=RelPosMonsters.increase("y", -5))
            # INT
            monster_int_save_text_label = tk.Label(new_window, text="INT:")
            monster_int_save_text_label.place(x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")),
                                              y=RelPosMonsters.increase("y", 30))
            monster_int_save_spinbox = ttk.Spinbox(new_window, width=3,
                                                   textvariable=monster_obj.savingthrow_int_mod_int,
                                                   from_=-10, to=20)
            monster_int_save_spinbox.place(x=RelPosMonsters.increase("x", spinbox_x_distance),
                                           y=RelPosMonsters.increase("y", 2))
            monster_int_save_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.savingthrow_int_roll_type_str,
                                                                *GSM.Roll_types)
            monster_int_save_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 40),
                                                      y=RelPosMonsters.increase("y", -5))
            # WIS
            monster_wis_save_text_label = tk.Label(new_window, text="WIS:")
            monster_wis_save_text_label.place(x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")),
                                              y=RelPosMonsters.increase("y", 30))
            monster_wis_save_spinbox = ttk.Spinbox(new_window, width=3,
                                                   textvariable=monster_obj.savingthrow_wis_mod_int,
                                                   from_=-10, to=20)
            monster_wis_save_spinbox.place(x=RelPosMonsters.increase("x", spinbox_x_distance),
                                           y=RelPosMonsters.increase("y", 2))
            monster_wis_save_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.savingthrow_wis_roll_type_str,
                                                                *GSM.Roll_types)
            monster_wis_save_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 40),
                                                      y=RelPosMonsters.increase("y", -5))
            # CHA
            monster_cha_save_text_label = tk.Label(new_window, text="CHA:")
            monster_cha_save_text_label.place(x=RelPosMonsters.set("x", RelPosMonsters.checkpoint_get("x")),
                                              y=RelPosMonsters.increase("y", 30))
            monster_cha_save_spinbox = ttk.Spinbox(new_window, width=3,
                                                   textvariable=monster_obj.savingthrow_cha_mod_int,
                                                   from_=-10, to=20)
            monster_cha_save_spinbox.place(x=RelPosMonsters.increase("x", spinbox_x_distance),
                                           y=RelPosMonsters.increase("y", 2))
            monster_cha_save_roll_type_dropdown = tk.OptionMenu(new_window, monster_obj.savingthrow_cha_roll_type_str,
                                                                *GSM.Roll_types)
            monster_cha_save_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 40),
                                                      y=RelPosMonsters.increase("y", -5))
        SavingThrows()
        # Add a button to close the new window
        close_button = tk.Button(new_window, text="Save and exit", command=lambda: (new_window.destroy(), monster_obj._my_button.config(text=monster_obj.name_str.get())),
                                 background="red")

        close_button.place(x=RelPosMonsters.set("x", 600), y=RelPosMonsters.reset("y"))
        # Bind the Enter key to the close_button's command
        new_window.bind("<Return>", lambda event: close_button.invoke())

    def CreateMonsterObject(n_monsters) -> None:
        #I have no idea why it automatically passes n_monsters in but no harm
        ClearMonsterUI()
        for i in range(GSM.N_monsters_int.get()):
            monster_obj = MonsterStats(i)
            GSM.Monsters_list.append(monster_obj)

            # Button to open the new window
            monster_obj._my_button = tk.Button(GSM.Monsters_frame, text=monster_obj.name_str.get(), command=lambda m=monster_obj: OpenMonsterWindow(m))
            monster_obj._my_button.place(x=RelPosMonsters.same("x"), y=RelPosMonsters.increase("y", 40))
            GSM.Monsters_widgets_list.append(monster_obj._my_button)



    def OpenMonsterWindow(monster_obj) -> None:
        # Create a new Toplevel window
        new_window = tk.Toplevel(GSM.Monsters_frame)
        new_window.title("Monster Details")
        new_window.geometry("700x600")  # Set the size of the new window

        CreateMonsterUI(monster_obj, new_window)


    'Setup'
    # Monster settings text
    monster_settings_text_label = tk.Label(GSM.Monsters_frame, text="Monster creation", font=GSM.Title_font)
    monster_settings_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))

    #Number of monsters
    n_monsters_label = tk.Label(GSM.Monsters_frame, text="How many monsters:")
    n_monsters_label.place(x=RelPosMonsters.same("x"), y=RelPosMonsters.increase("y", 35))
    n_monsters_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.N_monsters_int, *[1,2,3,4,5,6,7,8,9,10], command=CreateMonsterObject)
    n_monsters_dropdown.place(x=RelPosMonsters.increase("x", 120), y=RelPosMonsters.increase("y", -4))

    CreateMonsterObject(GSM.N_monsters_int.get())
