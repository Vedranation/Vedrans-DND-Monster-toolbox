import tkinter as tk
from tkinter import ttk
from GlobalStateManager import GSM

class PlayerStats():
    def __init__(self):
        #TODO: Make a setting to pick between PP and rolling percep for mass percep check
        self.name_str: str = tk.StringVar()
        self.ac_int = tk.IntVar(value=13)
        self.n_monsters_list_ints = [tk.IntVar() for _ in GSM.Monsters_list] #Creates a list holding how many monsters attack this target

        self.monster_roll_type_against_str = tk.StringVar(value="Normal") #If dodging or is flanked

        self.adamantine: BoolVal = tk.BooleanVar(value=False) #turn crits into normal attacks
        self.perception_mod: IntVar = tk.IntVar(value=0)
        self.investigation_mod: IntVar = tk.IntVar(value=0)
        self.arcana_mod: IntVar = tk.IntVar(value=0)
        self.insight_mod: IntVar = tk.IntVar(value=0)

        self._my_button = None  # Stores his own button reference

def CreatePlayers(RelPosTargets) -> None:

    def ClearUI():
        for widget in GSM.Target_widgets_list:
            widget.destroy()
        GSM.Target_widgets_list.clear()
        RelPosTargets.reset("x")
        RelPosTargets.set("y", 60)
        GSM.Targets_canvas.delete("all")
    def CreateTargetsObject() -> None:
        ClearUI()
        column_increase = 75
        row_increase = 40

        for j, TargetObj in enumerate(GSM.Target_obj_list):
            if TargetObj.name_str.get():  # string not empty
                pass
            else:
                TargetObj.name_str.set(f"Player {j + 1}")
            TargetObj.n_monsters_list_ints = [tk.IntVar() for _ in GSM.Monsters_list]  # Regenerate proper length list holding all monsters

            # Button to open the new window
            TargetObj._my_button = tk.Button(GSM.Targets_frame, text=TargetObj.name_str.get(),
                                               command=lambda t=TargetObj: OpenPlayerWindow(t))
            button_x = RelPosTargets.reset("x")
            button_y = RelPosTargets.set("y", 130 + row_increase * j)
            TargetObj._my_button.place(x=button_x, y=button_y)
            GSM.Target_widgets_list.append(TargetObj._my_button)

            # Create horizontal lines
            hex_dict = {0: "#ffffff",
                        1: "#cfcfcf"}
            color = hex_dict[j % len(hex_dict)]  # Cycle through hex_dict values
            GSM.Targets_canvas.create_rectangle(button_x, button_y - 7, button_x + GSM._frame_width,
                                           button_y + row_increase - 7, fill=color)

            if j == 0: #Place headers down once
                for k, monster in enumerate(GSM.Monsters_list):
                    height = 80 if k % 2 else 100
                    # Calculate the x-position for centering
                    text_width = GSM.Target_font.measure(monster.name_str.get() + ":")
                    center_x = text_width // 2

                    header_label = tk.Label(GSM.Targets_frame, text=f"{monster.name_str.get()}:", font=GSM.Target_font)
                    header_label.place(x=RelPosTargets.set("x", 94 + k * column_increase - center_x),
                                       y=RelPosTargets.set("y", height))
                    GSM.Target_widgets_list.append(header_label)

            #Place spinboxes
            for k, monster in enumerate(GSM.Monsters_list):
                # Create a Spinbox for each monster, binding it to the corresponding IntVar
                target_n_monster_spinbox = ttk.Spinbox(GSM.Targets_frame, width=3,
                                                       textvariable=TargetObj.n_monsters_list_ints[k], from_=0,
                                                       to=50)
                target_n_monster_spinbox.place(x=RelPosTargets.set("x", 80 + k * column_increase),
                                               y=RelPosTargets.set("y", 130 + j * row_increase))
                GSM.Target_widgets_list.append(target_n_monster_spinbox)# packs all Target Settings widgets (input and display) into one list so it can be cleared from window


    def PreservePreviousTargets(n_targets) -> None:
        current_count = len(GSM.Target_obj_list)
        preserve_data = []

        #TODO: Copy over the preservation logic to monster creation part
        # Preserve existing data
        for target_obj in GSM.Target_obj_list:
            preserve_data.append(target_obj.name_str.get())

        # Adjust the number of PlayerStats objects
        if n_targets < current_count:
            GSM.Target_obj_list = GSM.Target_obj_list[:n_targets]
        elif n_targets > current_count:
            for i in range(current_count, n_targets):
                TargetObj = PlayerStats()
                GSM.Target_obj_list.append(TargetObj)

        # Redraw labels and entries
        for i in range(n_targets):

            # Repopulate entries with preserved data if exists
            if i < len(preserve_data):
                GSM.Target_obj_list[i].name_str.set(preserve_data[i])
        CreateTargetsObject()



    def CreatePlayerUI(TargetObj, new_window):

        # Display name
        monster_name_label = tk.Label(new_window, text="Players name:")
        monster_name_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))
        monster_name_entry = tk.Entry(new_window, borderwidth=2, textvariable=TargetObj.name_str, width=18)
        monster_name_entry.place(x=RelPosTargets.increase("x", 93), y=RelPosTargets.increase("y", 2))
        # AC
        target_ac_text_label = tk.Label(new_window, text="AC:")
        target_ac_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.increase("y", 30))
        target_ac_spinbox = ttk.Spinbox(new_window, width=3, textvariable=TargetObj.ac_int, from_=0, to=30)
        target_ac_spinbox.place(x=RelPosTargets.increase("x", 28), y=RelPosTargets.same("y"))

        # Roll type (normal, adv, disadv...)
        target_roll_type_text_label = tk.Label(new_window, text="Imposes: ")
        target_roll_type_text_label.place(x=RelPosTargets.reset("x"),
                                          y=RelPosTargets.increase("y", 30))
        target_roll_type_dropdown = tk.OptionMenu(new_window, TargetObj.monster_roll_type_against_str,
                                                  *GSM.Roll_types)
        target_roll_type_dropdown.place(x=RelPosTargets.increase("x", 60),
                                        y=RelPosTargets.increase("y", -4))
        # Adamantine
        target_adamantine_checkbox = tk.Checkbutton(new_window, text='Adamantine (Turn crits into normal hits)',
                                                variable=TargetObj.adamantine, onvalue=True, offvalue=False)
        target_adamantine_checkbox.place(x=RelPosTargets.reset("x"),
                                     y=RelPosTargets.increase("y", RelPosTargets.constant_y + 5))

        # Add a button to close the new window
        close_button = tk.Button(new_window, text="Save and exit", command=lambda: (
        new_window.destroy(), TargetObj._my_button.config(text=TargetObj.name_str.get())),
                                 background="red")
        close_button.place(x=RelPosTargets.set("x", 310), y=RelPosTargets.reset("y"))
        # Bind the Enter key to the close_button's command
        new_window.bind("<Return>", lambda event: close_button.invoke())

    def OpenPlayerWindow(player_obj) -> None:
        # Create a new Toplevel window
        new_window = tk.Toplevel(GSM.Targets_frame)
        new_window.title("Player Details")
        new_window.geometry("400x600")  # Set the size of the new window

        CreatePlayerUI(player_obj, new_window)
    'Setup'
    # Target settings text
    Target_settings_text_label = tk.Label(GSM.Targets_frame, text="Player creation", font=GSM.Title_font)
    Target_settings_text_label.place(x=RelPosTargets.reset("x"), y=RelPosTargets.reset("y"))

    # Number of targets
    n_targets_text_label = tk.Label(GSM.Targets_frame, text="How many players: ")
    n_targets_text_label.place(x=RelPosTargets.same("x"), y=RelPosTargets.increase("y", 35))
    GSM.N_targets_int.set(4)

    # Button to update targets
    GSM.Target_widgets_list = []

    n_targets_dropdown = tk.OptionMenu(GSM.Targets_frame, GSM.N_targets_int, *[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                       command=PreservePreviousTargets)
    n_targets_dropdown.place(x=RelPosTargets.set("x", 115), y=RelPosTargets.increase("y", -4))

    RelPosTargets.constant_y = 24
    _first_target_row_y = RelPosTargets.increase("y", 40)
    PreservePreviousTargets(GSM.N_targets_int.get())
