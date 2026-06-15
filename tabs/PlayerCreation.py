import tkinter as tk
from tkinter import ttk
from GlobalStateManager import GSM
from engine.models import PlayerData


class PlayerStats:
    def __init__(self):
        # TODO: Make a setting to pick between PP and rolling percep for mass percep check
        self.name_str: str = tk.StringVar()
        self.ac_int = tk.IntVar(value=13)
        self.max_hp_int = tk.IntVar(value=10)

        self.monster_roll_type_against_str = tk.StringVar(value="Normal")  # If dodging or is flanked

        self.adamantine = tk.BooleanVar(value=False)  # turn crits into normal attacks
        self.attack_range_ft_int = tk.IntVar(value=5)
        self.ignore_ranged_in_melee_bool = tk.BooleanVar(value=False)
        self.highlight_range_ft_int = tk.IntVar(value=5)

        self.perception_roll_type_str = tk.StringVar(value="Normal")
        self.perception_mod_int = tk.IntVar(value=0)
        self.investigation_mod_int = tk.IntVar(value=0)
        self.investigation_roll_type_str = tk.StringVar(value="Normal")
        self.arcana_mod_int = tk.IntVar(value=0)
        self.arcana_roll_type_str = tk.StringVar(value="Normal")
        self.insight_mod_int = tk.IntVar(value=0)
        self.insight_roll_type_str = tk.StringVar(value="Normal")
        self.stealth_mod_int = tk.IntVar(value=0)
        self.stealth_roll_type_str = tk.StringVar(value="Normal")
        self.passiveperception_int = tk.IntVar(value=10)
        self.initiative_mod_int = tk.IntVar(value=0)

        self._my_button = None  # Stores his own button reference

    def __str__(self):
        return self.name_str.get()

    def to_data(self) -> PlayerData:
        return PlayerData(
            name=self.name_str.get(),
            ac=self.ac_int.get(),
            max_hp=self.max_hp_int.get(),
            attack_range_ft=self.attack_range_ft_int.get(),
            ignore_ranged_in_melee=self.ignore_ranged_in_melee_bool.get(),
            highlight_range_ft=self.highlight_range_ft_int.get(),
            imposed_roll_type=self.monster_roll_type_against_str.get(),
            adamantine=self.adamantine.get(),
            skills={
                "perception": (self.perception_mod_int.get(), self.perception_roll_type_str.get()),
                "investigation": (self.investigation_mod_int.get(), self.investigation_roll_type_str.get()),
                "arcana": (self.arcana_mod_int.get(), self.arcana_roll_type_str.get()),
                "insight": (self.insight_mod_int.get(), self.insight_roll_type_str.get()),
                "stealth": (self.stealth_mod_int.get(), self.stealth_roll_type_str.get()),
            },
            passive_perception=self.passiveperception_int.get(),
            initiative_mod=self.initiative_mod_int.get(),
        )

    def from_data(self, d: PlayerData) -> None:
        self.name_str.set(d.name)
        self.ac_int.set(d.ac)
        self.max_hp_int.set(d.max_hp)
        self.attack_range_ft_int.set(d.attack_range_ft)
        self.ignore_ranged_in_melee_bool.set(d.ignore_ranged_in_melee)
        self.highlight_range_ft_int.set(d.highlight_range_ft)
        self.monster_roll_type_against_str.set(d.imposed_roll_type)
        self.adamantine.set(d.adamantine)
        self.passiveperception_int.set(d.passive_perception)
        self.initiative_mod_int.set(d.initiative_mod)
        for skill, (mod, rt) in d.skills.items():
            getattr(self, f"{skill}_mod_int").set(mod)
            getattr(self, f"{skill}_roll_type_str").set(rt)


def ClearUI(RelPosTargets):
    for widget in GSM.Target_widgets_list:
        widget.destroy()
    GSM.Target_widgets_list.clear()
    RelPosTargets.reset("x")
    RelPosTargets.set("y", 60)
    GSM.Targets_canvas.delete("all")


