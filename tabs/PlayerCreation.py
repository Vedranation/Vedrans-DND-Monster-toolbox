import tkinter as tk
from tkinter import ttk
from GlobalStateManager import GSM

class PlayerStats():
    def __init__(self):
        #TODO: Make a setting to pick between PP and rolling percep for mass percep check
        self.name_str: str = tk.StringVar()
        self.ac_int = tk.IntVar(value=13)
        self.n_monsters_1_int = tk.IntVar(value=1)
        self.n_monsters_2_int = tk.IntVar(value=0)
        self.n_monsters_3_int = tk.IntVar(value=0)
        self.monster_roll_type_against_str = tk.StringVar(value="Normal") #If dodging or is flanked

        self.adamantine: int = False #turn crits into normal attacks

def CreatePlayers(RelPosTargets) -> None:
    # Target settings text
    Target_settings_text_label = tk.Label(GSM.Targets_frame, text="Target settings", font=GSM.Title_font)
    Target_settings_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))

    #Number of targets
    n_targets_text_label = tk.Label(GSM.Targets_frame, text="How many targets: ")
    n_targets_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.increase("y", 35))
    GSM.N_targets_int.set(4)

    # Button to update targets
    GSM.Target_widgets_list = []

    def CreateTargetsButton() -> None:
        for widget in GSM.Target_widgets_list:
            widget.destroy()
        GSM.Target_widgets_list.clear()
        current_create_targets_button_xy = GSM.Create_targets_button.place_info()
        current_create_targets_button_x = int(current_create_targets_button_xy["x"])
        current_create_targets_button_y = int(current_create_targets_button_xy["y"])
        RelPosTargets.set("x", current_create_targets_button_x)
        RelPosTargets.set("y", current_create_targets_button_y+20)
        #TODO: Wanna change this to be vertical (put monster names, AC etc ABOVE inputs to save a lot of space, make it tabular)
        for i, TargetObj in enumerate(GSM.Target_obj_list):

            if TargetObj.name_str.get():  # string not empty
                pass
            else:
                TargetObj.name_str.set(f"Target {i + 1}")
            RelPosTargets.set("x", current_create_targets_button_x)
            RelPosTargets.increase("y", 25)
            #Display name
            target_text_label = tk.Label(GSM.Targets_frame, text=f"{TargetObj.name_str.get()}:", font=GSM.Target_font)
            target_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.same("y"))
            GSM.Target_widgets_list.append(target_text_label)
            #AC
            target_ac_text_label = tk.Label(GSM.Targets_frame, text="AC:")
            target_ac_text_label.place(x=RelPosTargets.increase("x", 90), y=RelPosTargets.same("y"))
            target_ac_entry = tk.Entry(GSM.Targets_frame, borderwidth=2, textvariable=TargetObj.ac_int, width=2)
            target_ac_entry.place(x=RelPosTargets.increase("x", 28), y=RelPosTargets.same("y"))
            GSM.Target_widgets_list.append(target_ac_text_label)
            GSM.Target_widgets_list.append(target_ac_entry)

            # Roll type (normal, adv, disadv...)
            #FIXME: Allignment issue, fix it when making it tabular
            target_roll_type_text_label = tk.Label(GSM.Targets_frame, text="Imposes: ")
            target_roll_type_text_label.place(x=RelPosTargets.increase("x", 30),
                                              y=RelPosTargets.same("y"))
            target_roll_type_dropdown = tk.OptionMenu(GSM.Targets_frame, TargetObj.monster_roll_type_against_str, *GSM.Roll_types)
            target_roll_type_dropdown.place(x=RelPosTargets.increase("x", 60),
                                            y=RelPosTargets.increase("y", -4))
            GSM.Target_widgets_list.append(target_roll_type_text_label)
            GSM.Target_widgets_list.append(target_roll_type_dropdown)

            #N monsters (1-3)
            for i, monster in enumerate(GSM.Monsters_list):
                column_increase = 45
                target_n_monsters_text_label = tk.Label(GSM.Targets_frame, text=f"{monster.name_str.get()}:")


                if i == 0:
                    target_n_monster_spinbox = ttk.Spinbox(GSM.Targets_frame, width=3, textvariable=TargetObj.n_monsters_1_int, from_=0, to=50)
                    target_n_monsters_text_label.place(x=RelPosTargets.increase("x", 70), y=RelPosTargets.same("y"))
                elif i == 1:
                    target_n_monster_spinbox = ttk.Spinbox(GSM.Targets_frame, from_=0, to=50, textvariable=TargetObj.n_monsters_2_int, width=3)
                    target_n_monsters_text_label.place(x=RelPosTargets.increase("x", column_increase), y=RelPosTargets.same("y"))
                else:
                    target_n_monster_spinbox = ttk.Spinbox(GSM.Targets_frame, from_=0, to=50, textvariable=TargetObj.n_monsters_3_int, width=3)
                    target_n_monsters_text_label.place(x=RelPosTargets.increase("x", column_increase), y=RelPosTargets.same("y"))

                target_n_monster_spinbox.place(x=RelPosTargets.increase("x", 90), y=RelPosTargets.same("y"))
                #TODO: Add the target individual rolltype
                GSM.Target_widgets_list.append(target_n_monsters_text_label)
                GSM.Target_widgets_list.append(target_n_monster_spinbox)# packs all Target Settings widgets (input and display) into one list so it can be cleared from window


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
    _first_target_row_y = RelPosTargets.increase("y", 40)
    DrawTargetInputNameBoxes(GSM.N_targets_int.get())
