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
from tabs.Attack import Attack
from tabs.RandomGenerator import RandomGenerator
from utilities import Row_track, RollDice, ReturnMaxPossibleDie

#label - just text to display
#entry - type in something
#dropdown - pick one from a menu
#space - just a placeholder to move down by X amount
#n = number of something

Row = Row_track()

Settings(GSM.RelPosSettings)
CreateMonster(GSM.RelPosMonsters)
CreatePlayers(GSM.RelPosTargets)
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