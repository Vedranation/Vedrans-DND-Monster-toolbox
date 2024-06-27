from typing import List, Union, Tuple
import tkinter as tk
from tkinter import font as tkfont  # Import tkfont for font definitions
from tkinter import ttk
class GlobalsManager:
    # GUI globals
    Root = tk.Tk()
    Root.title("Vedran's D&D monster toolbox")
    Root.iconbitmap("Gearhands-corrupted-soldier.ico")
    Root.geometry("850x620")
    Notebook = ttk.Notebook(Root)
    Notebook.place(x=10, y=10)
    _frame_width = 605
    _frame_height = 575
    # Settings tab
    Settings_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)  # seems that only first frame defines the size of all frames
    Notebook.add(Settings_frame, text="Main settings")

    # Monsters tab
    Monsters_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Monsters_frame, text="Monster creation")

    # Targets tab
    Targets_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Targets_frame, text="Target creation")

    # Mass roll tab
    Mass_roll_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Mass_roll_frame, text="Mass roll")

    # Random generator tab
    Random_generator_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Random_generator_frame, text="Random generator")

    # ROLL tab
    ROLL_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(ROLL_frame, text="ROLL")


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
    Create_targets_button = None #Button defined properly in Targets function

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
    Mass_save_roll_type_str = tk.StringVar()