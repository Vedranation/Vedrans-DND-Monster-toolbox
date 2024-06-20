import tkinter as tk
from tkinter import font as tkfont  # Import tkfont for font definitions
import pyperclip
import random
import GlobalStateManager


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

GSM = GlobalStateManager.GlobalsManager()

def Settings() -> None:
    #Main settings text
    main_settings_text_label = tk.Label(GSM.root, text="Main settings", font=GSM.Title_font)
    main_settings_text_label.grid(row=Row.same(), column=0, sticky="w")

    #Meets it beats it checkbox
    checkbox_label = tk.Checkbutton(GSM.root, text='Attack roll equal to AC hits',variable=GSM.Meets_it_beats_it_bool, onvalue=True, offvalue=False)
    checkbox_label.grid(row=Row.increase(), column=0, sticky="w")

    #Crits double dice checkbox
    checkbox_label2 = tk.Checkbutton(GSM.root, text='Crits double dmg instead of dice',variable=GSM.Crits_double_dmg_bool, onvalue=True, offvalue=False)
    GSM.Crits_double_dmg_bool.set(True)
    checkbox_label2.grid(row=Row.increase(), column=0, sticky="w")

    #Crit always hits
    checkbox_label3 = tk.Checkbutton(GSM.root, text='NAT 20 always hits',variable=GSM.Crits_always_hit_bool, onvalue=True, offvalue=False)
    GSM.Crits_always_hit_bool.set(True)
    checkbox_label3.grid(row=Row.increase(), column=0, sticky="w")

    #Nat1 always miss
    checkbox_label3 = tk.Checkbutton(GSM.root, text='NAT 1 always miss',variable=GSM.Nat1_always_miss_bool, onvalue=True, offvalue=False)
    GSM.Nat1_always_miss_bool.set(True)
    checkbox_label3.grid(row=Row.increase(), column=0, sticky="w")

Settings()

def RollType() -> None:
    #Roll type (adv/dis/normal)
    roll_type_text_label = tk.Label(GSM.root, text="Roll type:")
    roll_type_text_label.grid(row=Row.increase(), column=0, sticky="w")

    GSM.Roll_type_str.set(GSM.Roll_types[0])
    Roll_type_dropdown = tk.OptionMenu(GSM.root, GSM.Roll_type_str, *GSM.Roll_types)
    Roll_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=55)

RollType()

def Targets() -> None:
    #Number of targets
    n_targets_text_label = tk.Label(GSM.root, text="How many targets: ")
    n_targets_text_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.N_targets_int.set(1)

    def DrawTargetNameBoxes(n_targets) -> None:

        #Delete previous boxes
        for text in _target_name_label_list:
            text.destroy()
        _target_name_label_list.clear()
        for entry in _target_name_label_entry_list:
            entry.destroy()
        _target_name_label_entry_list.clear()
        GSM.Target_names_classes_list.clear()

        for i in range(n_targets):
            target_name = tk.StringVar()

            if i > 3:
                right_offset = 165
                row = _first_target_row + i - 4
            else:
                right_offset = 0
                row = _first_target_row + i
            _target_name_label = tk.Label(GSM.root, text=f"Target {i+1} name: ")
            _target_name_label.grid(row=row, column=0, sticky="w", padx=right_offset)
            _target_name_label_list.append(_target_name_label)

            _target_name_entry = tk.Entry(GSM.root, textvariable=target_name, width=11)
            _target_name_entry.grid(row=row, column=0, sticky="w", padx=right_offset+90)
            _target_name_label_entry_list.append(_target_name_entry)

            GSM.Target_names_classes_list.append(target_name)

    _target_name_label_list = []
    _target_name_label_entry_list = []
    _first_target_row = Row.same()+1

    DrawTargetNameBoxes(GSM.N_targets_int.get())
    N_targets_dropdown = tk.OptionMenu(GSM.root, GSM.N_targets_int, *[1, 2, 3, 4, 5, 6, 7, 8], command=DrawTargetNameBoxes)
    N_targets_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=110)

    #Make space for target names
    Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w")
    Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w")
    Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w")
    Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w")

    #Button to update targets
    Target_names_list = []
    Target_related_widgets = []
    def UpdateTargetsButton() -> None:
        Target_names_list.clear()
        for widget in Target_related_widgets:
            widget.destroy()
        Target_related_widgets.clear()

        for i, name in enumerate(GSM.Target_names_classes_list): #renames them
            if name.get():  # string not empty
                Target_names_list.append(name.get())
            else:
                Target_names_list.append(f"Target {i + 1}")

        for i, target in enumerate(Target_names_list):
            if i > 3:
                right_offset = 220
                row = _first_target2_row + i - 4
            else:
                right_offset = 0
                row = _first_target2_row + i

            target_label_text = tk.Label(GSM.root, text=f"{target}:")
            target_label_text.grid(row=row, column=0, sticky="w", padx=right_offset+360)
            AC_text_label = tk.Label(GSM.root, text="AC:")
            AC_text_label.grid(row=row, column=0, sticky="w", padx=right_offset+420)
            AC_int = tk.IntVar()
            AC_int.set(13)
            AC_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=AC_int, width=2)
            AC_entry.grid(row=row, column=0, sticky="w", padx=right_offset+450)

            n_monster_target_label_text = tk.Label(GSM.root, text="Monsters:")
            n_monster_target_label_text.grid(row=row, column=0, sticky="w", padx=right_offset+480)
            n_monster_int = tk.IntVar()
            n_monster_int.set(1)
            n_monster_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=n_monster_int, width=2)
            n_monster_entry.grid(row=row, column=0, sticky="w", padx=right_offset+540)

            for widget in (AC_entry, n_monster_entry, target_label_text, AC_text_label, n_monster_target_label_text):
                Target_related_widgets.append(widget)

    update_target_names_button = tk.Button(GSM.root, text="Create targets", state="normal", command=UpdateTargetsButton,
                                           padx=6, pady=5)
    update_target_names_button.grid(row=Row.increase(), column=0, sticky="w")

