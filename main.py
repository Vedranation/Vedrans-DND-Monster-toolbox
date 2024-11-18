import tkinter as tk
from tkinter import font as tkfont  # Import tkfont for font definitions
from tkinter import ttk
#import pyperclip

from GlobalStateManager import GSM
from tabs.MonsterCreation import CreateMonster
from tabs.PlayerCreation import CreatePlayers
from tabs.MassRoll import MassRoll
from tabs.Spellcasters import SpellCasters
from tabs.MainSettings import Settings
from tabs.ROLL import ROLL
from tabs.RandomGenerator import RandomGenerator
from utilities import RelativePositionTracker, Row_track, RollDice, ReturnMaxPossibleDie

#label - just text to display
#entry - type in something
#dropdown - pick one from a menu
#space - just a placeholder to move down by X amount
#n = number of something

Row = Row_track()

RelPosSettings = RelativePositionTracker()
RelPosMonsters = RelativePositionTracker()
RelPosTargets = RelativePositionTracker()
RelPosMassroll = RelativePositionTracker()
RelPosRandGen = RelativePositionTracker()
RelPosROLL = RelativePositionTracker()
RelPosSpellCast = RelativePositionTracker()

CreateMonster(RelPosMonsters)
Settings(RelPosSettings)
CreatePlayers(RelPosTargets)
MassRoll(RelPosMassroll, RelPosMonsters)
SpellCasters(RelPosSpellCast)
RandomGenerator(RelPosRandGen)
# ROLL(RelPosROLL)

#ROLL button
random_generator_text_label = tk.Label(GSM.ROLL_frame, text="Roll attacks", font=GSM.Title_font)
random_generator_text_label.place(x=RelPosROLL.reset("x"), y=RelPosROLL.reset("y"))
ROLL_button = tk.Button(GSM.ROLL_frame, text="ROLL", state="normal", command=lambda: ROLL(RelPosROLL), font=GSM.Title_font,
                                           padx=9, background="red")
ROLL_button.place(x=RelPosROLL.increase("x", 10), y=RelPosROLL.increase("y", RelPosROLL.constant_y*1.5))


#TODO: Add a boss section, which tracks boss cooldowns, legendary actions etc
#TODO: Add automated rolling for random encounter table. Let players import a list, saying chance of each encounter,
#   which happen per night and which per day, how often to check, and how long PC's travelled and then determine the outcome
#TODO: Add a random store. Decide "quality" of store (distribution of item rarity), how many items, read an external list, and price range as inputs
#TODO: Add random loot

GSM.Root.mainloop()