def CreateTargetsObject(RelPosTargets) -> None:
    ClearUI(RelPosTargets)
    row_increase = 40

    for j, TargetObj in enumerate(GSM.Target_obj_list):
        if TargetObj.name_str.get():  # string not empty
            pass
        else:
            TargetObj.name_str.set(f"Player {j + 1}")

        # Button to open the new window
        TargetObj._my_button = tk.Button(
            GSM.Targets_frame,
            text=TargetObj.name_str.get(),
            command=lambda t=TargetObj: OpenPlayerWindow(t, RelPosTargets),
        )
        button_x = RelPosTargets.reset("x")
        button_y = RelPosTargets.set("y", 130 + row_increase * j)
        TargetObj._my_button.place(x=button_x, y=button_y)
        GSM.Target_widgets_list.append(TargetObj._my_button)

        # Create horizontal lines
        hex_dict = {0: "#ffffff", 1: "#cfcfcf"}
        color = hex_dict[j % len(hex_dict)]  # Cycle through hex_dict values
        GSM.Targets_canvas.create_rectangle(
            button_x, button_y - 7, button_x + GSM._frame_width, button_y + row_increase - 7, fill=color
        )


def CreatePlayerUI(TargetObj, new_window, RelPosTargets):

    target_title_label = tk.Label(new_window, text="Combat details:", font=GSM.Title_font)
    target_title_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))
    # Display name
    target_name_label = tk.Label(new_window, text="Players name:", font=GSM.Target_font)
    target_name_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
    target_name_entry = tk.Entry(new_window, borderwidth=2, textvariable=TargetObj.name_str, width=18)
    target_name_entry.place(x=RelPosTargets.increase("x", 93), y=RelPosTargets.increase("y", 2))
    # AC
    target_ac_text_label = tk.Label(new_window, text="AC:", font=GSM.Target_font)
    target_ac_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
    target_ac_spinbox = ttk.Spinbox(new_window, width=3, textvariable=TargetObj.ac_int, from_=0, to=30)
    target_ac_spinbox.place(x=RelPosTargets.increase("x", 28), y=RelPosTargets.same("y"))
    # Max HP
    target_maxhp_text_label = tk.Label(new_window, text="Max HP:", font=GSM.Target_font)
    target_maxhp_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 28))
    target_maxhp_spinbox = ttk.Spinbox(new_window, width=5, textvariable=TargetObj.max_hp_int, from_=0, to=9999)
    target_maxhp_spinbox.place(x=RelPosTargets.increase("x", 55), y=RelPosTargets.same("y"))
    # Attack range
    target_range_label = tk.Label(new_window, text="Attack range (ft):", font=GSM.Target_font)
    target_range_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 28))
    target_range_spinbox = ttk.Spinbox(
        new_window, width=4, textvariable=TargetObj.attack_range_ft_int, from_=5, to=600, increment=5
    )
    target_range_spinbox.place(x=RelPosTargets.increase("x", 110), y=RelPosTargets.same("y"))
    target_ignore_melee_checkbox = tk.Checkbutton(
        new_window, text="Ignore ranged-in-melee penalty",
        variable=TargetObj.ignore_ranged_in_melee_bool, onvalue=True, offvalue=False,
    )
    target_ignore_melee_checkbox.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 24))
    # Board highlight range
    target_hl_range_label = tk.Label(new_window, text="Board highlight (ft):", font=GSM.Target_font)
    target_hl_range_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 24))
    target_hl_range_spinbox = ttk.Spinbox(
        new_window, width=4, textvariable=TargetObj.highlight_range_ft_int, from_=5, to=600, increment=5
    )
    target_hl_range_spinbox.place(x=RelPosTargets.increase("x", 115), y=RelPosTargets.same("y"))

    # Roll type (normal, adv, disadv...)
    target_roll_type_text_label = tk.Label(new_window, text="Imposes:", font=GSM.Target_font)
    target_roll_type_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
    target_roll_type_dropdown = tk.OptionMenu(new_window, TargetObj.monster_roll_type_against_str, *GSM.Roll_types)
    target_roll_type_dropdown.place(x=RelPosTargets.increase("x", 60), y=RelPosTargets.increase("y", -4))

    # Adamantine
    target_adamantine_checkbox = tk.Checkbutton(
        new_window,
        text="Adamantine (Turn crits into normal hits)",
        variable=TargetObj.adamantine,
        onvalue=True,
        offvalue=False,
    )
    target_adamantine_checkbox.place(
        x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", RelPosTargets.constant_y + 5)
    )

    "Skills"

    def Skills(new_window, RelPosTargets) -> None:
        # Just grouped skills so they can be compressed
        target_title_label = tk.Label(new_window, text="Skill modifiers:", font=GSM.Title_font)
        target_title_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 40))
        spinbox_x_distance = 80
        # Perception
        target_perception_text_label = tk.Label(new_window, text="Perception:")
        target_perception_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_perception_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=TargetObj.perception_mod_int, from_=-10, to=20
        )
        target_perception_spinbox.place(
            x=RelPosTargets.increase("x", spinbox_x_distance), y=RelPosTargets.increase("y", 2)
        )
        target_perception_roll_type_dropdown = tk.OptionMenu(
            new_window, TargetObj.perception_roll_type_str, *GSM.Roll_types
        )
        target_perception_roll_type_dropdown.place(x=RelPosTargets.increase("x", 40), y=RelPosTargets.increase("y", -4))
        # Investigation
        target_investigation_text_label = tk.Label(new_window, text="Investigation:")
        target_investigation_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_investigation_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=TargetObj.investigation_mod_int, from_=-10, to=20
        )
        target_investigation_spinbox.place(
            x=RelPosTargets.increase("x", spinbox_x_distance), y=RelPosTargets.increase("y", 2)
        )
        target_investigation_roll_type_dropdown = tk.OptionMenu(
            new_window, TargetObj.investigation_roll_type_str, *GSM.Roll_types
        )
        target_investigation_roll_type_dropdown.place(
            x=RelPosTargets.increase("x", 40), y=RelPosTargets.increase("y", -4)
        )
        # Arcana
        target_arcana_text_label = tk.Label(new_window, text="Arcana:")
        target_arcana_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_arcana_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=TargetObj.arcana_mod_int, from_=-10, to=20
        )
        target_arcana_spinbox.place(x=RelPosTargets.increase("x", spinbox_x_distance), y=RelPosTargets.increase("y", 2))
        target_arcana_roll_type_dropdown = tk.OptionMenu(new_window, TargetObj.arcana_roll_type_str, *GSM.Roll_types)
        target_arcana_roll_type_dropdown.place(x=RelPosTargets.increase("x", 40), y=RelPosTargets.increase("y", -4))
        # Insight
        target_insight_text_label = tk.Label(new_window, text="Insight:")
        target_insight_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_insight_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=TargetObj.insight_mod_int, from_=-10, to=20
        )
        target_insight_spinbox.place(
            x=RelPosTargets.increase("x", spinbox_x_distance), y=RelPosTargets.increase("y", 2)
        )
        target_insight_roll_type_dropdown = tk.OptionMenu(new_window, TargetObj.insight_roll_type_str, *GSM.Roll_types)
        target_insight_roll_type_dropdown.place(x=RelPosTargets.increase("x", 40), y=RelPosTargets.increase("y", -4))
        # Stealth
        target_stealth_text_label = tk.Label(new_window, text="Stealth:")
        target_stealth_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_stealth_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=TargetObj.stealth_mod_int, from_=-10, to=20
        )
        target_stealth_spinbox.place(
            x=RelPosTargets.increase("x", spinbox_x_distance), y=RelPosTargets.increase("y", 2)
        )
        target_stealth_roll_type_dropdown = tk.OptionMenu(new_window, TargetObj.stealth_roll_type_str, *GSM.Roll_types)
        target_stealth_roll_type_dropdown.place(x=RelPosTargets.increase("x", 40), y=RelPosTargets.increase("y", -4))
        # Passive perception
        target_passiveperception_text_label = tk.Label(new_window, text="Passive perception:")
        target_passiveperception_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_passiveperception_spinbox = ttk.Spinbox(
            new_window, width=3, textvariable=TargetObj.passiveperception_int, from_=0, to=25
        )
        target_passiveperception_spinbox.place(
            x=RelPosTargets.increase("x", spinbox_x_distance * 1.5), y=RelPosTargets.increase("y", 2)
        )

    Skills(new_window, RelPosTargets)

    target_init_label = tk.Label(new_window, text="Initiative mod:")
    target_init_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
    ttk.Spinbox(new_window, width=3, textvariable=TargetObj.initiative_mod_int, from_=-10, to=20).place(
        x=RelPosTargets.increase("x", 90), y=RelPosTargets.increase("y", 2)
    )

    # Add a button to close the new window
    def chooseButtonColor(targetObj) -> str:
        # Recolours button color depending on Advantage/Disadvantage
        if (
            targetObj.monster_roll_type_against_str.get() == "Advantage"
            or targetObj.monster_roll_type_against_str.get() == "Super Advantage"
        ):
            background = "#ff6661"
        elif (
            targetObj.monster_roll_type_against_str.get() == "Disadvantage"
            or targetObj.monster_roll_type_against_str.get() == "Super Disadvantage"
        ):
            background = "#80f05b"
        else:
            background = "SystemButtonFace"
        return background

    close_button = tk.Button(
        new_window,
        text="Save and exit",
        command=lambda: (
            new_window.destroy(),
            TargetObj._my_button.config(text=TargetObj.name_str.get(), background=chooseButtonColor(TargetObj)),
        ),
        background="red",
    )
    close_button.place(x=RelPosTargets.set("x", 310), y=RelPosTargets.reset("y"))
    # Bind the Enter key to the close_button's command
    new_window.bind("<Return>", lambda event: close_button.invoke())