Targets()


def CreateMonster() -> None:
    #Monster settings text
    space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w")
    monster_settings_text_label = tk.Label(GSM.root, text="Monster settings", font=GSM.Title_font)
    monster_settings_text_label.grid(row=Row.increase(), column=0, sticky="w")
    #Number of attacks
    monster_n_attacks_text_label = tk.Label(GSM.root, text="Number of attacks: ")
    monster_n_attacks_text_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.Monster_n_attacks_int.set(1)
    monster_n_attacks_dropdown = tk.OptionMenu(GSM.root, GSM.Monster_n_attacks_int, *[1, 2, 3, 4])
    monster_n_attacks_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=110)

    #To hit
    monster_to_hit_label = tk.Label(GSM.root, text="Monster to hit: +")
    monster_to_hit_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.Monster_to_hit_int.set(6)
    monster_to_hit_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=GSM.Monster_to_hit_int, width=3)
    monster_to_hit_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)

    #Dmg 1
    monster_dmg1_text_label = tk.Label(GSM.root, text="Damage type 1:")
    monster_dmg1_text_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.Monster_dmg1_n_dice_int.set(1)
    monster_dmg1_number_dice_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=GSM.Monster_dmg1_n_dice_int, width=3)
    monster_dmg1_number_dice_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)


    GSM.Monster_dmg1_dice_type_str.set("d6")
    Dmg1_dice_type_dropdown = tk.OptionMenu(GSM.root, GSM.Monster_dmg1_dice_type_str, *GSM.Dice_types)
    Dmg1_dice_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=120)
    Dmg1_dmg_type = tk.StringVar()
    Dmg1_dmg_type.set("bludgeoning")
    def UpdateDmg1ExtraText(selected_dmg_type) -> None: #Because python says so this needs to be called here
        dmg1_extra_row
        dmg1_extra_text_label2 = tk.Label(GSM.root, text=selected_dmg_type + "                ")
        dmg1_extra_text_label2.grid(row=dmg1_extra_row, column=0, sticky="w", padx=120)
    dmg1_extra_row = Row.same() + 1
    Dmg1_dmg_type_dropdown = tk.OptionMenu(GSM.root, Dmg1_dmg_type, *GSM.Dmg_types, command=UpdateDmg1ExtraText)
    Dmg1_dmg_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=180)

    #Dmg 1 extra
    UpdateDmg1ExtraText(Dmg1_dmg_type.get())
    Dmg1_extra_text_label = tk.Label(GSM.root, text="Damage 1 flat:  +")
    Dmg1_extra_text_label.grid(row=Row.increase(), column=0, sticky="w")
    Dmg1_extra_int = tk.IntVar()
    Dmg1_extra_int.set(2)
    Dmg1_extra_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=Dmg1_extra_int, width=3)
    Dmg1_extra_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)

    #Dmg 2
    Dmg2_text_label = tk.Label(GSM.root, text="Damage type 2:")
    Dmg2_text_label.grid(row=Row.increase(), column=0, sticky="w")
    Dmg2_number_dice_int = tk.IntVar()
    Dmg2_number_dice_int.set(1)
    Dmg2_number_dice_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=Dmg2_number_dice_int, width=3)
    Dmg2_number_dice_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)

    Dmg2_dice_type = tk.StringVar()
    Dmg2_dice_type.set("d4")
    Dmg2_dice_type_dropdown = tk.OptionMenu(GSM.root, Dmg2_dice_type, *Dice_types)
    Dmg2_dice_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=120)
    Dmg2_dmg_type = tk.StringVar()
    Dmg2_dmg_type.set("fire")
    Dmg2_dmg_type_dropdown = tk.OptionMenu(GSM.root, Dmg2_dmg_type, *Monster_dmg_types)
    Dmg2_dmg_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=180)

