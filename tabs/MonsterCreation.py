import tkinter as tk
from GlobalStateManager import GSM

class MonsterStats():
    def __init__(self):
        self.name_str: str = tk.StringVar()
        self.name_str.set("Fire zombie")
        #to hit modifiers and multiattack
        self.n_attacks: int = tk.IntVar(value=1)
        self.to_hit_mod: int = tk.IntVar(value=5)
        self.roll_type: str = tk.StringVar(value="Normal")  # Normal
        #dmg 1
        self.dmg_type_1: str = tk.StringVar(value="bludgeoning")
        self.dmg_n_die_1: int = tk.IntVar(value=1)
        self.dmg_die_type_1: str = tk.StringVar(value="d6")
        self.dmg_flat_1: int = tk.IntVar(value=3)
        #dmg 2
        self.dmg_type_2: str = tk.StringVar(value="fire")
        self.dmg_die_type_2: str = tk.StringVar(value="d4")
        self.dmg_n_die_2: int = tk.IntVar(value=1)
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

        'Monsters Frame display widgets in row like dmg types'
        self._monster_dmg1_extra_text_label2 = None
        self._monster_dmg2_extra_text_label2 = None


def CreateMonster(RelPosMonsters) -> None:

    def ClearMonsterUI() -> None:
        GSM.Monsters_list.clear()
        for widget in GSM.Monsters_widgets_list:
            widget.destroy()
        GSM.Monsters_widgets_list.clear()

    def CreateMonsterUI(monster1, index) -> None:
        column_offset = 280 * index

        # Name
        monster_name_label = tk.Label(GSM.Monsters_frame, text="Monsters name:")
        monster_name_label.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.set("y", 80))
        monster1.name_str.set(str("Fire zombie " + str(index+1)))
        monster_name_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=monster1.name_str, width=18)
        monster_name_entry.place(x=RelPosMonsters.increase("x", 93) + column_offset, y=RelPosMonsters.same("y"))
        GSM.Monsters_widgets_list.append(monster_name_label)
        GSM.Monsters_widgets_list.append(monster_name_entry)

        # Number of attacks
        monster_n_attacks_text_label = tk.Label(GSM.Monsters_frame, text="Number of attacks: ")
        monster_n_attacks_text_label.place(x=RelPosMonsters.reset("x") + column_offset,
                                           y=RelPosMonsters.increase("y", 35))
        monster_n_attacks_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.n_attacks, *[1, 2, 3, 4])
        monster_n_attacks_dropdown.place(x=RelPosMonsters.increase("x", 110) + column_offset,
                                         y=RelPosMonsters.increase("y", -4))
        GSM.Monsters_widgets_list.append(monster_n_attacks_text_label)
        GSM.Monsters_widgets_list.append(monster_n_attacks_dropdown)

        # To hit
        monster_to_hit_label = tk.Label(GSM.Monsters_frame, text="Monster to hit: +")
        monster_to_hit_label.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.increase("y", 35))
        monster_to_hit_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=monster1.to_hit_mod, width=3)
        monster_to_hit_entry.place(x=RelPosMonsters.increase("x", 93) + column_offset, y=RelPosMonsters.same("y"))
        GSM.Monsters_widgets_list.append(monster_to_hit_label)
        GSM.Monsters_widgets_list.append(monster_to_hit_entry)

        # Roll type (normal, adv, disadv...)
        monster_roll_type_text_label = tk.Label(GSM.Monsters_frame, text="Roll type: ")
        monster_roll_type_text_label.place(x=RelPosMonsters.reset("x") + column_offset,
                                           y=RelPosMonsters.increase("y", 30))
        monster_roll_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.roll_type, *GSM.Roll_types)
        monster_roll_type_dropdown.place(x=RelPosMonsters.increase("x", 70) + column_offset,
                                         y=RelPosMonsters.increase("y", -4))
        GSM.Monsters_widgets_list.append(monster_roll_type_text_label)
        GSM.Monsters_widgets_list.append(monster_roll_type_dropdown)

        'Dmg 1'
        monster_dmg1_text_label = tk.Label(GSM.Monsters_frame, text="Damage type 1:")
        monster_dmg1_text_label.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.increase("y", 35))
        monster_dmg1_number_dice_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=monster1.dmg_n_die_1,
                                                  width=3)
        monster_dmg1_number_dice_entry.place(x=RelPosMonsters.increase("x", 93) + column_offset,
                                             y=RelPosMonsters.same("y"))
        monster_dmg1_dice_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.dmg_die_type_1, *GSM.Dice_types)
        monster_dmg1_dice_type_dropdown.place(x=RelPosMonsters.increase("x", 27) + column_offset,
                                              y=RelPosMonsters.increase("y", -5))
        GSM.Monsters_widgets_list.append(monster_dmg1_text_label)
        GSM.Monsters_widgets_list.append(monster_dmg1_number_dice_entry)
        GSM.Monsters_widgets_list.append(monster_dmg1_dice_type_dropdown)

        def UpdateMonsterDmg1FlatText(selected_dmg_type) -> None:
            if monster1._monster_dmg1_extra_text_label2 is None:
                monster1._monster_dmg1_extra_text_label2 = tk.Label(GSM.Monsters_frame, text=monster1.dmg_type_1.get())
                current_box_xy = monster_dmg1_flat_text_label.place_info()
                current_box_x = int(current_box_xy["x"])
                current_box_y = int(current_box_xy["y"])
                monster1._monster_dmg1_extra_text_label2.place(x=current_box_x + 120, y=current_box_y)
                GSM.Monsters_widgets_list.append(monster1._monster_dmg1_extra_text_label2)
            else:
                monster1._monster_dmg1_extra_text_label2.config(text=monster1.dmg_type_1.get())

        monster_dmg1_dmg_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.dmg_type_1, *GSM.Dmg_types,
                                                       command=UpdateMonsterDmg1FlatText)
        monster_dmg1_dmg_type_dropdown.place(x=RelPosMonsters.increase("x", 60) + column_offset,
                                             y=RelPosMonsters.same("y"))
        GSM.Monsters_widgets_list.append(monster_dmg1_dmg_type_dropdown)

        monster_dmg1_flat_text_label = tk.Label(GSM.Monsters_frame, text="Damage 1 flat:  +")
        monster_dmg1_flat_text_label.place(x=RelPosMonsters.reset("x") + column_offset,
                                           y=RelPosMonsters.increase("y", 30))
        monster_dmg1_extra_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=monster1.dmg_flat_1,
                                            width=3)
        monster_dmg1_extra_entry.place(x=RelPosMonsters.increase("x", 93) + column_offset, y=RelPosMonsters.same("y"))
        GSM.Monsters_widgets_list.append(monster_dmg1_flat_text_label)
        GSM.Monsters_widgets_list.append(monster_dmg1_extra_entry)

        'Dmg 2'
        monster_dmg2_text_label = tk.Label(GSM.Monsters_frame, text="Damage type 2:")
        monster_dmg2_text_label.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.increase("y", 40))
        monster_dmg2_n_dice_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2,
                                             textvariable=monster1.dmg_n_die_2, width=3)
        monster_dmg2_n_dice_entry.place(x=RelPosMonsters.increase("x", 93) + column_offset, y=RelPosMonsters.same("y"))
        monster_dmg2_dice_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.dmg_die_type_2,
                                                        *GSM.Dice_types)
        monster_dmg2_dice_type_dropdown.place(x=RelPosMonsters.increase("x", 27) + column_offset,
                                              y=RelPosMonsters.increase("y", -5))
        GSM.Monsters_widgets_list.append(monster_dmg2_text_label)
        GSM.Monsters_widgets_list.append(monster_dmg2_n_dice_entry)
        GSM.Monsters_widgets_list.append(monster_dmg2_dice_type_dropdown)

        def UpdateMonsterDmg2FlatText(selected_dmg_type) -> None:
            if monster1._monster_dmg2_extra_text_label2 is None:
                monster1._monster_dmg2_extra_text_label2 = tk.Label(GSM.Monsters_frame, text=monster1.dmg_type_2.get())
                current_box_xy = monster_dmg2_flat_text_label.place_info()
                current_box_x = int(current_box_xy["x"])
                current_box_y = int(current_box_xy["y"])
                monster1._monster_dmg2_extra_text_label2.place(x=current_box_x + 120, y=current_box_y)
                GSM.Monsters_widgets_list.append(monster1._monster_dmg2_extra_text_label2)
            else:
                monster1._monster_dmg2_extra_text_label2.config(text=monster1.dmg_type_2.get())

        monster_dmg2_dmg_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.dmg_type_2, *GSM.Dmg_types,
                                                       command=UpdateMonsterDmg2FlatText)
        monster_dmg2_dmg_type_dropdown.place(x=RelPosMonsters.increase("x", 60) + column_offset,
                                             y=RelPosMonsters.same("y"))
        GSM.Monsters_widgets_list.append(monster_dmg2_dmg_type_dropdown)

        monster_dmg2_flat_text_label = tk.Label(GSM.Monsters_frame, text="Damage 2 flat:  +")
        monster_dmg2_flat_text_label.place(x=RelPosMonsters.reset("x") + column_offset,
                                           y=RelPosMonsters.increase("y", 30))
        monster_dmg2_extra_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=monster1.dmg_flat_2,
                                            width=3)
        monster_dmg2_extra_entry.place(x=RelPosMonsters.increase("x", 93) + column_offset, y=RelPosMonsters.same("y"))
        GSM.Monsters_widgets_list.append(monster_dmg2_flat_text_label)
        GSM.Monsters_widgets_list.append(monster_dmg2_extra_entry)

        # Force saving throw on hit:
        monster_save_throw_dc_label = tk.Label(GSM.Monsters_frame, text="DC: ")
        monster_save_throw_dc_label.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.increase("y", 35))
        monster_save_throw_dc_label.config(state="disabled")
        monster_save_throw_dc_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2,
                                             textvariable=monster1.on_hit_save_dc, width=3)
        monster_save_throw_dc_entry.place(x=RelPosMonsters.increase("x", 35) + column_offset, y=RelPosMonsters.same("y"))
        monster_save_throw_dc_entry.config(state="disabled")
        monster_save_throw_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.on_hit_save_type,
                                                        *GSM.Saving_throw_types)
        monster_save_throw_type_dropdown.place(x=RelPosMonsters.increase("x", 27) + column_offset,
                                              y=RelPosMonsters.increase("y", -5))
        monster_save_throw_type_dropdown.config(state="disabled")
        def EnableDisableForceSaveWidget():
            if monster1.on_hit_force_saving_throw_bool.get():
                monster_save_throw_dc_label.config(state="normal")
                monster_save_throw_dc_entry.config(state="normal")
                monster_save_throw_type_dropdown.config(state="normal")
            else:
                monster_save_throw_dc_label.config(state="disabled")
                monster_save_throw_dc_entry.config(state="disabled")
                monster_save_throw_type_dropdown.config(state="disabled")

        monster_force_save_throw_checkbox = tk.Checkbutton(GSM.Monsters_frame, text='On hit, force saving throw',
                                         variable=monster1.on_hit_force_saving_throw_bool, onvalue=True, offvalue=False, command=EnableDisableForceSaveWidget)
        monster_force_save_throw_checkbox.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.increase("y", RelPosMonsters.constant_y+10))
        GSM.Monsters_widgets_list.append(monster_force_save_throw_checkbox)
        GSM.Monsters_widgets_list.append(monster_save_throw_dc_label)
        GSM.Monsters_widgets_list.append(monster_save_throw_dc_entry)
        GSM.Monsters_widgets_list.append(monster_save_throw_type_dropdown)

        # Halfling luck (reroll ones)
        monster_halfling_luck_checkbox = tk.Checkbutton(GSM.Monsters_frame, text='Halfling luck (reroll nat 1)',
                                                           variable=monster1.reroll_1_on_hit,
                                                           onvalue=True, offvalue=False)
        monster_halfling_luck_checkbox.place(x=RelPosMonsters.reset("x") + column_offset,
                                                y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        GSM.Monsters_widgets_list.append(monster_halfling_luck_checkbox)
        # Reroll 1 and 2 dmg die
        monster_reroll_1_2_dmg_checkbox = tk.Checkbutton(GSM.Monsters_frame, text='GWM (reroll 1 & 2 dmg dice)',
                                                        variable=monster1.reroll_1_2_dmg,
                                                        onvalue=True, offvalue=False)
        monster_reroll_1_2_dmg_checkbox.place(x=RelPosMonsters.reset("x") + column_offset,
                                             y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        GSM.Monsters_widgets_list.append(monster_reroll_1_2_dmg_checkbox)
        # Brutal critical
        monster_brutal_crit_checkbox = tk.Checkbutton(GSM.Monsters_frame, text='Brutal critical (add 1 extra dmg dice on crit)',
                                                         variable=monster1.brutal_critical,
                                                         onvalue=True, offvalue=False)
        monster_brutal_crit_checkbox.place(x=RelPosMonsters.reset("x") + column_offset,
                                              y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        GSM.Monsters_widgets_list.append(monster_brutal_crit_checkbox)
        # Savage attacker
        monster_savage_attacker_checkbox = tk.Checkbutton(GSM.Monsters_frame,
                                                      text='Savage attacker (Roll dmg dice twice and use higher)',
                                                      variable=monster1.savage_attacker,
                                                      onvalue=True, offvalue=False)
        monster_savage_attacker_checkbox.place(x=RelPosMonsters.reset("x") + column_offset,
                                           y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        GSM.Monsters_widgets_list.append(monster_savage_attacker_checkbox)
        # Crit number
        monster_crit_number_text_label = tk.Label(GSM.Monsters_frame, text="Champion - crit on:")
        monster_crit_number_text_label.place(x=RelPosMonsters.reset("x") + column_offset, y=RelPosMonsters.increase("y", 25))
        monster_crit_number_dropdown = tk.OptionMenu(GSM.Monsters_frame, monster1.crit_number, *[20, 19, 18, 17, 16])
        monster_crit_number_dropdown.place(x=RelPosMonsters.increase("x", 110) + column_offset,
                                             y=RelPosMonsters.increase("y", -4))
        GSM.Monsters_widgets_list.append(monster_crit_number_text_label)
        GSM.Monsters_widgets_list.append(monster_crit_number_dropdown)

    def CreateMonsterObject(n_monsters) -> None:
        #I have no idea why it automatically passes n_monsters in but no harm
        ClearMonsterUI()
        for i in range(GSM.N_monsters_int.get()):
            monster1 = MonsterStats()
            GSM.Monsters_list.append(monster1)
            CreateMonsterUI(monster1, i)

    def OpenMonsterWindow():
        # Create a new Toplevel window
        new_window = tk.Toplevel(GSM.Monsters_frame)
        new_window.title("Monster Details")
        new_window.geometry("400x300")  # Set the size of the new window

        # Add content to the new window
        tk.Label(new_window, text="Monster Details").pack(pady=10)
        tk.Label(new_window, text="Name: Dragon").pack()
        tk.Label(new_window, text="HP: 200").pack()
        tk.Label(new_window, text="Attack: 50").pack()

        # Add a button to close the new window
        tk.Button(new_window, text="Close", command=new_window.destroy).pack(pady=20)

    'Setup'
    # Monster settings text
    monster_settings_text_label = tk.Label(GSM.Monsters_frame, text="Monster settings", font=GSM.Title_font)
    monster_settings_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))

    #Number of monsters
    n_monsters_label = tk.Label(GSM.Monsters_frame, text="How many monsters:")
    n_monsters_label.place(x=RelPosMonsters.same("x"), y=RelPosMonsters.increase("y", 35))
    n_monsters_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.N_monsters_int, *[1, 2, 3], command=CreateMonsterObject)
    n_monsters_dropdown.place(x=RelPosMonsters.increase("x", 120), y=RelPosMonsters.increase("y", -4))

    # Button to open the new window
    create_monster_button = tk.Button(GSM.Monsters_frame, text="Create monster", command=OpenMonsterWindow)
    create_monster_button.place(x=RelPosMonsters.increase("x", 120), y=RelPosMonsters.increase("y", -4))
