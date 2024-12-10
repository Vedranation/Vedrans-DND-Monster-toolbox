import tkinter as tk
from GlobalStateManager import GSM

# FIXME: Bug when saving and loading makes it unable to delete checkboxes
# TODO: Merge this into monster creation
# TODO: Add a list of spells to store for easy retrieval
def CreateSpellCasters(n_casters: int, RelPosSpellCast) -> None:
    for widget in GSM.Spell_casters_widgets_list:
        widget.destroy()
    GSM.Spell_casters_widgets_list.clear()
    GSM.Spell_checkboxes_dict = {i: [] for i in range(n_casters)}  # Dictionary to hold checkboxes for each caster

    def DrawSpellBoxes(caster_lv, index):
        base_y = 200  # Starting y position for checkboxes
        column_offset = index * 165  # Position offset for each caster column
        print(caster_lv, index)
        # Remove old checkboxes if any
        for checkbox in GSM.Spell_checkboxes_dict.get(index, []):
            checkbox.destroy()
        GSM.Spell_checkboxes_dict[index] = []

        if caster_lv >= 1:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 1:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.set("y", 145))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 2:
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 3:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 2:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 4:
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 5:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 3:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 6:
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 7:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 4:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 8:
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 9:
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)

            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 5:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 10:
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.increase("x", 20) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 11:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 6:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 13:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 7:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 15:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 8:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 17:
            spell_text_label = tk.Label(GSM.Spell_caster_frame, text="Level 9:")
            spell_text_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_text_label)

            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 18:  # Specijalni RelPos X i Y jer idu unatrad
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 87) + column_offset, y=RelPosSpellCast.increase("y", -80))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv >= 19:  # Specijalni RelPos X i Y jer idu unatrad
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 67) + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)
        if caster_lv == 20:  # Specijalni RelPos X i Y jer idu unatrad
            spell_checkbox = tk.Checkbutton(GSM.Spell_caster_frame)
            spell_checkbox.place(x=RelPosSpellCast.set("x", 67) + column_offset, y=RelPosSpellCast.increase("y", 20))
            GSM.Spell_checkboxes_dict[index].append(spell_checkbox)

    for i in range(GSM.N_casters_int.get()):
        column_offset = i * 165
        caster_lv = tk.IntVar(value=1)

        caster_name_label = tk.Label(GSM.Spell_caster_frame, text="Name:")
        caster_name_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.set("y", 80))
        caster_name_entry = tk.Entry(GSM.Spell_caster_frame, borderwidth=2, width=15)
        caster_name_entry.place(x=RelPosSpellCast.increase("x", 47) + column_offset, y=RelPosSpellCast.same("y"))
        caster_lv_label = tk.Label(GSM.Spell_caster_frame, text="Spellcasting level:")
        caster_lv_label.place(x=RelPosSpellCast.reset("x") + column_offset, y=RelPosSpellCast.increase("y", 35))
        caster_lv_dropdown = tk.OptionMenu(GSM.Spell_caster_frame, caster_lv,
                                           *[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                                           command=lambda lv, idx=i: DrawSpellBoxes(lv, idx))
        caster_lv_dropdown.place(x=RelPosSpellCast.increase("x", 97) + column_offset,
                                 y=RelPosSpellCast.increase("y", -4))
        GSM.Spell_casters_widgets_list.append(caster_name_label)
        GSM.Spell_casters_widgets_list.append(caster_name_entry)
        GSM.Spell_casters_widgets_list.append(caster_lv_label)
        GSM.Spell_casters_widgets_list.append(caster_lv_dropdown)

def SpellCasters(RelPosSpellCast) -> None:
    # Spell casters title
    SpellCasters_text_label = tk.Label(GSM.Spell_caster_frame, text="Spell casters", font=GSM.Title_font)
    SpellCasters_text_label.place(x=RelPosSpellCast.reset("x"), y=RelPosSpellCast.reset("y"))


    # Number of casters
    n_casters_text_label = tk.Label(GSM.Spell_caster_frame, text="How many spell casters: ")
    n_casters_text_label.place(x=RelPosSpellCast.same("x"), y=RelPosSpellCast.increase("y", 35))
    n_casters_dropdown = tk.OptionMenu(GSM.Spell_caster_frame, GSM.N_casters_int, *[1, 2, 3, 4, 5], command=lambda value: CreateSpellCasters(value, RelPosSpellCast))
    n_casters_dropdown.place(x=RelPosSpellCast.increase("x", 135), y=RelPosSpellCast.increase("y", -4))