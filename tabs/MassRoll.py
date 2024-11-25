import tkinter as tk
from tkinter import ttk
from GlobalStateManager import GSM
from utilities import RollDice

def MassRoll(RelPosMassroll, RelPosMonsters) -> None:
    RelPosMassroll.constant_y = 25
    def UndefinedMassSave():
        mass_savingthrow_label = tk.Label(GSM.Mass_roll_frame, text="Mass undefined\nsaving throw", font=GSM.Title_font)
        mass_savingthrow_label.place(x=RelPosMonsters.reset("x"), y=RelPosMonsters.reset("y"))
        #Saving throw modifier
        mass_save_mod_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw mod:  +")
        mass_save_mod_text_label.place(x=RelPosMassroll.same("x"), y=RelPosMassroll.increase("y", 50))

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
        mass_save_n_monsters_text_label = tk.Label(GSM.Mass_roll_frame, text="How many creatures: ")
        mass_save_n_monsters_text_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", RelPosMassroll.constant_y))

        GSM.Mass_save_n_monsters_int.set(6)
        mass_save_n_monsters_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_n_monsters_int, width=3)
        mass_save_n_monsters_entry.place(x=RelPosMassroll.increase("x", 120), y=RelPosMassroll.same("y"))

    UndefinedMassSave()

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
            f"PASSES: {passes}     FAILS: {GSM.Mass_save_n_monsters_int.get() - passes}"))
        mass_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.set("y", current_button_y+30))
        GSM.Results_random_gen_widgets_to_clear.append(mass_save_results_label)

        mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(f"Results: {rolls}"))
        mass_save_results_label.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))
        GSM.Results_random_gen_widgets_to_clear.append(mass_save_results_label)

    mass_save_button = tk.Button(GSM.Mass_roll_frame, text="Roll save", state="normal", command=RollMassSaveButton,
                          padx=9, background="grey")
    mass_save_button.place(x=RelPosMassroll.reset("x"), y=RelPosMassroll.increase("y", 30))

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
        mass_skill_check_label = tk.Label(GSM.Mass_roll_frame, text="Mass undefined skill check", font=GSM.Title_font)
        RelPosMassroll.checkpoint_set("x", 220)
        mass_skill_check_label.place(x=RelPosMassroll.set("x", 220), y=RelPosMassroll.reset("y"))
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