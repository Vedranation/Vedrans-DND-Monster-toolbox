import tkinter as tk
import json

from GlobalStateManager import GSM
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
            checkbox_label21.config(state="normal")
        else:
            checkbox_label21.config(state="disabled")
    checkbox_label21 = tk.Checkbutton(GSM.Settings_frame, text='Crit extra roll is max possible', variable=GSM.Crits_extra_die_is_max_bool,
                                     onvalue=True, offvalue=False)
    checkbox_label21.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))
    checkbox_label21.config(state="disabled")

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

    #Save and load presets
    save_button = tk.Button(GSM.Settings_frame, text="Save preset", state="normal", command=Save, background="green")
    save_button.place(x=RelPosSettings.increase("x", 10), y=RelPosSettings.increase("y", RelPosSettings.constant_y * 1.5))

    load_button = tk.Button(GSM.Settings_frame, text="Load preset", state="normal", command=Load, background="green")
    load_button.place(x=RelPosSettings.increase("x", 80), y=RelPosSettings.same("y"))

def Save() -> None:
    with open("preset1.json", "w") as file:
        json.dump({"N_casters_int": GSM.N_casters_int.get()}, file)

def Load() -> None:

    with open("preset1.json", "r") as file:
        loaded_data = json.load(file)
        GSM.N_casters_int.set(loaded_data["N_casters_int"])
        CreateSpellCasters(GSM.N_casters_int.get(), GSM.RelPosSpellCast)
        print(loaded_data)