CreateMonster()

Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=0)

def MassSavingThrow() -> None:
    #Spell + to save
    Spell_plus_text_label = tk.Label(GSM.root, text="Saving throw mod:  +")
    Spell_plus_text_label.grid(row=Row.increase(), column=0, sticky="w")
    Spell_plus_int = tk.IntVar()
    Spell_plus_int.set(2)
    Spell_plus_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=Spell_plus_int, width=3)
    Spell_plus_entry.grid(row=Row.same(), column=0, sticky="w", padx=120)
    #Save DC
    Save_DC_text_label = tk.Label(GSM.root, text="Spell save DC: ")
    Save_DC_text_label.grid(row=Row.increase(), column=0, sticky="w")
    Save_DC_int = tk.IntVar()
    Save_DC_int.set(13)
    Save_DC_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=Save_DC_int, width=3)
    Save_DC_entry.grid(row=Row.same(), column=0, sticky="w", padx=120)
    #How many monsters
    Spell_n_monsters_text_label = tk.Label(GSM.root, text="How many monsters: ")
    Spell_n_monsters_text_label.grid(row=Row.increase(), column=0, sticky="w")
    Spell_n_monsters_int = tk.IntVar()
    Spell_n_monsters_int.set(6)
    Spell_n_monsters_entry = tk.Entry(GSM.root, borderwidth=2, textvariable=Spell_n_monsters_int, width=3)
    Spell_n_monsters_entry.grid(row=Row.same(), column=0, sticky="w", padx=120)

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


#Target settings text
Target_settings_text_label = tk.Label(GSM.root, text="Target settings", font=GSM.Title_font)
Target_settings_text_label.grid(row=Row.reset(), column=0, sticky="w", padx=360)
#Button to save target settings

_first_target2_row = Row.increase()

#Make space for target names
Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)
Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)
Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)

fumble_table = ["Get distracted: Disadvantage on next attack", "Overextended Swing: Next attack on you have advantage", "Hit yourself for half dmg",
                "Hit ally for half dmg", "String Snap: If using a bow or crossbow", "Fall prone", "Ranged attack/spell: Goes in completely random direction and hits something",
                "Drop your weapon", "Misjudged Distance: enemy within 5ft can attempt a free grapple check", "Twisted Ankle: half move speed next turn",
                "Overexertion: Lose bonus action this turn", "Self doubt: Lose reaction this turn", "Ice spells: Your feet freeze, is rooted until next turn",
                "Fire spells: Lit yourself on fire, 2 turns take 1d6 dmg or action to put it out", "Ranged weapons: Drop 10 pieces of ammunition, it scatters and needs action to collect",
                "A random glass item/potion breaks and spills", "Coin pouch rips, you lose 5d8 GP", "If spell: Roll wild magic table", "Loud noise: You cause a very loud noise",
                "Panic: Become frightened of whatever you just attacked", "Sand/Mud in eyes: Become blinded until your next turn", "Drop formation: Lose 2 AC until next turn",
                "Instinct movement: You provoke instincts in enemy, they move 10ft immediately"]
TargetDmgWidgets = []

