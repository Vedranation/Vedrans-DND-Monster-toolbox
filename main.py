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
class PlayerStats():
    def __init__(self):
        #TODO: Make a setting to pick between PP and rolling percep for mass percep check
        self.name_str: str = tk.StringVar()
        self.ac_int = tk.IntVar()
        self.ac_int.set(13)
        #TODO: Make multiple monsters
        self.n_monsters_int = tk.IntVar()
        self.n_monsters_int.set(0)

        self.pp: int = 10 #passive perception
        self.percep_mod: int = 2
        self.pi: int = 10 #passive investigation
        self.arcana_mod: int = 0
        self.adamantine: int = False #turn crits into normal attacks

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

def RollType() -> None:
    #Roll type (adv/dis/normal)
    roll_type_text_label = tk.Label(GSM.Settings_frame, text="Roll type:")
    roll_type_text_label.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

    GSM.Roll_type_str.set(GSM.Roll_types[0])
    Roll_type_dropdown = tk.OptionMenu(GSM.Settings_frame, GSM.Roll_type_str, *GSM.Roll_types)
    Roll_type_dropdown.place(x=RelPosSettings.same("x"), y=RelPosSettings.increase("y", RelPosSettings.constant_y))

RollType()


def Targets() -> None:
    # Target settings text
    Target_settings_text_label = tk.Label(GSM.Targets_frame, text="Target settings", font=GSM.Title_font)
    Target_settings_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))

    _first_target2_row = Row.increase()

    #Number of targets
    n_targets_text_label = tk.Label(GSM.Targets_frame, text="How many targets: ")
    n_targets_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.increase("y", 29))
    GSM.N_targets_int.set(1)

    # Button to update targets
    GSM.Target_related_widgets = []

    def CreateTargetsButton() -> None:
        for widget in GSM.Target_related_widgets:
            widget.destroy()
        GSM.Target_related_widgets.clear()
        # FIXME: Changing how many targets creates new objects, which removes all progress in entering - can be annoying
        for i, TargetObj in enumerate(GSM.Target_obj_list):

            if TargetObj.name_str.get():  # string not empty
                pass
            else:
                TargetObj.name_str.set(f"Target {i + 1}")
            if i > 3:
                right_offset = 220
                row = _first_target2_row + i - 4
            else:
                right_offset = 0
                row = _first_target2_row + i

            target_text_label = tk.Label(GSM.Targets_frame, text=f"{TargetObj.name_str.get()}:")
            target_text_label.grid(row=row, column=0, sticky="w", padx=right_offset + 360)
            target_ac_text_label = tk.Label(GSM.Targets_frame, text="AC:")
            target_ac_text_label.grid(row=row, column=0, sticky="w", padx=right_offset + 420)

            target_ac_entry = tk.Entry(GSM.Targets_frame, borderwidth=2, textvariable=TargetObj.ac_int, width=2)
            target_ac_entry.grid(row=row, column=0, sticky="w", padx=right_offset + 450)

            target_n_monsters_text_label = tk.Label(GSM.Targets_frame, text="Monsters:")
            target_n_monsters_text_label.grid(row=row, column=0, sticky="w", padx=right_offset + 480)

            target_n_monster_entry = tk.Entry(GSM.Targets_frame, borderwidth=2, textvariable=TargetObj.n_monsters_int,
                                              width=2)
            target_n_monster_entry.grid(row=row, column=0, sticky="w", padx=right_offset + 540)

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
    _first_target_row_y = RelPosTargets.increase("y", 45)

    DrawTargetInputNameBoxes(GSM.N_targets_int.get())




Targets()


