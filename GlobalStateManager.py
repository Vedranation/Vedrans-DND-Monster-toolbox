from typing import List, Union, Tuple
import tkinter as tk
from tkinter import font as tkfont  # Import tkfont for font definitions
class GlobalsManager:
    root = tk.Tk()
    #Globals for modification
    root.title("Vedran's D&D monster toolbox")
    root.geometry("850x580")

    Roll_types = ["Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"]
    Dmg_types = ["bludgeoning", "magic bludgeoning", "piercing", "magic piercing", "slashing",
                 "magic slashing", "acid", "cold", "fire", "force", "lightning", "thunder", "necrotic",
                 "poison", "psychic", "radiant"]
    Dice_types = ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]

    Title_font = tkfont.Font(family="Helvetica", size=12, weight="bold")


    #Globals for running the program
    Meets_it_beats_it_bool = tk.BooleanVar()
    Crits_double_dmg_bool = tk.BooleanVar()
    Crits_always_hit_bool = tk.BooleanVar()
    Nat1_always_miss_bool = tk.BooleanVar()

    Roll_type_str = tk.StringVar()
    N_targets_int = tk.IntVar()

    Target_obj_list: List[str] = []
    Target_related_widgets: List[str] = []

    #Target related variables


    #Monster creation variables
    Monster_n_attacks_int = tk.IntVar()
    Monster_to_hit_int = tk.IntVar()
    Monster_dmg1_n_dice_int = tk.IntVar()
    Monster_dmg1_dice_type_str = tk.StringVar()
    Monster_dmg1_dmg_type_str = tk.StringVar()
    Monster_dmg1_flat_int = tk.IntVar()
    Monster_dmg2_n_dice_int = tk.IntVar()
    Monster_dmg2_dice_type_str = tk.StringVar()
    Monster_dmg2_dmg_type_str = tk.StringVar()

    #Mass save variables
    Mass_save_mod_int = tk.IntVar()
    Mass_save_DC_int = tk.IntVar()
    Mass_save_n_monsters_int = tk.IntVar()