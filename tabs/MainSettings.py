import tkinter as tk
import json

from GlobalStateManager import GSM
from tabs.MonsterCreation import PreservePreviousMonsters
from tabs.PlayerCreation import PreservePreviousTargets
from tabs.Spellcasters import CreateSpellCasters

def Settings(RelPosSettings) -> None:

    #Main settings text
    main_settings_text_label = tk.Label(GSM.Settings_frame, text="Main settings", font=GSM.Title_font)
    main_settings_text_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.same("y"))

    #Meets it beats it checkbox
    checkbox_label = tk.Checkbutton(GSM.Settings_frame, text='Attack roll = AC is hit (meets it beats it)',variable=GSM.Meets_it_beats_it_bool, onvalue=True, offvalue=False)
    checkbox_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    #Extra crit die is max possible roll
    def EnableDisableMaxDiceRoll() -> None:
        if GSM.Crits_double_dmg_bool.get() == False:
            Checkbox_CritExtraDiceMaxDmg.config(state="normal")
        else:
            Checkbox_CritExtraDiceMaxDmg.config(state="disabled")
            GSM.Crits_extra_die_is_max_bool.set(False)
    Checkbox_CritExtraDiceMaxDmg = tk.Checkbutton(GSM.Settings_frame, text='Crit extra roll is max possible', variable=GSM.Crits_extra_die_is_max_bool,
                                     onvalue=True, offvalue=False)
    Checkbox_CritExtraDiceMaxDmg.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))
    Checkbox_CritExtraDiceMaxDmg.config(state="disabled")
    GSM.Load_widgets_mainsettings_dict["Checkbox_CritExtraDiceMaxDmg"] = Checkbox_CritExtraDiceMaxDmg #Save widget into dict to be able to find it when loading data

    #Crits double dice checkbox
    checkbox_label2 = tk.Checkbutton(GSM.Settings_frame, text='Crits double TOTAL dmg instead of dice',variable=GSM.Crits_double_dmg_bool,
                                     onvalue=True, offvalue=False, command=EnableDisableMaxDiceRoll)
    checkbox_label2.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    #Nat1 always miss
    checkbox_label4 = tk.Checkbutton(GSM.Settings_frame, text='NAT 1 always miss',variable=GSM.Nat1_always_miss_bool, onvalue=True, offvalue=False)
    checkbox_label4.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    # (Dis)advantages combine into super (dis)advantages
    checkbox_label5 = tk.Checkbutton(GSM.Settings_frame, text='2 Advantages combine into 1 Super Advantage', variable=GSM.Adv_combine_bool,
                                     onvalue=True, offvalue=False)
    checkbox_label5.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    #TODO: Roll stealth detection using passive perception or active perception

    #Save and load presets
    save_button = tk.Button(GSM.Settings_frame, text="Save preset", state="normal", command=Save, background="green")
    save_button.place(x=RelPosSettings.increase("x", 10), y=RelPosSettings.increase("y", RelPosSettings.constant_y * 1.5))

    load_button = tk.Button(GSM.Settings_frame, text="Load preset", state="normal", command=Load, background="green")
    load_button.place(x=RelPosSettings.increase("x", 80), y=RelPosSettings.same("y"))