def CreateMonster() -> None:
    #Monster settings text
    space = tk.Label(GSM.Monsters_frame, text="").grid(row=Row.increase(), column=0, sticky="w")
    monster_settings_text_label = tk.Label(GSM.Monsters_frame, text="Monster settings", font=GSM.Title_font)
    monster_settings_text_label.grid(row=Row.increase(), column=0, sticky="w")
    #Number of attacks
    monster_n_attacks_text_label = tk.Label(GSM.Monsters_frame, text="Number of attacks: ")
    monster_n_attacks_text_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.Monster_n_attacks_int.set(1)
    monster_n_attacks_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.Monster_n_attacks_int, *[1, 2, 3, 4])
    monster_n_attacks_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=110)

    #To hit
    monster_to_hit_label = tk.Label(GSM.Monsters_frame, text="Monster to hit: +")
    monster_to_hit_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.Monster_to_hit_int.set(6)
    monster_to_hit_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=GSM.Monster_to_hit_int, width=3)
    monster_to_hit_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)
    #TODO: add tenacity, reroll 1s and 2s, brutal critical etc, saving throw on hit
    #Dmg 1
    monster_dmg1_text_label = tk.Label(GSM.Monsters_frame, text="Damage type 1:")
    monster_dmg1_text_label.grid(row=Row.increase(), column=0, sticky="w")
    GSM.Monster_dmg1_n_dice_int.set(1)
    monster_dmg1_number_dice_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=GSM.Monster_dmg1_n_dice_int, width=3)
    monster_dmg1_number_dice_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)


    GSM.Monster_dmg1_dice_type_str.set("d6")
    monster_dmg1_dice_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.Monster_dmg1_dice_type_str, *GSM.Dice_types)
    monster_dmg1_dice_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=120)
    GSM.Monster_dmg1_dmg_type_str.set("bludgeoning")
    def UpdateMonsterDmg1FlatText(selected_dmg_type) -> None: #Because python says so this needs to be called here
        #This just displays the user selected dmg type in next line (right next to flat number)
        #monster_dmg1_flat_row
        monster_dmg1_extra_text_label2 = tk.Label(GSM.Monsters_frame, text=selected_dmg_type + "                ")
        monster_dmg1_extra_text_label2.grid(row=monster_dmg1_flat_row, column=0, sticky="w", padx=120)
    monster_dmg1_flat_row = Row.same() + 1 #This stores the row number where text of flat dmg is
    monster_dmg1_dmg_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.Monster_dmg1_dmg_type_str, *GSM.Dmg_types, command=UpdateMonsterDmg1FlatText)
    monster_dmg1_dmg_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=180)

    #Dmg 1 flat
    UpdateMonsterDmg1FlatText(GSM.Monster_dmg1_dmg_type_str.get())
    monster_dmg1_flat_text_label = tk.Label(GSM.Monsters_frame, text="Damage 1 flat:  +")
    monster_dmg1_flat_text_label.grid(row=Row.increase(), column=0, sticky="w")

    GSM.Monster_dmg1_flat_int.set(2)
    monster_dmg1_extra_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=GSM.Monster_dmg1_flat_int, width=3)
    monster_dmg1_extra_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)

    #Dmg 2
    monster_dmg2_text_label = tk.Label(GSM.Monsters_frame, text="Damage type 2:")
    monster_dmg2_text_label.grid(row=Row.increase(), column=0, sticky="w")

    GSM.Monster_dmg2_n_dice_int.set(1)
    monster_dmg2_n_dice_entry = tk.Entry(GSM.Monsters_frame, borderwidth=2, textvariable=GSM.Monster_dmg2_n_dice_int, width=3)
    monster_dmg2_n_dice_entry.grid(row=Row.same(), column=0, sticky="w", padx=95)

    GSM.Monster_dmg2_dice_type_str.set("d4")
    monster_dmg2_dice_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.Monster_dmg2_dice_type_str, *GSM.Dice_types)
    monster_dmg2_dice_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=120)

    GSM.Monster_dmg2_dmg_type_str.set("fire")
    monster_dmg2_dmg_type_dropdown = tk.OptionMenu(GSM.Monsters_frame, GSM.Monster_dmg2_dmg_type_str, *GSM.Dmg_types)
    monster_dmg2_dmg_type_dropdown.grid(row=Row.same(), column=0, sticky="w", padx=180)

