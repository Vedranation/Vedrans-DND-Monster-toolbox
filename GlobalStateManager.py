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
    _frame_width = 825
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

    # Mass roll tab
    Spell_caster_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Spell_caster_frame, text="Spell casters")

    # Random generator tab
    Random_generator_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Random_generator_frame, text="Random generator")

    # ROLL tab
    ROLL_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height, )
    Notebook.add(ROLL_frame, text="ROLL")


    Roll_types = ["Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"]
    Dmg_types = ["bludgeoning", "magic bludgeoning", "piercing", "magic piercing", "slashing",
                 "magic slashing", "acid", "cold", "fire", "force", "lightning", "thunder", "necrotic",
                 "poison", "psychic", "radiant"]
    Dice_types = ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]
    Saving_throw_types = ["STR", "DEX", "CON", "WIS", "INT", "CHAR"]

    Title_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
    Target_font = tkfont.Font(family="Helvetica", size=9, weight="bold")


    #Globals for running the program
    Meets_it_beats_it_bool = tk.BooleanVar(value=False)
    Crits_double_dmg_bool = tk.BooleanVar(value=True)
    Crits_extra_die_is_max_bool = tk.BooleanVar(value=False)
    Crits_always_hit_bool = tk.BooleanVar(value=True)
    Nat1_always_miss_bool = tk.BooleanVar(value=True)
    Adv_combine_bool = tk.BooleanVar(value=False)

    Roll_type_str = tk.StringVar()
    N_targets_int = tk.IntVar()

    Target_obj_list: List[str] = []
    Target_widgets_list: List[str] = []

    #Target related variables
    Create_targets_button = None #Button defined properly in Targets function

    #Monster creation variables
    Monsters_list = []
    Monsters_widgets_list = []
    N_monsters_int = tk.IntVar(value=1)

    Monster_dmg1_extra_text_label2 = None #the text that appears next line depending on your choice of dmg type
    Monster_dmg2_extra_text_label2 = None

    #Spell casters variables
    N_casters_int = tk.IntVar(value=1)
    Spell_casters_widgets_list = []
    Spell_checkboxes_dict = {}

    #Mass save variables
    Mass_save_mod_int = tk.IntVar()
    Mass_save_DC_int = tk.IntVar()
    Mass_save_n_monsters_int = tk.IntVar()
    Mass_save_roll_type_str = tk.StringVar()
    Results_random_gen_widgets_to_clear = []

    #ROLL globals
    Results_display_widgets_list = []