def OpenPlayerWindow(player_obj, RelPosTargets) -> None:
    # Create a new Toplevel window
    new_window = tk.Toplevel(GSM.Targets_frame)
    new_window.title("Player Details")
    new_window.geometry("400x700")

    CreatePlayerUI(player_obj, new_window, RelPosTargets)


def PreservePreviousTargets(n_targets, RelPosTargets) -> None:
    current_count = len(GSM.Target_obj_list)
    preserve_data = []

    # Preserve existing data
    for target_obj in GSM.Target_obj_list:
        preserve_data.append(target_obj.name_str.get())

    # Adjust the number of PlayerStats objects
    if n_targets < current_count:
        GSM.Target_obj_list = GSM.Target_obj_list[:n_targets]
    elif n_targets > current_count:
        for i in range(current_count, n_targets):
            targetObj = PlayerStats()
            GSM.Target_obj_list.append(targetObj)

    # Redraw labels and entries
    for i in range(n_targets):

        # Repopulate entries with preserved data if exists
        if i < len(preserve_data):
            GSM.Target_obj_list[i].name_str.set(preserve_data[i])
    CreateTargetsObject(RelPosTargets)


def CreatePlayers(RelPosTargets) -> None:
    "Setup"
    # Target settings text
    Target_settings_text_label = tk.Label(GSM.Targets_frame, text="Player creation", font=GSM.Title_font)
    Target_settings_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))

    # Number of targets
    n_targets_text_label = tk.Label(GSM.Targets_frame, text="How many players: ")
    n_targets_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.increase("y", 35))

    # Button to update targets
    GSM.Target_widgets_list = []

    n_targets_dropdown = tk.OptionMenu(
        GSM.Targets_frame,
        GSM.N_targets_int,
        *[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        command=lambda value: PreservePreviousTargets(value, RelPosTargets),
    )
    n_targets_dropdown.place(x=RelPosTargets.set("x", 115), y=RelPosTargets.increase("y", -4))

    RelPosTargets.constant_y = 24
    _first_target_row_y = RelPosTargets.increase("y", 40)
    PreservePreviousTargets(GSM.N_targets_int.get(), RelPosTargets)
