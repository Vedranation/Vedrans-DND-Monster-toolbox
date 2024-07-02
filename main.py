import tkinter as tk
from tkinter import font as tkfont  # Import tkfont for font definitions
from tkinter import ttk
import pyperclip
import random
import GlobalStateManager


#label - just text to display
#entry - type in something
#dropdown - pick one from a menu
#space - just a placeholder to move down by X amount
#n = number of something

class Row_track():
    def __init__(self):
        self.row = 0
    def same(self):
        return self.row
    def increase(self):
        self.row += 1
        return self.row
    def reset(self):
        self.row = 0
        return self.row
Row = Row_track()

class RelativePositionTracker():
    def __init__(self):
        self.x = 5
        self.y = 10
        self.constant_y = 20
    def same(self, what: str):
        if what == "x":
            return self.x
        elif what == "y":
            return self.y
    def increase(self, what: str, how_much: int):
        if what == "x":
            self.x += how_much
            return self.x
        elif what == "y":
            self.y += how_much
            return self.y
    def reset(self, what: str):
        if what == "x":
            self.x = 5
            return self.x
        elif what == "y":
            self.y = 10
            return self.y

    def set(self, what: str, to_what: int):
        if what == "x":
            self.x = to_what
            return self.x
        elif what == "y":
            self.y = to_what
            return self.y
RelPosSettings = RelativePositionTracker()
RelPosMonsters = RelativePositionTracker()
RelPosTargets = RelativePositionTracker()
RelPosMassroll = RelativePositionTracker()
RelPosRandGen = RelativePositionTracker()
RelPosROLL = RelativePositionTracker()

class PlayerStats():
    def __init__(self):
        #TODO: Make a setting to pick between PP and rolling percep for mass percep check
        self.name_str: str = tk.StringVar()
        self.ac_int = tk.IntVar(value=13)
        #TODO: Make multiple monsters
        self.n_monsters_1_int = tk.IntVar(value=1)
        self.n_monsters_2_int = tk.IntVar(value=0)
        self.n_monsters_3_int = tk.IntVar(value=0)
        self.monster_roll_type_against_str = tk.StringVar(value="Normal") #If dodging or is flanked

        self.pp: int = 10 #passive perception
        self.percep_mod: int = 2 #for regular trap spotting
        self.arcana_mod: int = 0 #for wards/magic trap spotting
        self.insight_mod: int = 0 #Insight checks
        self.adamantine: int = False #turn crits into normal attacks

class MonsterStats():
    def __init__(self):
        self.name_str: str = tk.StringVar()
        self.name_str.set("Fire zombie")
        #to hit modifiers and multiattack
        self.n_attacks: int = tk.IntVar()
        self.n_attacks.set(1)
        self.to_hit_mod: int = tk.IntVar()
        self.to_hit_mod.set(5)
        self.roll_type: str = tk.StringVar()  # Normal
        self.roll_type.set("Normal")
        #dmg 1
        self.dmg_type_1: str = tk.StringVar(value="bludgeoning")
        self.dmg_n_die_1: int = tk.IntVar(value=1)
        self.dmg_die_type_1: str = tk.StringVar(value="d6")
        self.dmg_flat_1: int = tk.IntVar(value=3)
        #dmg 2
        self.dmg_type_2: str = tk.StringVar()
        self.dmg_type_2.set("fire")
        self.dmg_die_type_2: str = tk.StringVar()
        self.dmg_die_type_2.set("d4")
        self.dmg_n_die_2: int = tk.IntVar()
        self.dmg_n_die_2.set(1)
        self.dmg_flat_2: int = tk.IntVar()
        self.dmg_flat_2.set(0)
        #force saving throw on hit
        self.on_hit_force_saving_throw_bool: bool = tk.BooleanVar(value=False) #False
        self.on_hit_save_dc: int = tk.IntVar(value=13)
        self.on_hit_save_type: str = tk.StringVar(value="STR")
        #extra abilities
        self.reroll_1_on_hit: bool = tk.BooleanVar() #once rerolls a 1 TO HIT (halfing luck)
        self.reroll_1_2_dmg: bool = tk.BooleanVar() #GW fighting style - reroll 1 or 2 on DMG once
        self.brutal_critical: bool = tk.BooleanVar() #On crit, rolls an extra dmg die
        self.crit_number: int = tk.IntVar() #Usually 20, in case you want crit on 19 or 18
        self.savage_attacker: bool = tk.BooleanVar() #Once per turn, roll dmg twice and use higher number

        # TODO: Add spellcasters
        self.is_spell_caster: bool = tk.BooleanVar() #Usually no
        self.lv_1_spell_slots: int = tk.IntVar()
        self.lv_2_spell_slots: int = tk.IntVar()
        self.lv_3_spell_slots: int = tk.IntVar()
        self.lv_4_spell_slots: int = tk.IntVar()
        self.lv_5_spell_slots: int = tk.IntVar()
        self.lv_6_spell_slots: int = tk.IntVar()
        self.lv_7_spell_slots: int = tk.IntVar()
        self.lv_8_spell_slots: int = tk.IntVar()
        self.lv_9_spell_slots: int = tk.IntVar()

        'Monsters Frame display widgets in row like dmg types'
        self._monster_dmg1_extra_text_label2 = None
        self._monster_dmg2_extra_text_label2 = None
