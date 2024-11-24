from GlobalStateManager import GSM
import tkinter as tk
from tkinter import ttk
from utilities import RollDice, ReturnMaxPossibleDie

def ROLL(RelPosROLL) -> None:
    #TODO: Add a "Copy results to clipboard" button!
    print("")
    print("NEW ROLL")
    RelPosROLL.reset("x")
    RelPosROLL.set("y", 60)
    for widget in GSM.Results_display_widgets_list:
        widget.destroy()
    GSM.Results_display_widgets_list.clear()
    GSM.Treeview_target_id_list.clear()

    def CreateTreeview():

        GSM.Tree_item_id = 0
        GSM.Roll_Treeview = ttk.Treeview(GSM.ROLL_frame)
        GSM.Roll_Treeview.place(x=RelPosROLL.set("x", 35), y=RelPosROLL.set("y", 110), height=450, width=755)
        GSM.Results_display_widgets_list.append(GSM.Roll_Treeview)

        style = ttk.Style(GSM.ROLL_frame)
        style.map("Treeview", background=[("selected", "green")])
        GSM.Roll_Treeview.tag_configure('has_hits', background="silver")
        GSM.Roll_Treeview.tag_configure('no_hits', background="white")
        GSM.Roll_Treeview.tag_configure('bold', background="white", font=("Roboco", 9, "bold"))

        #Define columns
        GSM.Roll_Treeview["columns"] = ('Hits', 'Dmg rolls 1', 'Total dmg 1',
                               'Dmg Type 1', 'Dmg rolls 2', 'Total dmg 2', 'Dmg Type 2',
                               'Save')
        #Format columns
        GSM.Roll_Treeview.column("#0", anchor="w", width=80, minwidth=30)  #Target column
        GSM.Roll_Treeview.column("Hits", anchor="center", width=40, minwidth=30)
        GSM.Roll_Treeview.column("Dmg rolls 1", anchor="center", width=20, minwidth=20)
        GSM.Roll_Treeview.column("Total dmg 1", anchor="center", width=4, minwidth=10)
        GSM.Roll_Treeview.column("Dmg Type 1", anchor="center", width=10, minwidth=10)
        GSM.Roll_Treeview.column("Dmg rolls 2", anchor="center", width=20, minwidth=20)
        GSM.Roll_Treeview.column("Total dmg 2", anchor="center", width=4, minwidth=10)
        GSM.Roll_Treeview.column("Dmg Type 2", anchor="center", width=10, minwidth=10)
        GSM.Roll_Treeview.column("Save", anchor="center", width=20, minwidth=20)
        # Create headings
        GSM.Roll_Treeview.heading("#0", anchor="center", text="Target")
        GSM.Roll_Treeview.heading("Hits", anchor="center", text="Hits")
        GSM.Roll_Treeview.heading("Dmg rolls 1", anchor="center", text="Dmg rolls 1")
        GSM.Roll_Treeview.heading("Total dmg 1", anchor="center", text="Total dmg 1")
        GSM.Roll_Treeview.heading("Dmg Type 1", anchor="center", text="Dmg Type 1")
        GSM.Roll_Treeview.heading("Dmg rolls 2", anchor="center", text="Dmg rolls 2")
        GSM.Roll_Treeview.heading("Total dmg 2", anchor="center", text="Total dmg 2")
        GSM.Roll_Treeview.heading("Dmg Type 2", anchor="center", text="Dmg Type 2")
        GSM.Roll_Treeview.heading("Save", anchor="center", text="Save")


    CreateTreeview()

    def DisplayResults(hits: list, dmgs1: list, dmgs1_type: list, dmgs2: list, dmgs2_type: list, target_name: str,
                       monster_names: list, n_monsters_list: list, saving_throw_package: list) -> None:
        '''Index of lists is a sublist of individual monster related hits/dmgs etc,
        is called once for each target '''

        for i in range(len(monster_names)):
            print(n_monsters_list[i], monster_names[i], hits[i], dmgs1[i], dmgs1_type[i], dmgs2[i], dmgs2_type[i])
            # 1 Fire zombie 1 ['crit20'] [16] bludgeoning [6] fire
            # 1 Fire zombie 2 [19, 17] [4, 6] magic piercing [3, 4] cold
        #Insert Target parent
        GSM.Tree_item_id += 1
        GSM.Roll_Treeview.insert(parent="", index="end", iid=GSM.Tree_item_id,
                                 text=target_name, values=(""), tags=("bold"))
        GSM.Treeview_target_id_list.append(GSM.Tree_item_id)
        expand = False
        #Insert monster children
        for i, monster in enumerate(monster_names):
            GSM.Tree_item_id += 1

            if hits[i]:  #If 'Hits' is not empty, color row
                tag = 'has_hits'
                expand = True
            else:
                tag = 'no_hits'

            # saving_throw_package[i] = [bool, dc, save_type]
            if saving_throw_package[i][0]: #If has saving throw
                dc = str(saving_throw_package[i][1])
                save_type = str(saving_throw_package[i][2])
                n_times = len(hits[i])
                write_save = str(f"{str(n_times)}x DC{dc} {save_type}")
                GSM.Roll_Treeview.insert(parent=GSM.Treeview_target_id_list[-1], index="end", iid=GSM.Tree_item_id,
                                         text=monster, values=(hits[i], dmgs1[i], sum(dmgs1[i]), dmgs1_type[i],
                                                               dmgs2[i], sum(dmgs2[i]), dmgs2_type[i], write_save), tags=tag)
            else:
                GSM.Roll_Treeview.insert(parent=GSM.Treeview_target_id_list[-1], index="end", iid=GSM.Tree_item_id,
                                         text=monster, values=(hits[i], dmgs1[i], sum(dmgs1[i]), dmgs1_type[i],
                                                               dmgs2[i], sum(dmgs2[i]), dmgs2_type[i]), tags=tag)
            GSM.Roll_Treeview.item(GSM.Treeview_target_id_list[-1], open=expand)  # This expands the parent node

    def CombineRollTypes(monster_type: str, target_type: str) -> str:
        # Combines 2 roll types to get what to actually use (like adv + disadv = normal)
        if monster_type == "Normal":
            if target_type == "Normal":
                return "Normal"
            elif target_type == "Advantage":
                return "Advantage"
            elif target_type == "Super Advantage":
                return "Super Advantage"
            elif target_type == "Disadvantage":
                return "Disadvantage"
            else:  # Super Disadvantage
                return "Super Disadvantage"
        elif monster_type == "Advantage":
            if target_type == "Normal":
                return "Advantage"
            elif target_type == "Disadvantage":
                return "Normal"
            elif target_type == "Super Disadvantage":
                return "Disadvantage"
            elif target_type == "Advantage":
                if GSM.Adv_combine_bool.get():
                    return "Super Advantage"
                else:
                    return "Advantage"
            else:  # Super Advantage
                return "Super Advantage"
        elif monster_type == "Disadvantage":
            if target_type == "Normal":
                return "Disadvantage"
            elif target_type == "Disadvantage":
                if GSM.Adv_combine_bool.get():
                    return "Super Disadvantage"
                else:
                    return "Disadvantage"
            elif target_type == "Super Disadvantage":
                return "Super Disadvantage"
            elif target_type == "Advantage":
                return "Normal"
            else:  # Super Advantage
                return "Advantage"
        elif monster_type == "Super Advantage":
            if target_type == "Normal":
                return "Super Advantage"
            elif target_type == "Disadvantage":
                return "Advantage"
            elif target_type == "Super Disadvantage":
                return "Normal"
            elif target_type == "Advantage":
                return "Super Advantage"
            else:  # Super Advantage
                return "Super Advantage"
        elif monster_type == "Super Disadvantage":
            if target_type == "Normal":
                return "Super Disadvantage"
            elif target_type == "Disadvantage":
                return "Super Disadvantage"
            elif target_type == "Super Disadvantage":
                return "Super Disadvantage"
            elif target_type == "Advantage":
                return "Disadvantage"
            else:  # Super Advantage
                return "Normal"

    def RollToHit(final_rolltype: str) -> int:
        if final_rolltype == "Normal":  # "Normal", "Advantage", "Disadvantage", "Super Advantage", "Super Disadvantage"
            roll = RollDice("d20")
        elif final_rolltype == "Advantage":
            roll = max(RollDice("d20"), RollDice("d20"))
        elif final_rolltype == "Disadvantage":
            roll = min(RollDice("d20"), RollDice("d20"))
        elif final_rolltype == "Super Advantage":
            roll = max(RollDice("d20"), RollDice("d20"), RollDice("d20"))
        elif final_rolltype == "Super Disadvantage":
            roll = min(RollDice("d20"), RollDice("d20"), RollDice("d20"))
        return int(roll)
    def ComputeDamage(dmg_1_n_die: int, dmg_1_die_type: str, dmg_1_flat: int, dmg_2_n_die: int, dmg_2_die_type: str,
               dmg_2_flat: int, GW_fighting_style: bool, brut_crit: bool, savage_attacker: bool, crit=False) -> (int, int):
        def GW_roll(die_type: str) -> int:  #Rolls dice with GW fighting style (reroll 1 & 2)
            roll = RollDice(die_type)
            if roll == 1 or roll == 2:
                roll = RollDice(die_type)
            return roll
        def Savage_attacker_roll(die_type: str) -> int: #Rolls dmg twice and use higher
            return max(RollDice(die_type), RollDice(die_type))
        def Brutal_crit_roll(die_type: str) -> int:     #Rolls dmg twice and use both
            return RollDice(die_type) + RollDice(die_type)
        def RollWithStyleNoCrit(GW: bool, savage: bool, die_type: str) -> int:
            "Rolls with one of two (or none) special abilities"
            if GW:  # Use GW fighting? #FIXME: At the moment, ONLY ONE of the three options is applied, never more
                return GW_roll(die_type)
            elif savage:  # Use Savaga attacker?
                return Savage_attacker_roll(die_type)
            else:  # Normal roll
                return RollDice(die_type)
        def RollWithStyleIsCrit(GW: bool, savage: bool, brut: bool, die_type: str) -> int:
            "Rolls with one of three (or none) special abilities when crits"
            if GW:  # Use GW fighting? #FIXME: At the moment, ONLY ONE of the three options is applied, never more
                return GW_roll(die_type)
            elif savage:  # Use Savaga attacker?
                return Savage_attacker_roll(die_type)
            elif brut:  # Use brutal hit (barb extra die)
                return Brutal_crit_roll(die_type)
            else:  # Normal roll
                return RollDice(die_type)

        if not crit:
            dmg1 = dmg_1_flat
            for dice in range(dmg_1_n_die):
                dmg1 = dmg1 + RollWithStyleNoCrit(GW_fighting_style, savage_attacker, dmg_1_die_type)
            dmg2 = dmg_2_flat
            for dice in range(dmg_2_n_die):
                dmg2 = dmg2 + RollWithStyleNoCrit(GW_fighting_style, savage_attacker, dmg_2_die_type)

        else: #Three different ways to compute critical hit
            if GSM.Crits_double_dmg_bool.get(): #Double all crit dmg
                dmg1 = dmg_1_flat
                for dice in range(dmg_1_n_die):
                    dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_1_die_type)
                dmg1 = dmg1*2
                dmg2 = dmg_2_flat
                for dice in range(dmg_2_n_die):
                        dmg2 = dmg2 + + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_2_die_type)
                dmg2 = dmg2*2
            else:
                if not GSM.Crits_extra_die_is_max_bool.get(): #Roll crit normally
                    dmg1 = dmg_1_flat
                    for dice in range(dmg_1_n_die*2):
                            dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_1_die_type)
                    dmg2 = dmg_2_flat
                    for dice in range(dmg_2_n_die*2):
                        dmg2 = dmg2 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_2_die_type)
                else: #Anti snake eyes crit rule
                    dmg1 = dmg_1_flat
                    for dice in range(dmg_1_n_die):
                        dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_1_die_type)\
                               + ReturnMaxPossibleDie(dmg_1_die_type)
                    dmg2 = dmg_2_flat
                    for dice in range(dmg_2_n_die):
                        dmg2 = dmg2 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_2_die_type)\
                               + ReturnMaxPossibleDie(dmg_1_die_type)
        return dmg1, dmg2

    for TargetObj in GSM.Target_obj_list:
        n_monsters = len(GSM.Monsters_list)  # Number of monsters dynamically
        #Created nested lists with number of lists inside the big one depending on how many monsters, [[]] for 1, [[], []] for 2 etc.
        hits = [[] for _ in range(n_monsters)]
        dmgs1 = [[] for _ in range(n_monsters)]
        dmgs2 = [[] for _ in range(n_monsters)]
        dmgs1_type = [[] for _ in range(n_monsters)]
        dmgs2_type = [[] for _ in range(n_monsters)]
        monster_names_list = [[] for _ in range(n_monsters)]
        n_monsters_list = [[] for _ in range(n_monsters)]
        saving_throw_package = [[] for _ in range(n_monsters)]

        ac = int(TargetObj.ac_int.get())
        print(f"-----{TargetObj.name_str.get()}-----")

        for i, monster_object in enumerate(GSM.Monsters_list):
            monster_name = monster_object.name_str.get()
            monster_n_attacks = monster_object.n_attacks.get()
            monster_to_hit_mod = monster_object.to_hit_mod.get()
            monster_roll_type = monster_object.roll_type.get()

            monster_dmg_1_type = monster_object.dmg_type_1.get()
            monster_dmg_1_n_die = monster_object.dmg_n_die_1.get()
            monster_dmg_1_die_type = monster_object.dmg_die_type_1.get()
            monster_dmg_1_flat = monster_object.dmg_flat_1.get()

            monster_dmg_2_type = monster_object.dmg_type_2.get()
            monster_dmg_2_n_die = monster_object.dmg_n_die_2.get()
            monster_dmg_2_die_type = monster_object.dmg_die_type_2.get()
            monster_dmg_2_flat = monster_object.dmg_flat_2.get()

            monster_on_hit_force_saving_throw_bool = monster_object.on_hit_force_saving_throw_bool.get()
            monster_on_hit_save_dc = monster_object.on_hit_save_dc.get()
            monster_on_hit_save_type = monster_object.on_hit_save_type.get()

            monster_halfling_luck = monster_object.reroll_1_on_hit.get()
            monster_GW_fighting_style = monster_object.reroll_1_2_dmg.get()
            monster_brut_crit = monster_object.brutal_critical.get()
            monster_crit_number = monster_object.crit_number.get()
            monster_savage_attacker = monster_object.savage_attacker.get()

            final_rolltype =  CombineRollTypes(monster_roll_type, TargetObj.monster_roll_type_against_str.get())

            #Grabs the correct number for each monster amount
            n_monsters = TargetObj.n_monsters_list_ints[i].get()

            for j in range(n_monsters):
                for attack in range(monster_n_attacks):

                    roll = RollToHit(final_rolltype) #Roll a d20
                    if roll == 1 and monster_halfling_luck: #reroll halfling luck (1 to hit)
                        roll = RollToHit(final_rolltype)
                    final_tohit_roll = roll + monster_to_hit_mod #Compute the final roll to hit
                    if monster_object.bless:
                        final_tohit_roll += RollDice("d4")
                    if monster_object.bane:
                        final_tohit_roll -= RollDice("d4")


                    if roll >= monster_crit_number: #Rolled a crit? and GSM.Crits_always_hit_bool.get():
                        adamantine_crit = True if not TargetObj.adamantine.get() else False #Adamantine overrides crit dmg
                        dmg1, dmg2 = ComputeDamage(monster_dmg_1_n_die, monster_dmg_1_die_type, monster_dmg_1_flat,
                                            monster_dmg_2_n_die, monster_dmg_2_die_type, monster_dmg_2_flat,
                                            monster_GW_fighting_style, monster_brut_crit, monster_savage_attacker, crit=adamantine_crit)
                        hits[i].append("crit" + str(roll))
                        dmgs1[i].append(dmg1)
                        dmgs2[i].append(dmg2) #Rolled a crit

                    elif roll == 1 and GSM.Nat1_always_miss_bool.get():
                        hits[i].append("nat1")

                    elif GSM.Meets_it_beats_it_bool.get():
                        if final_tohit_roll >= ac:
                            dmg1, dmg2 = ComputeDamage(monster_dmg_1_n_die, monster_dmg_1_die_type, monster_dmg_1_flat,
                                            monster_dmg_2_n_die, monster_dmg_2_die_type, monster_dmg_2_flat,
                                            monster_GW_fighting_style, monster_brut_crit, monster_savage_attacker, crit=False)
                            hits[i].append(final_tohit_roll)
                            dmgs1[i].append(dmg1)
                            dmgs2[i].append(dmg2)
                    else:
                        if final_tohit_roll > ac:
                            dmg1, dmg2 = ComputeDamage(monster_dmg_1_n_die, monster_dmg_1_die_type, monster_dmg_1_flat,
                                            monster_dmg_2_n_die, monster_dmg_2_die_type, monster_dmg_2_flat,
                                            monster_GW_fighting_style, monster_brut_crit, monster_savage_attacker, crit=False)
                            hits[i].append(final_tohit_roll)
                            dmgs1[i].append(dmg1)
                            dmgs2[i].append(dmg2)
            #Pack things to send to display
            dmgs1_type[i] = monster_dmg_1_type
            dmgs2_type[i] = monster_dmg_2_type
            monster_names_list[i] = monster_name
            n_monsters_list[i] = n_monsters
            saving_throw_package[i] = [monster_on_hit_force_saving_throw_bool, monster_on_hit_save_dc, monster_on_hit_save_type]


        DisplayResults(hits, dmgs1, dmgs1_type, dmgs2, dmgs2_type, TargetObj.name_str.get(), monster_names_list,
                       n_monsters_list, saving_throw_package)
