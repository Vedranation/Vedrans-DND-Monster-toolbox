import tkinter as tk
from tkinter import font as tkfont  # Import tkfont for font definitions
from tkinter import ttk

import tabs.PlayerCreation
#import pyperclip

from GlobalStateManager import GSM
from tabs.MonsterCreation import CreateMonster
from tabs.PlayerCreation import CreatePlayers
from tabs.MassRoll import MassRoll
from tabs.Spellcasters import SpellCasters
from tabs.MainSettings import Settings
from tabs.Attack import Attack
from tabs.RandomGenerator import RandomGenerator
from utilities import Row_track, RollDice, ReturnMaxPossibleDie

#label - just text to display
#entry - type in something
#dropdown - pick one from a menu
#space - just a placeholder to move down by X amount
#n = number of something

def On_tab_change(event):
    #This procs every tab change, for resetting dropdown lists
    selected_tab = GSM.Notebook.tab(GSM.Notebook.index("current"), "text")
    if selected_tab == "Attacks":
        list_of_widgets = GSM.OnTab_Attack_reset_widgets.copy()
        GSM.OnTab_Attack_reset_widgets.clear()
        for package in list_of_widgets:
            #package = [widget_obj, widget_x, widget_y, widget_identifier]
            widget = package[0]
            x = package[1]
            y = package[2]
            identifier = package[3]

            # purge old widget from all lists so garbage collecter reclaims it
            widget.destroy()

            if identifier == "attacker_dropdown":
                # Check if the selected attacker exists in the monsters list by comparing strings
                if GSM.OneAttacker_str.get() not in [str(monster) for monster in GSM.Monsters_list]:
                    # If the selected monster was removed, select the first one
                    GSM.OneAttacker_str.set(str(GSM.Monsters_list[0]))
                new_widget = tk.OptionMenu(GSM.Attack_frame, GSM.OneAttacker_str, *GSM.Monsters_list)
            elif identifier == "defender_dropdown":
                if GSM.OneDefender_str.get() not in [str(obj) for obj in (*GSM.Monsters_list, *GSM.Target_obj_list, "None")]:
                    GSM.OneDefender_str.set("None")
                new_widget = tk.OptionMenu(GSM.Attack_frame, GSM.OneDefender_str, *[*GSM.Monsters_list, *GSM.Target_obj_list, "None"])

            #make a new widget
            new_widget.place(x=x, y=y)
            #Re-add it to relevant lists
            GSM.OnTab_Attack_reset_widgets.append([new_widget, x, y, identifier])
            GSM.Results_display_widgets_list.append(new_widget)

    elif selected_tab == "Skills/Saves":
        list_of_widgets = GSM.OnTab_MassSaves_reset_widgets.copy()
        GSM.OnTab_MassSaves_reset_widgets.clear()
        for package in list_of_widgets:

            widget = package[0]
            x = package[1]
            y = package[2]
            identifier = package[3]

            # purge old widget from all lists so garbage collecter reclaims it
            widget.destroy()

            if identifier == "which_monster":
                # Check if the selected attacker exists in the monsters list by comparing strings
                if GSM.Quick_save_which_mob_str.get() not in [str(monster) for monster in GSM.Monsters_list]:
                    # If the selected monster was removed, select the first one
                    GSM.Quick_save_which_mob_str.set(str(GSM.Monsters_list[0]))
                new_widget = tk.OptionMenu(GSM.Mass_roll_frame, GSM.Quick_save_which_mob_str, *GSM.Monsters_list)

            # make a new widget
            new_widget.place(x=x, y=y)
            # Re-add it to relevant lists
            GSM.OnTab_MassSaves_reset_widgets.append([new_widget, x, y, identifier])


GSM.Notebook.bind("<<NotebookTabChanged>>", On_tab_change)

Settings(GSM.RelPosSettings)
CreatePlayers(GSM.RelPosTargets)
CreateMonster(GSM.RelPosMonsters) #FIXME: Switching pos of monster and target fucks with n_monsters dropdown at PlayerCreation
MassRoll(GSM.RelPosMassroll, GSM.RelPosMonsters)
SpellCasters(GSM.RelPosSpellCast)
RandomGenerator(GSM.RelPosRandGen)
Attack(GSM.RelPosROLL)

#TODO: Initiative tracker
#TODO: Add a boss section, which tracks boss cooldowns, legendary actions etc
#TODO: Add automated rolling for random encounter table. Let players import a list, saying chance of each encounter,
#   which happen per night and which per day, how often to check, and how long PC's travelled and then determine the outcome
#TODO: Add a random store. Decide "quality" of store (distribution of item rarity), how many items, read an external list, and price range as inputs
#TODO: Add random loot

GSM.Root.mainloop()