GSM = GlobalStateManager.GlobalsManager()

def Settings() -> None:

    #Main settings text
    main_settings_text_label = tk.Label(GSM.Settings_frame, text="Main settings", font=GSM.Title_font)
    main_settings_text_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.same("y"))

    #Meets it beats it checkbox
    checkbox_label = tk.Checkbutton(GSM.Settings_frame, text='Attack roll equal to AC hits',variable=GSM.Meets_it_beats_it_bool, onvalue=True, offvalue=False)
    checkbox_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    #Crits double dice checkbox
    checkbox_label2 = tk.Checkbutton(GSM.Settings_frame, text='Crits double dmg instead of dice',variable=GSM.Crits_double_dmg_bool, onvalue=True, offvalue=False)
    GSM.Crits_double_dmg_bool.set(True)
    checkbox_label2.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    #Crit always hits
    checkbox_label3 = tk.Checkbutton(GSM.Settings_frame, text='NAT 20 always hits',variable=GSM.Crits_always_hit_bool, onvalue=True, offvalue=False)
    GSM.Crits_always_hit_bool.set(True)
    checkbox_label3.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    #Nat1 always miss
    checkbox_label3 = tk.Checkbutton(GSM.Settings_frame, text='NAT 1 always miss',variable=GSM.Nat1_always_miss_bool, onvalue=True, offvalue=False)
    GSM.Nat1_always_miss_bool.set(True)
    checkbox_label3.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

Settings()