CreateMonster()

def MassSavingThrow() -> None:
    #Saving throw modifier
    mass_save_mod_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw mod:  +")
    mass_save_mod_text_label.grid(row=Row.increase(), column=0, sticky="w")

    GSM.Mass_save_mod_int.set(2)
    mass_save_mod_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_mod_int, width=3)
    mass_save_mod_entry.grid(row=Row.same(), column=0, sticky="w", padx=120)
    #Save DC
    mass_save_DC_text_label = tk.Label(GSM.Mass_roll_frame, text="Saving throw DC: ")
    mass_save_DC_text_label.grid(row=Row.increase(), column=0, sticky="w")

    GSM.Mass_save_DC_int.set(13)
    mass_save_DC_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_DC_int, width=3)
    mass_save_DC_entry.grid(row=Row.same(), column=0, sticky="w", padx=120)
    #How many monsters
    mass_save_n_monsters_text_label = tk.Label(GSM.Mass_roll_frame, text="How many monsters: ")
    mass_save_n_monsters_text_label.grid(row=Row.increase(), column=0, sticky="w")

    GSM.Mass_save_n_monsters_int.set(6)
    mass_save_n_monsters_entry = tk.Entry(GSM.Mass_roll_frame, borderwidth=2, textvariable=GSM.Mass_save_n_monsters_int, width=3)
    mass_save_n_monsters_entry.grid(row=Row.same(), column=0, sticky="w", padx=120)

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

fumble_table = ["Get distracted: Disadvantage on next attack", "Overextended Swing: Next attack on you have advantage", "Hit yourself for half dmg",
                "Hit ally for half dmg", "String Snap: If using a bow or crossbow", "Fall prone", "Ranged attack/spell: Goes in completely random direction and hits something",
                "Drop your weapon", "Misjudged Distance: enemy within 5ft can attempt a free grapple check", "Twisted Ankle: half move speed next turn",
                "Overexertion: Lose bonus action this turn", "Self doubt: Lose reaction this turn", "Ice spells: Your feet freeze, is rooted until next turn",
                "Fire spells: Lit yourself on fire, 2 turns take 1d6 dmg or action to put it out", "Ranged weapons: Drop 10 pieces of ammunition, it scatters and needs action to collect",
                "A random glass item/potion breaks and spills", "Coin pouch rips, you lose 5d8 GP", "If spell: Roll wild magic table", "Loud noise: You cause a very loud noise",
                "Panic: Become frightened of whatever you just attacked", "Sand/Mud in eyes: Become blinded until your next turn", "Drop formation: Lose 2 AC until next turn",
                "Instinct movement: You provoke instincts in enemy, they move 10ft immediately", "Nothing happens, lucky day", "You got distracted by a coin on the ground! Add 1GP to your inventory"]
TargetDmgWidgets = []

def ROLL() -> None:
    n_dice1 = GSM.Monster_dmg1_n_dice_int.get()
    dice_type1 = GSM.Monster_dmg1_dice_type_str.get()
    flat_dmg1 = GSM.Monster_dmg1_flat_int.get()
    dmg_type1 = GSM.Monster_dmg1_dmg_type_str.get()
    n_dice2 = GSM.Monster_dmg2_n_dice_int.get()
    dice_type2 = GSM.Monster_dmg2_dice_type_str.get()
    dmg_type2 = GSM.Monster_dmg2_dmg_type_str.get()
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
        TargetDmgLabel = tk.Label(GSM.ROLL_frame, text=(f"{target_name}"))
        TargetDmgLabel.grid(column=0, padx=340, row=row, sticky="w")
        TargetDmgWidgets.append(TargetDmgLabel)

        filtered_length = (lambda hits: len([hit for hit in hits if hit != "nat1"]))(sorted_hits)
        TargetDmgLabel = tk.Label(GSM.ROLL_frame, text=(f"|  {filtered_length}  |   {sorted_hits}"))
        TargetDmgLabel.grid(column=0, padx=410, row=row, sticky="w")
        TargetDmgWidgets.append(TargetDmgLabel)

        TargetDmgLabel = tk.Label(GSM.ROLL_frame, text=(f"|   {sum(dmgs1)} {dmg_type1}   |   {sum(dmgs2)} {dmg_type2}"))
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
                tohit = GSM.Monster_to_hit_int.get()
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
        display(hits, dmgs1, dmgs2, TargetObj.name_str.get())
        print(f"Total: {sum(dmgs1)} {dmg_type1}, {sum(dmgs2)} {dmg_type2}")


