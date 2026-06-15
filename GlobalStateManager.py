import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from engine.board import Board
from utilities import RelativePositionTracker


class GlobalsManager:
    # GUI globals
    Root = tk.Tk()
    Root.title("Vedran's D&D monster toolbox")
    Root.iconbitmap("Gearhands-corrupted-soldier.ico")
    Root.geometry("850x645")
    Notebook = ttk.Notebook(Root)
    Notebook.place(x=10, y=10)
    _frame_width = 825
    _frame_height = 600

    # Monsters tab
    Monsters_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Monsters_frame, text="Monster creation")

    # Player (Targets) tab
    Targets_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Targets_frame, text="Player creation")
    Targets_canvas = tk.Canvas(Targets_frame, width=_frame_width, height=_frame_height)
    Targets_canvas.pack(fill="both", expand=True)

    # Attack tab
    Attack_frame = ttk.Frame(
        Notebook,
        width=_frame_width,
        height=_frame_height,
    )
    Notebook.add(Attack_frame, text="Attacks")

    # Mass roll tab
    Mass_roll_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Mass_roll_frame, text="Skills/Saves")

    # Spell casters tab
    Spell_caster_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Spell_caster_frame, text="Spell casters")

    # Random generator tab
    Random_generator_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Random_generator_frame, text="Random generator")

    # Settings tab
    Settings_frame = ttk.Frame(
        Notebook, width=_frame_width, height=_frame_height
    )  # seems that only first frame defines the size of all frames
    Notebook.add(Settings_frame, text="Main settings")

    # Battle Board tab
    Board_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Board_frame, text="Battle Board")

    # Initiative Tracker tab
    Initiative_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Initiative_frame, text="Initiative")

    # Search tab (voice + fuzzy lookup of local library / 5e.tools)
    Search_frame = ttk.Frame(Notebook, width=_frame_width, height=_frame_height)
    Notebook.add(Search_frame, text="Search")

    Roll_types = ["Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"]
    Dmg_types = [
        "bludgeoning",
        "magic bludgeoning",
        "piercing",
        "magic piercing",
        "slashing",
        "magic slashing",
        "acid",
        "cold",
        "fire",
        "force",
        "lightning",
        "thunder",
        "necrotic",
        "poison",
        "psychic",
        "radiant",
    ]
    Dice_types = ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]
    Saving_throw_types = ["STR", "DEX", "CON", "WIS", "INT", "CHA"]

    # Fonts
    Title_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
    Target_font = tkfont.Font(family="Helvetica", size=9, weight="bold")

    # Globals for running the program
    Meets_it_beats_it_bool = tk.BooleanVar(value=False)
    Crits_double_dmg_bool = tk.BooleanVar(value=True)
    Crits_extra_die_is_max_bool = tk.BooleanVar(value=False)
    Nat1_always_miss_bool = tk.BooleanVar(value=True)
    Adv_combine_bool = tk.BooleanVar(value=False)
    Adv_mode = tk.StringVar(value="RAW")  # "RAW" | "Arithmetic"
    Auto_disable_zero_hp_bool = tk.BooleanVar(value=True)
    Ignore_resistances_bool = tk.BooleanVar(value=False)  # ignore monster damage resist/immunity

    Roll_type_str = tk.StringVar()

    N_targets_int = tk.IntVar(value=4)
    Target_obj_list: list = []
    Target_widgets_list: list = []

    # Target related variables
    Create_targets_button = None  # Button defined properly in Targets function

    # Monster creation variables
    Monster_obj_list: list = []  # Holds the created monster objects
    Monsters_widgets_list = []
    N_monsters_int = tk.IntVar(value=2)

    Monster_dmg1_extra_text_label2 = None  # the text that appears next line depending on your choice of dmg type
    Monster_dmg2_extra_text_label2 = None

    # Spell casters variables
    N_casters_int = tk.IntVar(value=1)
    Spell_casters_widgets_list = []       # kept for compatibility, no longer used
    Spell_checkboxes_dict: dict = {}      # {index: [slot checkbox/label widgets]}
    Spell_slot_vars: dict = {}            # {index: {spell_level: [tk.BooleanVar, ...]}}
    Spell_caster_header_widgets: dict = {}  # {index: [header widgets]}
    Spell_caster_level_vars: dict = {}    # {index: tk.IntVar}
    Spell_caster_name_entries: dict = {}  # {index: tk.Entry}
    Spell_caster_spells: dict = {}        # {index: {spell_level: [spell_name, ...]}}
    Spell_library: list = []              # [{name, level, school, casting_time, component_v/s/m, description}]

    # Mass save variables
    Quick_monster_save_rolltype_str = tk.StringVar(value="Monster default")
    Quick_save_which_mob_str = tk.StringVar()
    Quick_save_which_save = tk.StringVar(value="STR")
    Results_quick_mob_save_widgets_to_clear = []
    OnTab_MassSaves_reset_widgets = []  # Widgets to be remade when tab changes to Saves (dropdowns)

    WhichSkillToCheck = tk.StringVar(value="Perception")
    SkillCheckDC = tk.IntVar(value=15)
    PartySkillCheckResults = []

    # Attack globals
    Results_display_widgets_list = []
    OneAttacker_str = tk.StringVar()
    OneDefender_str = tk.StringVar()
    OneAttack_spec_str = tk.StringVar()  # Selected attack spec name for single-attack roll
    Override_roll_type_str = tk.StringVar()  # Overrides all rolltypes for OneAttackRoll
    OneAttackLogResults = []  # Stores all OneAttack results

    OnTab_Attack_reset_widgets = []  # Widgets to be remade when tab changes to Attack (dropdowns)

    # Callable set by MassRoll — lets BoardTab load monster groups into the mass save section
    Load_mass_saves: object = None

    # Save/Load widgets which need to be kept track off
    Load_widgets_mainsettings_dict = {}

    # Board settings
    Board_diagonal_mode = tk.StringVar(value="standard")   # "standard" | "5-10-5"
    Board_flank_geometry = tk.StringVar(value="hard")      # "hard" | "soft"
    Board_flank_benefit = tk.StringVar(value="advantage")  # "advantage" | "+2"
    Board_range_mode = tk.StringVar(value="warn")          # "warn" | "block"
    # Live board state — populated by BoardTab
    Board_state: Board = Board()

    # Widget position trackers
    RelPosSettings = RelativePositionTracker()
    RelPosSpellCast = RelativePositionTracker()
    RelPosMonsters = RelativePositionTracker()
    RelPosTargets = RelativePositionTracker()
    RelPosMassroll = RelativePositionTracker()
    RelPosRandGen = RelativePositionTracker()
    RelPosROLL = RelativePositionTracker()


GSM = GlobalsManager()