def Targets() -> None:
    # Target settings text
    Target_settings_text_label = tk.Label(GSM.Targets_frame, text="Target settings", font=GSM.Title_font)
    Target_settings_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))

    #Number of targets
    n_targets_text_label = tk.Label(GSM.Targets_frame, text="How many targets: ")
    n_targets_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.increase("y", 35))
    GSM.N_targets_int.set(4)

    # Button to update targets
    GSM.Target_related_widgets = []

    def CreateTargetsButton() -> None:
        for widget in GSM.Target_related_widgets:
            widget.destroy()
        GSM.Target_related_widgets.clear()
        current_create_targets_button_xy = GSM.Create_targets_button.place_info()
        current_create_targets_button_x = int(current_create_targets_button_xy["x"])
        current_create_targets_button_y = int(current_create_targets_button_xy["y"])
        RelPosTargets.set("x", current_create_targets_button_x)
        RelPosTargets.set("y", current_create_targets_button_y+20)

        for i, TargetObj in enumerate(GSM.Target_obj_list):

            if TargetObj.name_str.get():  # string not empty
                pass
            else:
                TargetObj.name_str.set(f"Target {i + 1}")
            RelPosTargets.set("x", current_create_targets_button_x)
            RelPosTargets.increase("y", 25)
            #Display name
            target_text_label = tk.Label(GSM.Targets_frame, text=f"{TargetObj.name_str.get()}:")
            target_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.same("y"))
            #AC
            target_ac_text_label = tk.Label(GSM.Targets_frame, text="AC:")
            target_ac_text_label.place(x=RelPosTargets.increase("x", 85), y=RelPosTargets.same("y"))
            target_ac_entry = tk.Entry(GSM.Targets_frame, borderwidth=2, textvariable=TargetObj.ac_int, width=2)
            target_ac_entry.place(x=RelPosTargets.increase("x", 28), y=RelPosTargets.same("y"))
            #N monsters (1-3)
            for i, monster in enumerate(GSM.Monsters_list):
                column_index = i * 120
                target_n_monsters_text_label = tk.Label(GSM.Targets_frame, text=f"{monster.name_str.get()}:")
                target_n_monsters_text_label.place(x=RelPosTargets.set("x", 70 + column_index), y=RelPosTargets.same("y"))
                print(monster.name_str.get())
                if i == 0:
                    target_n_monster_entry = tk.Entry(GSM.Targets_frame, borderwidth=2, textvariable=TargetObj.n_monsters_1_int,
                                                  width=2)
                elif i == 1:
                    target_n_monster_entry = tk.Entry(GSM.Targets_frame, borderwidth=2,
                                                      textvariable=TargetObj.n_monsters_2_int, width=2)
                else:
                    target_n_monster_entry = tk.Entry(GSM.Targets_frame, borderwidth=2,
                                                      textvariable=TargetObj.n_monsters_3_int, width=2)
                target_n_monster_entry.place(x=RelPosTargets.increase("x", 90), y=RelPosTargets.same("y"))

                for widget in (target_ac_entry, target_n_monster_entry, target_text_label, target_ac_text_label,
                               target_n_monsters_text_label):
                    GSM.Target_related_widgets.append(
                        widget)  # packs all Target Settings widgets (input and display) into one list so it can be cleared from window

    def DrawTargetInputNameBoxes(n_targets) -> None:
        current_count = len(GSM.Target_obj_list)
        preserve_data = []

        # Preserve existing data
        for target_obj in GSM.Target_obj_list:
            preserve_data.append(target_obj.name_str.get())

        # Adjust the number of PlayerStats objects
        if n_targets < current_count:
            for i in range(current_count - n_targets):
                _target_name_labels_list.pop().destroy()
                _target_name_entry_list.pop().destroy()
            GSM.Target_obj_list = GSM.Target_obj_list[:n_targets]
        elif n_targets > current_count:
            for i in range(current_count, n_targets):
                TargetObj = PlayerStats()
                GSM.Target_obj_list.append(TargetObj)

        # Redraw labels and entries
        for i in range(n_targets):
            local_x = RelPosTargets.set("x", 200) if i > 5 else RelPosTargets.reset("x")
            local_y = _first_target_row_y + RelPosTargets.constant_y * (i - 6 if i > 5 else i)

            if i >= current_count:
                # Create new label and entry if new target
                _target_name_label = tk.Label(GSM.Targets_frame, text=f"Target {i + 1} name:")
                _target_name_label.place(x=local_x, y=local_y)
                _target_name_labels_list.append(_target_name_label)

                _target_name_entry = tk.Entry(GSM.Targets_frame, textvariable=GSM.Target_obj_list[i].name_str, width=13)
                _target_name_entry.place(x=local_x + 95, y=local_y)
                _target_name_entry_list.append(_target_name_entry)
            else:
                # Move existing label and entry
                _target_name_labels_list[i].place(x=local_x, y=local_y)
                _target_name_entry_list[i].place(x=local_x + 95, y=local_y)

            # Repopulate entries with preserved data if exists
            if i < len(preserve_data):
                GSM.Target_obj_list[i].name_str.set(preserve_data[i])

        # Adjust button position
        if GSM.Create_targets_button is None:
            GSM.Create_targets_button = tk.Button(GSM.Targets_frame, text="Create targets", command=CreateTargetsButton,
                                              padx=6, pady=5)
        last_y = _first_target_row_y + RelPosTargets.constant_y * (n_targets - 1 if n_targets <= 6 else 5)
        GSM.Create_targets_button.place(x=RelPosTargets.reset("x"), y=RelPosTargets.set("y", last_y + 30))

    n_targets_dropdown = tk.OptionMenu(GSM.Targets_frame, GSM.N_targets_int, *[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                       command=DrawTargetInputNameBoxes)
    n_targets_dropdown.place(x=RelPosTargets.set("x", 115), y=RelPosTargets.increase("y", -4))

    _target_name_labels_list = []
    _target_name_entry_list = []
    RelPosTargets.constant_y = 24
    _first_target_row_y = RelPosTargets.increase("y", 40)
    DrawTargetInputNameBoxes(GSM.N_targets_int.get())




Targets()
monster1 = MonsterStats()

def CreateMonster() -> None:

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




        # Nat1 always miss
        monster_force_save_throw_checkbox = tk.Checkbutton(GSM.Monsters_frame, text='On hit, force save: ',
                                                           variable=monster1.on_hit_force_saving_throw_bool,
                                                           onvalue=True, offvalue=False)
        monster_force_save_throw_checkbox.place(x=RelPosMonsters.reset("x") + column_offset,
                                                y=RelPosMonsters.increase("y", RelPosMonsters.constant_y))
        GSM.Monsters_widgets_list.append(monster_force_save_throw_checkbox)

    def CreateMonsterObject(n_monsters) -> None:
        #I have no idea why it automatically passes n_monsters in but no harm
        ClearMonsterUI()
        for i in range(GSM.N_monsters_int.get()):
            monster1 = MonsterStats()
            GSM.Monsters_list.append(monster1)
            CreateMonsterUI(monster1, i)

    'Setup'
    # Monster settings text
    monster_settings_text_label = tk.Label(GSM.Monsters_frame, text="Monster settings", font=GSM.Title_font)
    monster_settings_text_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))

    #Number of monsters
    n_monsters_label = tk.Label(GSM.Monsters_frame, text="How many monsters:")
    n_monsters_label.place(x=RelPosMonsters.same("x"), y=RelPosMonsters.increase("y", 35))
    n_monsters_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.N_monsters_int, *[1, 2, 3], command=CreateMonsterObject)
    n_monsters_dropdown.place(x=RelPosMonsters.increase("x", 120), y=RelPosMonsters.increase("y", -4))


