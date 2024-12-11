import tkinter as tk
from tkinter import ttk

import utilities
from GlobalStateManager import GSM
from utilities import RollDice

def MassRoll(RelPosMassroll, RelPosMonsters) -> None:
    RelPosMassroll.constant_y = 25

    def RollMassSaveButton(current_button_y):
        for widget in GSM.Results_mass_save_widgets_to_clear:
            widget.destroy()
        GSM.Results_mass_save_widgets_to_clear.clear()
        passes = 0
        rolls = []
        rolltype = GSM.Mass_save_roll_type_str.get()
        # FIXME: Move this into utilities one day so its not same code over and over
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

        mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(
            f"PASSES: {passes}     FAILS: {GSM.Mass_save_n_monsters_int.get() - passes}"))
        mass_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.set("y", current_button_y+30))
        GSM.Results_mass_save_widgets_to_clear.append(mass_save_results_label)

        mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(f"Results: {rolls}"))
        mass_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))
        GSM.Results_mass_save_widgets_to_clear.append(mass_save_results_label)
    def UndefinedMassSave():
        mass_savingthrow_label = tk.Label(GSM.Mass_roll_frame, text="Mass undefined\nsaving throw", font=GSM.Title_font)
        mass_savingthrow_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))
        #Saving throw modifier
        mass_save_mod_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw mod:  +")
        mass_save_mod_text_label.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 50))

        GSM.Mass_save_mod_int.set(2)
        mass_save_mod_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, textvariable=GSM.Mass_save_mod_int, width=3, from_=-10, to=20)
        mass_save_mod_spinbox.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.increase("y", 2))

        #Save DC
        mass_save_DC_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw DC: ")
        mass_save_DC_text_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

        GSM.Mass_save_DC_int.set(13)
        mass_save_DC_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, textvariable=GSM.Mass_save_DC_int, width=3, from_=5, to=30)
        mass_save_DC_spinbox.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.same("y"))
        #How many monsters
        mass_save_n_monsters_text_label = tk.Label(GSM.Mass_roll_frame, text="How many creatures: ")
        mass_save_n_monsters_text_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

        GSM.Mass_save_n_monsters_int.set(6)
        mass_save_n_monsters_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, textvariable=GSM.Mass_save_n_monsters_int, width=3,
                                                   from_=1, to=30)
        mass_save_n_monsters_spinbox.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.same("y"))

        # Roll type (adv/dis/normal)
        roll_type_text_label = tk.Label(GSM.Mass_roll_frame, text="Roll type:")
        roll_type_text_label.place(x=RelPosMassroll.reset("x"),
                                   y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

        GSM.Mass_save_roll_type_str.set(GSM.Roll_types[0])
        Roll_type_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Mass_save_roll_type_str, *GSM.Roll_types)
        Roll_type_dropdown.place(x=RelPosMassroll.increase("x", 65), y=RelPosMassroll.increase("y", -4))

        #Button to roll mass save
        mass_save_button = tk.Button(GSM.Mass_roll_frame, text="Roll save", state="normal",
                                     command=lambda: RollMassSaveButton(int(mass_save_button.place_info()["y"])),
                                     padx=9, background="grey")
        mass_save_button.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))

    UndefinedMassSave()

    def RollQuickMobSaveButton(current_button_y: int):
        for widget in GSM.Results_quick_mob_save_widgets_to_clear:
            widget.destroy()
        GSM.Results_quick_mob_save_widgets_to_clear.clear()
        rolls = []
        rolltype = GSM.Quick_monster_save_rolltype_str.get()

        #Get the monster obj from string since Tkinker can only hold strings
        monster_map = {monster.name_str.get(): monster for monster in GSM.Monsters_list}
        monster_obj = monster_map.get(GSM.Quick_save_which_mob_str.get(), None)  # Retrieve attacker object
        which_save = GSM.Quick_save_which_save.get()
        if monster_obj is None:
            raise Exception("No monster selected for quick save throw")

        if rolltype == "Monster default": #Grab roletype from monster statblock, otherwise override with user's choice
            if which_save == "STR":
                rolltype = monster_obj.savingthrow_str_roll_type_str.get()
            elif which_save == "DEX":
                rolltype = monster_obj.savingthrow_dex_roll_type_str.get()
            elif which_save == "CON":
                rolltype = monster_obj.savingthrow_con_roll_type_str.get()
            elif which_save == "INT":
                rolltype = monster_obj.savingthrow_int_roll_type_str.get()
            elif which_save == "WIS":
                rolltype = monster_obj.savingthrow_wis_roll_type_str.get()
            elif which_save == "CHA":
                rolltype = monster_obj.savingthrow_cha_roll_type_str.get()

        if which_save == "STR": #Get appropriate save modifier
            modifier = monster_obj.savingthrow_str_mod_int.get()
        elif which_save == "DEX":
            modifier = monster_obj.savingthrow_dex_mod_int.get()
        elif which_save == "CON":
            modifier = monster_obj.savingthrow_con_mod_int.get()
        elif which_save == "INT":
            modifier = monster_obj.savingthrow_int_mod_int.get()
        elif which_save == "WIS":
            modifier = monster_obj.savingthrow_wis_mod_int.get()
        elif which_save == "CHA":
            modifier = monster_obj.savingthrow_cha_mod_int.get()
        # FIXME: Move this into utilities one day so its not same code over and over
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
        roll_total = roll + modifier
        text_colour = "black"
        if roll == 1 and GSM.Nat1_always_miss_bool.get():
            roll_total = f"nat1 ({roll_total})"
            text_colour = "red"
        elif roll == 20:
            roll_total = f"nat20 ({roll_total})"
            text_colour = "green"

        quick_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(
            f"{monster_obj.name_str.get()} rolled a {roll_total}"), fg=text_colour)
        quick_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.set("y", current_button_y + 30))
        GSM.Results_quick_mob_save_widgets_to_clear.append(quick_save_results_label)


    def QuickMonsterSave():
        quick_monster_save_label = tk.Label(GSM.Mass_roll_frame, text="Quick monster\nsaving throw", font=GSM.Title_font)
        quick_monster_save_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 100))
        #Which monster
        quick_monster_save_label2 = tk.Label(GSM.Mass_roll_frame, text="Which monster: ")
        quick_monster_save_label2.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 45))
        quick_monster_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Quick_save_which_mob_str, *GSM.Monsters_list)
        GSM.Quick_save_which_mob_str.set(GSM.Monsters_list[0])
        quick_monster_dropdown.place(x=RelPosMassroll.increase("x", 90), y=RelPosMassroll.increase("y", -4))
        GSM.OnTab_MassSaves_reset_widgets.append([quick_monster_dropdown, GSM.RelPosMassroll.same("x"),
                                                  GSM.RelPosMassroll.same("y"), "which_monster"])
        #Which save
        quick_monster_save_label3 = tk.Label(GSM.Mass_roll_frame, text="Which save:")
        quick_monster_save_label3.place(x=RelPosMassroll.reset("x"),
                                   y=RelPosMassroll.increase("y", 35))
        select_save_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Quick_save_which_save,
                                              *GSM.Saving_throw_types)
        select_save_dropdown.place(x=RelPosMassroll.increase("x", 80), y=RelPosMassroll.increase("y", -4))

        #Which rolltype (or default)
        quick_monster_rolltype_label = tk.Label(GSM.Mass_roll_frame, text="Roll type:")
        quick_monster_rolltype_label.place(x=RelPosMassroll.reset("x"),
                                   y=RelPosMassroll.increase("y", 35))

        quick_mob_save_rolltype_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Quick_monster_save_rolltype_str,
                                                         *["Monster default", *GSM.Roll_types])
        quick_mob_save_rolltype_dropdown.place(x=RelPosMassroll.increase("x", 70), y=RelPosMassroll.increase("y", -4))
        # Button to roll save
        mob_quick_save_button = tk.Button(GSM.Mass_roll_frame, text="Roll save", state="normal",
                                     command=lambda: RollQuickMobSaveButton(int(mob_quick_save_button.place_info()["y"])),
                                     padx=9, background="grey")
        mob_quick_save_button.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))

    QuickMonsterSave()


    def RollMassSkillButton():
        for widget in GSM.Results_mass_skill_check_widgets_to_clear:
            widget.destroy()
        GSM.Results_mass_skill_check_widgets_to_clear.clear()
        results = []
        counter = 0
        for creature in GSM.Mass_skill_check_stats_list:
            name = creature[0].get()
            mod = creature[1].get()
            rolltype = creature[2].get()
            enabled = creature[3].get()
            passed = "Failed"
            if not enabled: #Creature not enabled to roll
                continue
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
            roll_total = roll + mod
            if roll == 1 and GSM.Nat1_always_miss_bool.get():
                pass  # nat 1 always fails with rule
            elif roll == 20:
                passed = "Nat20"
            elif (roll_total) >= (GSM.Mass_skill_check_dc_int.get()):
                passed = "Passed"
            results.append([name, roll_total, passed])
        for checkbox in GSM.Mass_skill_enable_checkboxes_list:
            if not checkbox.instate(['selected']): #Don't care about empty checkboxes
                continue
            checkbox_y = checkbox.winfo_y()
            mass_skill_result_label = tk.Label(GSM.Mass_roll_frame, text=f"{results[counter][1]},   {results[counter][2]}")
            mass_skill_result_label.place(x=RelPosMassroll.set("x", 470), y=RelPosMassroll.set("y", checkbox_y))
            GSM.Results_mass_skill_check_widgets_to_clear.append(mass_skill_result_label)
            counter += 1

    def UndefinedMassSkillCheck():
        RelPosMassroll.checkpoint_set("x", 240)
        mass_skill_check_label = tk.Label(GSM.Mass_roll_frame, text="Mass undefined skill check", font=GSM.Title_font)
        mass_skill_check_label.place(x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.reset("y"))
        #TODO: Make multiple presets for this

        #HEADERS FOR MASS SKILL CHECK
        #Name ENTRY, modifier SLIDER, rolltype DROPDOWN, enable CHECKBOX
        skill_name_text_label = tk.Label(GSM.Mass_roll_frame, text="Creature", font=GSM.Target_font)
        skill_name_text_label.place(x=RelPosMassroll.increase("x", -10), y=RelPosMassroll.increase("y", 23))

        skill_mod_text_label = tk.Label(GSM.Mass_roll_frame, text="Skill mod", font=GSM.Target_font)
        skill_mod_text_label.place(x=RelPosMassroll.increase("x", 65), y=RelPosMassroll.same("y"))

        skill_rolltype_text_label = tk.Label(GSM.Mass_roll_frame, text="Rolltype", font=GSM.Target_font)
        skill_rolltype_text_label.place(x=RelPosMassroll.increase("x", 65), y=RelPosMassroll.same("y"))

        skill_enable_text_label = tk.Label(GSM.Mass_roll_frame, text="Enable", font=GSM.Target_font)
        skill_enable_text_label.place(x=RelPosMassroll.increase("x", 75), y=RelPosMassroll.same("y"))
        for i in range(10):
            list_of_info = []
            # Name
            mass_skill_name_str = tk.StringVar(value=("Creature " + str(i+1)))
            mass_skill_name_entry = tk.Entry(GSM.Mass_roll_frame, width=10, textvariable=mass_skill_name_str)
            mass_skill_name_entry.place(x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.increase("y", 28))
            list_of_info.append(mass_skill_name_str)
            # Skill modifier
            mass_skill_mod_int = tk.IntVar(value=2)
            mass_skill_mod_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, width=3, textvariable=mass_skill_mod_int, from_=-5, to=20)
            mass_skill_mod_spinbox.place(x=RelPosMassroll.increase("x", 72), y=RelPosMassroll.same("y"))
            list_of_info.append(mass_skill_mod_int)
            # Rolltype
            mass_skill_rolltype_str = tk.StringVar(value=GSM.Roll_types[0])
            mass_skill_rolltype_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, mass_skill_rolltype_str, *GSM.Roll_types)
            mass_skill_rolltype_dropdown.place(x=RelPosMassroll.increase("x", 43), y=RelPosMassroll.increase("y", -4))
            list_of_info.append(mass_skill_rolltype_str)
            #Enable
            def EnableDisableEntry(name_entry, mod_spinbox, rolltype_dropdown, enable_var):
                """Enable or disable entries based on the checkbox state."""
                if enable_var.get():
                    name_entry.config(state="normal")
                    mod_spinbox.config(state="normal")
                    rolltype_dropdown.config(state="normal")
                else:
                    name_entry.config(state="disabled")
                    mod_spinbox.config(state="disabled")
                    rolltype_dropdown.config(state="disabled")

            mass_skill_enable_bool = tk.BooleanVar(value=True) if i < 3 else tk.BooleanVar(value=False)
            mass_skill_enable_checkbox = ttk.Checkbutton(GSM.Mass_roll_frame, variable=mass_skill_enable_bool, onvalue=True,
                offvalue=False, command=lambda entry=mass_skill_name_entry, spinbox=mass_skill_mod_spinbox,
                                               dropdown=mass_skill_rolltype_dropdown,
                                               var=mass_skill_enable_bool: EnableDisableEntry(entry,spinbox,dropdown,var))
            EnableDisableEntry(mass_skill_name_entry, mass_skill_mod_spinbox, mass_skill_rolltype_dropdown, mass_skill_enable_bool)
            mass_skill_enable_checkbox.place(x=RelPosMassroll.increase("x", 100), y=RelPosMassroll.same("y"))
            list_of_info.append(mass_skill_enable_bool)
            GSM.Mass_skill_check_stats_list.append(list_of_info)
            GSM.Mass_skill_enable_checkboxes_list.append(mass_skill_enable_checkbox)    #List of checkboxes so we can get their locations to append results to

        mass_skill_dc_text_label = tk.Label(GSM.Mass_roll_frame, text="Skill check DC:")
        mass_skill_dc_text_label.place(x=RelPosMassroll.increase("x", -230), y=RelPosMassroll.increase("y", 30))
        mass_skill_dc_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, width=3, textvariable=GSM.Mass_skill_check_dc_int, from_=5, to=40)
        mass_skill_dc_spinbox.place(x=RelPosMassroll.increase("x", 86), y=RelPosMassroll.increase("y", 1))

        mass_skill_check_button = tk.Button(GSM.Mass_roll_frame, text="Mass skill check", state="normal", command=RollMassSkillButton,
                                     padx=9, background="grey")
        mass_skill_check_button.place(x=RelPosMassroll.increase("x", 50), y=RelPosMassroll.same("y"))

    UndefinedMassSkillCheck()

    def PartySkillCheckRoll(button_pos) -> None:
        for widget in GSM.PartySkillCheckResults:
            widget.destroy()
        results = []
        for Player in GSM.Target_obj_list:
            skill_mod = int((getattr(Player, f"{GSM.WhichSkillToCheck.get().lower()}_mod_int")).get())
            rolltype = str((getattr(Player, f"{GSM.WhichSkillToCheck.get().lower()}_roll_type_str")).get())
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
            roll_total = roll + skill_mod
            if roll == 1 and GSM.Nat1_always_miss_bool.get():
                passed = "Nat1"  # nat 1 always fails with rule
            elif roll == 20:
                passed = "Nat20"
            elif (roll_total) >= (GSM.Mass_skill_check_dc_int.get()):
                passed = "Passed"
            else:
                passed = "Failed"
            results.append([Player.name_str.get(), roll_total, passed])

        button_x = int(button_pos["x"])
        button_y = int(button_pos["y"])
        GSM.RelPosMassroll.checkpoint_set("x", button_x)
        GSM.RelPosMassroll.checkpoint_set("y", button_y + 30)
        for i, result in enumerate(results):
            # Determine text color for nat1 or nat20
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

            results_label1 = tk.Label(GSM.Mass_roll_frame, text=str(result[0]), fg=text_colour3)
            results_label1.place(x=GSM.RelPosMassroll.checkpoint_get("x"), y=GSM.RelPosMassroll.checkpoint_get("y") + 20 * i)
            GSM.PartySkillCheckResults.append(results_label1)

            results_label1 = tk.Label(GSM.Mass_roll_frame, text=str(result[1]), fg=text_colour2)
            results_label1.place(x=GSM.RelPosMassroll.checkpoint_get("x") + 80, y=GSM.RelPosMassroll.checkpoint_get("y") + 20 * i)
            GSM.PartySkillCheckResults.append(results_label1)

            results_label1 = tk.Label(GSM.Mass_roll_frame, text=str(result[2]), fg=text_colour3)
            results_label1.place(x=GSM.RelPosMassroll.checkpoint_get("x") + 120, y=GSM.RelPosMassroll.checkpoint_get("y") + 20 * i)
            GSM.PartySkillCheckResults.append(results_label1)


    def PartySkillCheckUI() -> None:
        RelPosMassroll.checkpoint_set("x", 580)
        skillcheck_label = tk.Label(GSM.Mass_roll_frame, text="Party skill check", font=GSM.Title_font)
        skillcheck_label.place(x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.reset("y"))

        select_skill_label = tk.Label(GSM.Mass_roll_frame, text="Select skill: ")
        select_skill_label.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 37))

        select_skill_dropdown = tk.OptionMenu(GSM.Mass_roll_frame, GSM.WhichSkillToCheck,
                                              *["Perception", "Investigation", "Arcana", "Insight", "Stealth"])
        select_skill_dropdown.place(x=RelPosMassroll.increase("x", 60), y=RelPosMassroll.increase("y", -4))

        select_skill_label = tk.Label(GSM.Mass_roll_frame, text="DC:")
        select_skill_label.place(x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.increase("y", 33))
        mass_save_mod_spinbox = ttk.Spinbox(GSM.Mass_roll_frame, textvariable=GSM.SkillCheckDC, width=3, from_=5, to=30)
        mass_save_mod_spinbox.place(x=RelPosMassroll.increase("x", 30), y=RelPosMassroll.increase("y", 2))

        rollskillcheck_button = tk.Button(GSM.Mass_roll_frame, text="Party skill check", state="normal",
                                          command=lambda: PartySkillCheckRoll(rollskillcheck_button.place_info()),
                                          padx=9, background="grey")
        rollskillcheck_button.place(x=RelPosMassroll.set("x", RelPosMassroll.checkpoint_get("x")), y=RelPosMassroll.increase("y", 28))
    PartySkillCheckUI()