def Save() -> None:
    data = {
        # Main settings
        "Meets_it_beats_it_bool": GSM.Meets_it_beats_it_bool.get(),
        "Crits_double_dmg_bool": GSM.Crits_double_dmg_bool.get(),
        "Crits_extra_die_is_max_bool": GSM.Crits_extra_die_is_max_bool.get(),
        "Nat1_always_miss_bool": GSM.Nat1_always_miss_bool.get(),
        "Adv_combine_bool": GSM.Adv_combine_bool.get(),

        # Spellcasters
        "N_casters_int": GSM.N_casters_int.get(),

        # Player targets (Saved as a list of dictionaries)
        "N_targets_int": GSM.N_targets_int.get(),
        "Target_obj_list": [
            {
                "name_str": playerObj.name_str.get(),
                "ac_int": playerObj.ac_int.get(),
                "monster_roll_type_against_str": playerObj.monster_roll_type_against_str.get(),
                "adamantine": playerObj.adamantine.get(),
                "perception_roll_type_str": playerObj.perception_roll_type_str.get(),
                "perception_mod_int": playerObj.perception_mod_int.get(),
                "investigation_mod_int": playerObj.investigation_mod_int.get(),
                "investigation_roll_type_str": playerObj.investigation_roll_type_str.get(),
                "arcana_mod_int": playerObj.arcana_mod_int.get(),
                "arcana_roll_type_str": playerObj.arcana_roll_type_str.get(),
                "insight_mod_int": playerObj.insight_mod_int.get(),
                "insight_roll_type_str": playerObj.insight_roll_type_str.get(),
                "stealth_mod_int": playerObj.stealth_mod_int.get(),
                "stealth_roll_type_str": playerObj.stealth_roll_type_str.get(),
                "passiveperception_int": playerObj.passiveperception_int.get(),
            }
            for playerObj in GSM.Target_obj_list
        ],

        #Monsters
        "N_monsters_int": GSM.N_monsters_int.get(),
        "Monster_obj_list": [
            {
                "name_str": monsterObj.name_str.get(),
                "ac_int": monsterObj.ac_int.get(),
                "roll_type": monsterObj.roll_type.get(),
                "n_attacks": monsterObj.n_attacks.get(),
                "to_hit_mod": monsterObj.to_hit_mod.get(),

                "dmg_type_1": monsterObj.dmg_type_1.get(),
                "dmg_n_die_1": monsterObj.dmg_n_die_1.get(),
                "dmg_die_type_1": monsterObj.dmg_die_type_1.get(),
                "dmg_flat_1": monsterObj.dmg_flat_1.get(),

                "dmg_type_2": monsterObj.dmg_type_2.get(),
                "dmg_die_type_2": monsterObj.dmg_die_type_2.get(),
                "dmg_n_die_2": monsterObj.dmg_n_die_2.get(),
                "dmg_flat_2": monsterObj.dmg_flat_2.get(),

                "on_hit_force_saving_throw_bool": monsterObj.on_hit_force_saving_throw_bool.get(),
                "on_hit_save_dc": monsterObj.on_hit_save_dc.get(),
                "on_hit_save_type": monsterObj.on_hit_save_type.get(),

                "reroll_1_on_hit": monsterObj.reroll_1_on_hit.get(),
                "reroll_1_2_dmg": monsterObj.reroll_1_2_dmg.get(),
                "brutal_critical": monsterObj.brutal_critical.get(),
                "crit_number": monsterObj.crit_number.get(),
                "savage_attacker": monsterObj.savage_attacker.get(),
                "bane": monsterObj.bane.get(),
                "bless": monsterObj.bless.get(),

                "walking_speed_int": monsterObj.walking_speed_int.get(),
                "flying_speed_int": monsterObj.flying_speed_int.get(),
                "climbing_speed_int": monsterObj.climbing_speed_int.get(),
                "burrowing_speed_int": monsterObj.burrowing_speed_int.get(),

                "savingthrow_str_mod_int": monsterObj.savingthrow_str_mod_int.get(),
                "savingthrow_str_roll_type_str": monsterObj.savingthrow_str_roll_type_str.get(),
                "savingthrow_dex_mod_int": monsterObj.savingthrow_dex_mod_int.get(),
                "savingthrow_dex_roll_type_str": monsterObj.savingthrow_dex_roll_type_str.get(),
                "savingthrow_con_mod_int": monsterObj.savingthrow_con_mod_int.get(),
                "savingthrow_con_roll_type_str": monsterObj.savingthrow_con_roll_type_str.get(),
                "savingthrow_int_mod_int": monsterObj.savingthrow_int_mod_int.get(),
                "savingthrow_int_roll_type_str": monsterObj.savingthrow_int_roll_type_str.get(),
                "savingthrow_wis_mod_int": monsterObj.savingthrow_wis_mod_int.get(),
                "savingthrow_wis_roll_type_str": monsterObj.savingthrow_wis_roll_type_str.get(),
                "savingthrow_cha_mod_int": monsterObj.savingthrow_cha_mod_int.get(),
                "savingthrow_cha_roll_type_str": monsterObj.savingthrow_cha_roll_type_str.get(),
                "passiveperception_int": monsterObj.passiveperception_int.get(),
            }
            for monsterObj in GSM.Monster_obj_list
        ]
    }

    # Save to JSON file
    with open("Presets/preset1.json", "w") as file:
        json.dump(data, file, indent=4)  # Pretty print for easier debugging