CreateMonster()

def MassSavingThrow() -> None:
    RelPosMassroll.constant_y = 25

    mass_savingthrow_label = tk.Label(GSM.Mass_roll_frame, text="Mass saving throw", font=GSM.Title_font)
    mass_savingthrow_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))
    #Saving throw modifier
    mass_save_mod_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw mod:  +")
    mass_save_mod_text_label.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 35))

    GSM.Mass_save_mod_int.set(2)
    mass_save_mod_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_mod_int, width=3)
    mass_save_mod_entry.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.increase("y", 2))
    #Save DC
    mass_save_DC_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw DC: ")
    mass_save_DC_text_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

    GSM.Mass_save_DC_int.set(13)
    mass_save_DC_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_DC_int, width=3)
    mass_save_DC_entry.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.same("y"))
    #How many monsters
    mass_save_n_monsters_text_label = tk.Label(GSM.Mass_roll_frame, text="How many monsters: ")
    mass_save_n_monsters_text_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

    GSM.Mass_save_n_monsters_int.set(6)
    mass_save_n_monsters_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_n_monsters_int, width=3)
    mass_save_n_monsters_entry.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.same("y"))

    def RollType() -> None:
        # Roll type (adv/dis/normal)
        roll_type_text_label = tk.Label(GSM.Mass_roll_frame, text="Roll type:")
        roll_type_text_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

        GSM.Mass_save_roll_type_str.set(GSM.Roll_types[0])
        Roll_type_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Mass_save_roll_type_str, *GSM.Roll_types)
        Roll_type_dropdown.place(x=RelPosMassroll.increase("x", 65), y=RelPosMassroll.increase("y", -4))

    RollType()

    def RollMassSaveButton():
        for widget in GSM.Results_random_gen_widgets_to_clear:
            widget.destroy()
        GSM.Results_random_gen_widgets_to_clear.clear()
        passes = 0
        rolls = []
        rolltype = GSM.Mass_save_roll_type_str.get()
        for i in range(GSM.Mass_save_n_monsters_int.get()):
            if rolltype == "Normal":  # "Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"
                roll = RollDice("d20")
            elif rolltype == "Advantage":
                roll = max(RollDice("d20"), RollDice("d20"))
            elif rolltype == "Disadvantage":
                roll = min(RollDice("d20"), RollDice("d20"))
            elif rolltype == "Super Advantage":
                roll = max(RollDice("d20"), RollDice("d20"), RollDice("d20"))
            elif rolltype == "Super Disadvantage":
                roll = min(RollDice("d20"), RollDice("d20"), RollDice("d20"))
            roll_total = roll + GSM.Mass_save_mod_int.get()
            if roll == 1 and GSM.Nat1_always_miss_bool.get():
                pass #nat 1 always fails with rule
            elif (roll_total) >= (GSM.Mass_save_DC_int.get()):
                passes += 1
            rolls.append(roll_total)

        rolls.sort(reverse=True)
        nonlocal mass_save_button
        current_button_xy = mass_save_button.place_info()
        current_button_x = int(current_button_xy["x"])
        current_button_y = int(current_button_xy["y"])

        mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(
            f"Out of {GSM.Mass_save_n_monsters_int.get()} monsters, {passes} passed and {GSM.Mass_save_n_monsters_int.get() - passes} failed"))
        mass_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.set("y", current_button_y+30))
        GSM.Results_random_gen_widgets_to_clear.append(mass_save_results_label)

        mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(f"Rolled with {rolltype} for: {rolls}"))
        mass_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))
        GSM.Results_random_gen_widgets_to_clear.append(mass_save_results_label)

    mass_save_button = tk.Button(GSM.Mass_roll_frame, text="Roll save", state="normal", command=RollMassSaveButton,
                          padx=9, background="grey")
    mass_save_button.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))