#3 Roll buttons
ROLL_button = tk.Button(GSM.ROLL_frame, text="ROLL", state="normal", command=ROLL, font=GSM.Title_font,
                                           padx=9, background="red")
ROLL_button.grid(row=Row.increase(), column=0, sticky="w", padx=360)

def RollMassSaveButton():
    for widget in TargetDmgWidgets:
        widget.destroy()
    TargetDmgWidgets.clear()
    passes = 0
    rolls = []
    rolltype = GSM.Roll_type_str.get()
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
        roll = roll + GSM.Mass_save_mod_int.get()
        if (roll) >= (GSM.Mass_save_DC_int.get()):
            passes += 1
        rolls.append(roll)

    rolls.sort(reverse=True)
    mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(f"Out of {GSM.Mass_save_n_monsters_int.get()} monsters, {passes} passed and {GSM.Mass_save_n_monsters_int.get()-passes} failed"))
    mass_save_results_label.grid(column=0, padx=360, row=_first_target3_row, sticky="w")
    TargetDmgWidgets.append(mass_save_results_label)

    mass_save_results_label = tk.Label(GSM.Mass_roll_frame, text=(f"Rolled with {rolltype} for: {rolls}"))
    mass_save_results_label.grid(column=0, padx=360, row=_first_target3_row+1, sticky="w")
    TargetDmgWidgets.append(mass_save_results_label)


DC_button = tk.Button(GSM.Mass_roll_frame, text="Roll save", state="normal", command=RollMassSaveButton,
                                           padx=9, background="grey")
DC_button.grid(row=Row.same(), column=0, sticky="w", padx=450)

def RollFumbleButton():
    for widget in TargetDmgWidgets:
        widget.destroy()
    TargetDmgWidgets.clear()
    fumble_label = tk.Label(GSM.Random_generator_frame, text=(f"{random.choice(fumble_table)}"))
    fumble_label.grid(column=0, padx=360, row=_first_target3_row, sticky="w")

    TargetDmgWidgets.append(fumble_label)
nat1_button = tk.Button(GSM.Random_generator_frame, text="Roll fumble", state="normal", command=RollFumbleButton,
                                           padx=9, background="grey")
nat1_button.grid(row=Row.same(), column=0, sticky="w", padx=530)

Space = tk.Label(GSM.Random_generator_frame, text="").grid(row=Row.increase(), column=0, sticky="w", padx=360)
#Target settings text
Target_settings_text_label = tk.Label(GSM.Random_generator_frame, text="Roll results", font=GSM.Title_font)
Target_settings_text_label.grid(row=Row.increase(), column=0, sticky="w", padx=360)

_first_target3_row = Row.increase()

#TODO: Add a boss section, which tracks boss cooldowns, legendary actions etc
#TODO: Add automated rolling for random encounter table. Let players import a list, saying chance of each encounter,
#   which happen per night and which per day, how often to check, and how long PC's travelled and then determine the outcome
#TODO: Add a random store. Decide "quality" of store (distribution of item rarity), how many items, read an external list, and price range as inputs


GSM.Root.mainloop()