def Load() -> None:

    with open("Presets\preset1.json", "r") as file:
        loaded_data = json.load(file)

        #Main settings
        GSM.Meets_it_beats_it_bool.set(loaded_data["Meets_it_beats_it_bool"])
        GSM.Crits_double_dmg_bool.set(loaded_data["Crits_double_dmg_bool"])
        if GSM.Crits_double_dmg_bool.get() == False: #Disable checkbox when it should be
            GSM.Load_widgets_mainsettings_dict["Checkbox_CritExtraDiceMaxDmg"].config(state="normal")
        else:
            GSM.Load_widgets_mainsettings_dict["Checkbox_CritExtraDiceMaxDmg"].config(state="disabled")
        GSM.Crits_extra_die_is_max_bool.set(loaded_data["Crits_extra_die_is_max_bool"])
        GSM.Nat1_always_miss_bool.set(loaded_data["Nat1_always_miss_bool"])
        GSM.Adv_combine_bool.set(loaded_data["Adv_combine_bool"])

        #Spellcasters
        #TODO: Incorporate spellcasters into monsters tab

        # GSM.N_casters_int.set(loaded_data["N_casters_int"])
        # CreateSpellCasters(GSM.N_casters_int.get(), GSM.RelPosSpellCast)

        #Players
        GSM.N_targets_int.set(loaded_data["N_targets_int"])
        PreservePreviousTargets(GSM.N_targets_int.get(), GSM.RelPosTargets)

        # Iterate over both GSM.Target_obj_list and loaded data, but limit to N_targets_int
        for i, playerObj in enumerate(GSM.Target_obj_list[:GSM.N_targets_int.get()]):
            if i < len(loaded_data["Target_obj_list"]):  # Prevent indexing error if JSON has fewer entries
                player_data = loaded_data["Target_obj_list"][i]  # Get the corresponding loaded data

                # Set values from loaded data
                playerObj.name_str.set(player_data["name_str"])
                playerObj.ac_int.set(player_data["ac_int"])
                playerObj.monster_roll_type_against_str.set(player_data["monster_roll_type_against_str"])
                playerObj.adamantine.set(player_data["adamantine"])
                playerObj.perception_roll_type_str.set(player_data["perception_roll_type_str"])
                playerObj.perception_mod_int.set(player_data["perception_mod_int"])
                playerObj.investigation_mod_int.set(player_data["investigation_mod_int"])
                playerObj.investigation_roll_type_str.set(player_data["investigation_roll_type_str"])
                playerObj.arcana_mod_int.set(player_data["arcana_mod_int"])
                playerObj.arcana_roll_type_str.set(player_data["arcana_roll_type_str"])
                playerObj.insight_mod_int.set(player_data["insight_mod_int"])
                playerObj.insight_roll_type_str.set(player_data["insight_roll_type_str"])
                playerObj.stealth_mod_int.set(player_data["stealth_mod_int"])
                playerObj.stealth_roll_type_str.set(player_data["stealth_roll_type_str"])
                playerObj.passiveperception_int.set(player_data["passiveperception_int"])
                playerObj._my_button.config(text=playerObj.name_str.get())

        #Monsters
        GSM.N_monsters_int.set(loaded_data["N_monsters_int"])
        PreservePreviousMonsters(GSM.N_monsters_int.get(), GSM.RelPosMonsters)

        # Iterate over both GSM.Monster_obj_list and loaded data, but limit to N_monsters_int
        for i, monsterObj in enumerate(GSM.Monster_obj_list[:GSM.N_monsters_int.get()]):
            if i < len(loaded_data["Monster_obj_list"]):  # Prevent indexing error if JSON has fewer entries
                monster_data = loaded_data["Monster_obj_list"][i]  # Get the corresponding loaded data

                # Set values from loaded data
                monsterObj.name_str.set(monster_data["name_str"])
                monsterObj.ac_int.set(monster_data["ac_int"])
                monsterObj.roll_type.set(monster_data["roll_type"])
                monsterObj.n_attacks.set(monster_data["n_attacks"])
                monsterObj.to_hit_mod.set(monster_data["to_hit_mod"])

                monsterObj.dmg_type_1.set(monster_data["dmg_type_1"])
                monsterObj.dmg_n_die_1.set(monster_data["dmg_n_die_1"])
                monsterObj.dmg_die_type_1.set(monster_data["dmg_die_type_1"])
                monsterObj.dmg_flat_1.set(monster_data["dmg_flat_1"])

                monsterObj.dmg_type_2.set(monster_data["dmg_type_2"])
                monsterObj.dmg_die_type_2.set(monster_data["dmg_die_type_2"])
                monsterObj.dmg_n_die_2.set(monster_data["dmg_n_die_2"])
                monsterObj.dmg_flat_2.set(monster_data["dmg_flat_2"])

                monsterObj.on_hit_force_saving_throw_bool.set(monster_data["on_hit_force_saving_throw_bool"])
                monsterObj.on_hit_save_dc.set(monster_data["on_hit_save_dc"])
                monsterObj.on_hit_save_type.set(monster_data["on_hit_save_type"])

                monsterObj.reroll_1_on_hit.set(monster_data["reroll_1_on_hit"])
                monsterObj.reroll_1_2_dmg.set(monster_data["reroll_1_2_dmg"])
                monsterObj.brutal_critical.set(monster_data["brutal_critical"])
                monsterObj.crit_number.set(monster_data["crit_number"])
                monsterObj.savage_attacker.set(monster_data["savage_attacker"])
                monsterObj.bane.set(monster_data["bane"])
                monsterObj.bless.set(monster_data["bless"])

                monsterObj.walking_speed_int.set(monster_data["walking_speed_int"])
                monsterObj.flying_speed_int.set(monster_data["flying_speed_int"])
                monsterObj.climbing_speed_int.set(monster_data["climbing_speed_int"])
                monsterObj.burrowing_speed_int.set(monster_data["burrowing_speed_int"])

                monsterObj.savingthrow_str_mod_int.set(monster_data["savingthrow_str_mod_int"])
                monsterObj.savingthrow_str_roll_type_str.set(monster_data["savingthrow_str_roll_type_str"])
                monsterObj.savingthrow_dex_mod_int.set(monster_data["savingthrow_dex_mod_int"])
                monsterObj.savingthrow_dex_roll_type_str.set(monster_data["savingthrow_dex_roll_type_str"])
                monsterObj.savingthrow_con_mod_int.set(monster_data["savingthrow_con_mod_int"])
                monsterObj.savingthrow_con_roll_type_str.set(monster_data["savingthrow_con_roll_type_str"])
                monsterObj.savingthrow_int_mod_int.set(monster_data["savingthrow_int_mod_int"])
                monsterObj.savingthrow_int_roll_type_str.set(monster_data["savingthrow_int_roll_type_str"])
                monsterObj.savingthrow_wis_mod_int.set(monster_data["savingthrow_wis_mod_int"])
                monsterObj.savingthrow_wis_roll_type_str.set(monster_data["savingthrow_wis_roll_type_str"])
                monsterObj.savingthrow_cha_mod_int.set(monster_data["savingthrow_cha_mod_int"])
                monsterObj.savingthrow_cha_roll_type_str.set(monster_data["savingthrow_cha_roll_type_str"])
                monsterObj.passiveperception_int.set(monster_data["passiveperception_int"])
                monsterObj._my_button.config(text=monsterObj.name_str.get())