MassSavingThrow()
def RollDice(die_type: str) -> int:
    if die_type == "d4":
        die_max = 4
    elif die_type == "d6":
        die_max = 6
    elif die_type == "d8":
        die_max = 8
    elif die_type == "d10":
        die_max = 10
    elif die_type == "d12":
        die_max = 12
    elif die_type == "d20":
        die_max = 20
    elif die_type == "d100":
        die_max = 100
    return random.randint(1, die_max)

def RandomGenerator():
    fumble_table = ["Get distracted: Disadvantage on next attack", "Overextended Swing: Next attack on you have advantage", "Hit yourself for half dmg",
                    "Hit ally for half dmg", "String Snap: If using a bow or crossbow", "Fall prone", "Ranged attack/spell: Goes in completely random direction and hits something",
                    "Drop your weapon", "Misjudged Distance: enemy within 5ft can attempt a free grapple check", "Twisted Ankle: half move speed next turn",
                    "Overexertion: Lose bonus action this turn", "Self doubt: Lose reaction this turn", "Ice spells: Your feet freeze, is rooted until next turn",
                    "Fire spells: Lit yourself on fire, 2 turns take 1d6 dmg or action to put it out", "Ranged weapons: Drop 10 pieces of ammunition, it scatters and needs action to collect",
                    "A random glass item/potion breaks and spills", "Coin pouch rips, you lose 5d8 GP", "If spell: Roll wild magic table", "Loud noise: You cause a very loud noise",
                    "Panic: Become frightened of whatever you just attacked", "Sand/Mud in eyes: Become blinded until your next turn", "Drop formation: Lose 2 AC until next turn",
                    "Instinct movement: You provoke instincts in enemy, they move 10ft immediately", "Nothing happens, lucky day", "You got distracted by a coin on the ground! Add 1GP to your inventory"]
    random_gen_result_label = None
    RelPosRandGen.constant_y = 40
    def RollFumbleButton():
        nonlocal random_gen_result_label
        if random_gen_result_label is not None:
            random_gen_result_label.destroy()

        random_gen_result_label = tk.Label(GSM.Random_generator_frame, text=(f"{random.choice(fumble_table)}"))
        random_gen_result_label.place(x=RelPosRandGen.reset("x"), y=RelPosRandGen.set("y", 120))

    # Random generator title
    random_generator_text_label = tk.Label(GSM.Random_generator_frame, text="Random Generator", font=GSM.Title_font)
    random_generator_text_label.place(x=RelPosRandGen.reset("x"), y=RelPosRandGen.reset("y"))

    roll_fumble_button = tk.Button(GSM.Random_generator_frame, text="Roll fumble", state="normal", command=RollFumbleButton,
                                               padx=9, background="grey")
    RelPosRandGen.reset("x")
    roll_fumble_button.place(x=RelPosRandGen.increase("x", 10), y=RelPosRandGen.increase("y", RelPosRandGen.constant_y))