def ROLL() -> None:
    n_dice1 = GSM.Monster_dmg1_n_dice_int.get()
    dice_type1 = GSM.Monster_dmg1_dice_type_str.get()
    flat_dmg1 = Dmg1_extra_int.get()
    dmg_type1 = Dmg1_dmg_type.get()
    n_dice2 = Dmg2_number_dice_int.get()
    dice_type2 = Dmg2_dice_type.get()
    dmg_type2 = Dmg2_dmg_type.get()
    rolltype = GSM.Roll_type_str.get()
    print("----")
    for widget in TargetDmgWidgets:
        widget.destroy()
    TargetDmgWidgets.clear()
    row = _first_target3_row

    def display(hits, dmgs1, dmgs2, target_name) -> None:
        nonlocal row
        def custom_sort(item):
            if isinstance(item, str):
                return (0, item)  # Put strings first
            else:
                return (1, -item)  # Sort integers in reverse order

        sorted_hits = sorted(hits, key=custom_sort)
        print(sorted_hits)
        TargetDmgLabel = tk.Label(GSM.root, text=(f"{target_name}"))
        TargetDmgLabel.grid(column=0, padx=340, row=row, sticky="w")
        TargetDmgWidgets.append(TargetDmgLabel)

        filtered_length = (lambda hits: len([hit for hit in hits if hit != "nat1"]))(sorted_hits)
        TargetDmgLabel = tk.Label(GSM.root, text=(f"|  {filtered_length}  |   {sorted_hits}"))
        TargetDmgLabel.grid(column=0, padx=410, row=row, sticky="w")
        TargetDmgWidgets.append(TargetDmgLabel)

        TargetDmgLabel = tk.Label(GSM.root, text=(f"|   {sum(dmgs1)} {dmg_type1}   |   {sum(dmgs2)} {dmg_type2}"))
        TargetDmgLabel.grid(column=0, padx=670, row=row, sticky="w")
        TargetDmgWidgets.append(TargetDmgLabel)

        row = row + 1

    def damage(crit=False) -> (int, int):
        if not crit:
            dmg1 = flat_dmg1
            for dice in range(n_dice1):
                dmg1 = dmg1 + RollDice(dice_type1)
            dmg2 = 0
            for dice in range(n_dice2):
                dmg2 = dmg2 + RollDice(dice_type2)
        else:
            if Crits_double_dmg_bool.get():
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
    for i, target_name in enumerate(GSM.Target_names_list):
        print()
        print(target_name)
        ac = int(Target_related_widgets[0 + i * 5].get())
        n_monsters = int(Target_related_widgets[1 + i * 5].get())

        hits = []
        dmgs1 = []
        dmgs2 = []
        for monster in range(n_monsters):
            for attack in range(N_attacks_int.get()):
                tohit = To_hit_int.get()
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
                        dmg1, dmg2 = damage(crit=False)
                        hits.append(roll+tohit)
                        dmgs1.append(dmg1)
                        dmgs2.append(dmg2)

        print(f"Hits: {hits}, {dmgs1} {dmg_type1}, {dmgs2} {dmg_type2}")
        display(hits, dmgs1, dmgs2, target_name)
        print(f"Total: {sum(dmgs1)} {dmg_type1}, {sum(dmgs2)} {dmg_type2}")

#3 Roll buttons
ROLL_button = tk.Button(GSM.root, text="ROLL", state="normal", command=ROLL, font=GSM.Title_font,
                                           padx=9, background="red")
ROLL_button.grid(row=Row.increase(), column=0, sticky="w", padx=360)

def RollSpellSave():
    for widget in TargetDmgWidgets:
        widget.destroy()
    TargetDmgWidgets.clear()
    passes = 0
    rolls = []
    rolltype = GSM.Roll_type_str.get()
    for i in range(Spell_n_monsters_int.get()):
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
        roll = roll + Spell_plus_int.get()
        if (roll) >= (Save_DC_int.get()):
            passes += 1
        rolls.append(roll)

    rolls.sort(reverse=True)
    save_label = tk.Label(GSM.root, text=(f"Out of {Spell_n_monsters_int.get()} monsters, {passes} passed and {Spell_n_monsters_int.get()-passes} failed"))
    save_label.grid(column=0, padx=360, row=_first_target3_row, sticky="w")
    TargetDmgWidgets.append(save_label)

    save_label = tk.Label(GSM.root, text=(f"{rolltype} rolls with were: {rolls}"))
    save_label.grid(column=0, padx=360, row=_first_target3_row+1, sticky="w")
    TargetDmgWidgets.append(save_label)


DC_button = tk.Button(GSM.root, text="Roll save", state="normal", command=RollSpellSave,
                                           padx=9, background="grey")
DC_button.grid(row=Row.same(), column=0, sticky="w", padx=450)

def RollFumble():
    for widget in TargetDmgWidgets:
        widget.destroy()
    TargetDmgWidgets.clear()
    fumble_label = tk.Label(GSM.root, text=(f"{random.choice(fumble_table)}"))
    fumble_label.grid(column=0, padx=360, row=_first_target3_row, sticky="w")

    TargetDmgWidgets.append(fumble_label)
nat1_button = tk.Button(GSM.root, text="Roll fumble", state="normal", command=RollFumble,
                                           padx=9, background="grey")
nat1_button.grid(row=Row.same(), column=0, sticky="w", padx=530)

Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)
#Target settings text
Target_settings_text_label = tk.Label(GSM.root, text="Roll results", font=GSM.Title_font)
Target_settings_text_label.grid(row=Row.increase(), column=0, sticky="w", padx=360)

_first_target3_row = Row.increase()

#TODO: Add a boss section, which tracks boss cooldowns, legendary actions etc
#TODO: Add automated rolling for random encounter table. Let players import a list, saying chance of each encounter,
#   which happen per night and which per day, how often to check, and how long PC's travelled and then determine the outcome
#Make space for target names
Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)
Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)
Space = tk.Label(GSM.root, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)


GSM.root.mainloop()