RandomGenerator()

def ROLL() -> None:
    #TODO: Add a "Copy results to clipboard" button!
    n_dice1 = GSM.Monster_dmg1_n_dice_int.get()
    dice_type1 = GSM.Monster_dmg1_dice_type_str.get()
    flat_dmg1 = GSM.Monster_dmg1_flat_int.get()
    dmg_type1 = GSM.Monster_dmg1_dmg_type_str.get()
    n_dice2 = GSM.Monster_dmg2_n_dice_int.get()
    dice_type2 = GSM.Monster_dmg2_dice_type_str.get()
    dmg_type2 = GSM.Monster_dmg2_dmg_type_str.get()
    rolltype = "Normal" #GSM.Roll_type_str.get()
    print("----")
    RelPosROLL.reset("x")
    RelPosROLL.set("y", 60)
    for widget in GSM.Results_display_widgets_list:
        widget.destroy()
    GSM.Results_display_widgets_list.clear()
    def display(hits, dmgs1, dmgs2, target_name) -> None:

        def custom_sort(item):
            if isinstance(item, str):
                return (0, item)  # Put strings first
            else:
                return (1, -item)  # Sort integers in reverse order

        sorted_hits = sorted(hits, key=custom_sort)
        print(sorted_hits)
        targetDmgLabel = tk.Label(GSM.ROLL_frame, text=(f"{target_name}"))
        targetDmgLabel.place(x=RelPosROLL.set("x", 10), y=RelPosROLL.increase("y", RelPosROLL.constant_y*1.3))
        GSM.Results_display_widgets_list.append(targetDmgLabel)

        filtered_length = (lambda hits: len([hit for hit in hits if hit != "nat1"]))(sorted_hits)
        targetDmgLabel = tk.Label(GSM.ROLL_frame, text=(f"|  {filtered_length}  |   {sorted_hits}"))
        targetDmgLabel.place(x=RelPosROLL.increase("x", 60), y=RelPosROLL.same("y"))
        GSM.Results_display_widgets_list.append(targetDmgLabel)

        targetDmgLabel = tk.Label(GSM.ROLL_frame, text=(f"|   {sum(dmgs1)} {dmg_type1}   |   {sum(dmgs2)} {dmg_type2}"))
        targetDmgLabel.place(x=RelPosROLL.increase("x", 60), y=RelPosROLL.same("y"))
        GSM.Results_display_widgets_list.append(targetDmgLabel)


    def damage(crit=False) -> (int, int):
        if not crit:
            dmg1 = flat_dmg1
            for dice in range(n_dice1):
                dmg1 = dmg1 + RollDice(dice_type1)
            dmg2 = 0
            for dice in range(n_dice2):
                dmg2 = dmg2 + RollDice(dice_type2)
        else:
            if GSM.Crits_double_dmg_bool.get():
                dmg1 = flat_dmg1
                for dice in range(n_dice1):
                    dmg1 = dmg1 + RollDice(dice_type1)
                dmg1 = dmg1*2
                dmg2 = 0
                for dice in range(n_dice2):
                    dmg2 = dmg2 + RollDice(dice_type2)
                dmg2 = dmg2*2
            else:
                dmg1 = flat_dmg1
                for dice in range(n_dice1*2):
                    dmg1 = dmg1 + RollDice(dice_type1)
                dmg2 = 0
                for dice in range(n_dice2*2):
                    dmg2 = dmg2 + RollDice(dice_type2)
        return dmg1, dmg2

    for i, TargetObj in enumerate(GSM.Target_obj_list):

        ac = int(TargetObj.ac_int.get())
        n_monsters = int(TargetObj.n_monsters_int.get())

        hits = []
        dmgs1 = []
        dmgs2 = []
        for monster in range(n_monsters):
            for attack in range(GSM.Monster_n_attacks_int.get()):
                tohit = int(GSM.Monster_to_hit_int.get())
                roll = int(0)

                if rolltype == "Normal": #"Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"
                    roll = RollDice("d20")
                elif rolltype == "Advantage":
                    roll = max(RollDice("d20"), RollDice("d20"))
                elif rolltype == "Disadvantage":
                    roll = min(RollDice("d20"), RollDice("d20"))
                elif rolltype == "Super Advantage":
                    roll = max(RollDice("d20"), RollDice("d20"), RollDice("d20"))
                elif rolltype == "Super Disadvantage":
                    roll = min(RollDice("d20"), RollDice("d20"), RollDice("d20"))

                if roll == 20 and GSM.Crits_always_hit_bool.get():
                    dmg1, dmg2 = damage(crit=True)
                    hits.append("nat20")
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)
                elif roll == 1 and GSM.Nat1_always_miss_bool.get():
                    hits.append("nat1")

                elif (GSM.Meets_it_beats_it_bool.get()):
                    if roll + tohit >= ac:
                        dmg1, dmg2 = damage(crit=False)
                        hits.append(roll+tohit)
                        dmgs1.append(dmg1)
                        dmgs2.append(dmg2)
                else:
                    if roll + tohit > ac:
                        print(roll, tohit, ac)
                        dmg1, dmg2 = damage(crit=False)
                        hits.append(roll+tohit)
                        dmgs1.append(dmg1)
                        dmgs2.append(dmg2)

        print(f"Hits: {hits}, {dmgs1} {dmg_type1}, {dmgs2} {dmg_type2}")
        display(hits, dmgs1, dmgs2, TargetObj.name_str.get())
        print(f"Total: {sum(dmgs1)} {dmg_type1}, {sum(dmgs2)} {dmg_type2}")


#ROLL button
random_generator_text_label = tk.Label(GSM.ROLL_frame, text="Roll attacks", font=GSM.Title_font)
random_generator_text_label.place(x=RelPosROLL.reset("x"), y=RelPosROLL.reset("y"))

ROLL_button = tk.Button(GSM.ROLL_frame, text="ROLL", state="normal", command=ROLL, font=GSM.Title_font,
                                           padx=9, background="red")
ROLL_button.place(x=RelPosROLL.increase("x", 10), y=RelPosROLL.increase("y", RelPosROLL.constant_y*1.5))



#TODO: Add a boss section, which tracks boss cooldowns, legendary actions etc
#TODO: Add automated rolling for random encounter table. Let players import a list, saying chance of each encounter,
#   which happen per night and which per day, how often to check, and how long PC's travelled and then determine the outcome
#TODO: Add a random store. Decide "quality" of store (distribution of item rarity), how many items, read an external list, and price range as inputs
#TODO: Add random loot

GSM.Root.mainloop()