from logging import exception

from GlobalStateManager import GSM
import tkinter as tk
from tkinter import ttk

from tabs.PlayerCreation import PlayerStats
from utilities import RollDice, ReturnMaxPossibleDie


def Attack(RelPosROLL):

    def ClearUI() -> None:
        for widget in GSM.Results_display_widgets_list:
            widget.destroy()
        GSM.Results_display_widgets_list.clear()
        GSM.Treeview_target_id_list.clear()
        GSM.OnTab_Attack_reset_widgets.clear()

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
                      dmg_2_flat: int, GW_fighting_style: bool, brut_crit: bool, savage_attacker: bool,
                      crit=False) -> (int, int):
        def GW_roll(die_type: str) -> int:  # Rolls dice with GW fighting style (reroll 1 & 2)
            roll = RollDice(die_type)
            if roll == 1 or roll == 2:
                roll = RollDice(die_type)
            return roll

        def Savage_attacker_roll(die_type: str) -> int:  # Rolls dmg twice and use higher
            return max(RollDice(die_type), RollDice(die_type))

        def Brutal_crit_roll(die_type: str) -> int:  # Rolls dmg twice and use both
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

        else:  # Three different ways to compute critical hit
            if GSM.Crits_double_dmg_bool.get():  # Double all crit dmg
                dmg1 = dmg_1_flat
                for dice in range(dmg_1_n_die):
                    dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_1_die_type)
                dmg1 = dmg1 * 2
                dmg2 = dmg_2_flat
                for dice in range(dmg_2_n_die):
                    dmg2 = dmg2 + + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit,
                                                        dmg_2_die_type)
                dmg2 = dmg2 * 2
            else:
                if not GSM.Crits_extra_die_is_max_bool.get():  # Roll crit normally
                    dmg1 = dmg_1_flat
                    for dice in range(dmg_1_n_die * 2):
                        dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit,
                                                          dmg_1_die_type)
                    dmg2 = dmg_2_flat
                    for dice in range(dmg_2_n_die * 2):
                        dmg2 = dmg2 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit,
                                                          dmg_2_die_type)
                else:  # Anti snake eyes crit rule
                    dmg1 = dmg_1_flat
                    for dice in range(dmg_1_n_die):
                        dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit,
                                                          dmg_1_die_type) \
                               + ReturnMaxPossibleDie(dmg_1_die_type)
                    dmg2 = dmg_2_flat
                    for dice in range(dmg_2_n_die):
                        dmg2 = dmg2 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit,
                                                          dmg_2_die_type) \
                               + ReturnMaxPossibleDie(dmg_1_die_type)
        return dmg1, dmg2


    def ComputeSingleAttack(target_obj: object, monster_object: object, override_rolltype: str=None) -> (list, list, list, str, str, list):
        #If target_obj is None or monster_object, it will miss AC or monster_roll_type_against_str so we'll have to define that
        #Its those cases when a singular attack is called - we should also override any rollTypes
        # Attack once, ignoring multiattack
        hits = []
        dmgs1 = []
        dmgs2 = []

        if override_rolltype: # Called by a OneAttack function
            crit_extra_dmg = True
            if target_obj:  # Is not None,
                ac = int(target_obj.ac_int.get())
                if isinstance(target_obj, PlayerStats):
                    crit_extra_dmg = not target_obj.adamantine.get()  # Adamantine overrides crit dmg
            else: #Display all results
                ac = 0
            final_rolltype = override_rolltype
            monster_n_attacks = 1
        else: #Called by ResolveAll, behave normally
            ac = int(target_obj.ac_int.get())
            final_rolltype = CombineRollTypes(monster_object.roll_type.get(), target_obj.monster_roll_type_against_str.get())
            crit_extra_dmg = not target_obj.adamantine.get()  # Adamantine overrides crit dmg
            monster_n_attacks = monster_object.n_attacks.get()

        monster_to_hit_mod = monster_object.to_hit_mod.get()

        monster_dmg_1_n_die = monster_object.dmg_n_die_1.get()
        monster_dmg_1_die_type = monster_object.dmg_die_type_1.get()
        monster_dmg_1_flat = monster_object.dmg_flat_1.get()

        monster_dmg_2_n_die = monster_object.dmg_n_die_2.get()
        monster_dmg_2_die_type = monster_object.dmg_die_type_2.get()
        monster_dmg_2_flat = monster_object.dmg_flat_2.get()

        monster_halfling_luck = monster_object.reroll_1_on_hit.get()
        monster_GW_fighting_style = monster_object.reroll_1_2_dmg.get()
        monster_brut_crit = monster_object.brutal_critical.get()
        monster_crit_number = monster_object.crit_number.get()
        monster_savage_attacker = monster_object.savage_attacker.get()

        'Actual attack logic'
        for attack in range(monster_n_attacks):
            roll = RollToHit(final_rolltype)  # Roll a d20
            if roll == 1 and monster_halfling_luck:  # reroll halfling luck (1 to hit)
                roll = RollToHit(final_rolltype)
            final_tohit_roll = roll + monster_to_hit_mod  # Compute the final roll to hit
            if monster_object.bless.get():
                final_tohit_roll += RollDice("d4")
            if monster_object.bane.get():
                final_tohit_roll -= RollDice("d4")

            if roll >= monster_crit_number:  # Rolled a crit? and GSM.Crits_always_hit_bool.get():
                dmg1, dmg2 = ComputeDamage(monster_dmg_1_n_die, monster_dmg_1_die_type, monster_dmg_1_flat,
                                           monster_dmg_2_n_die, monster_dmg_2_die_type, monster_dmg_2_flat,
                                           monster_GW_fighting_style, monster_brut_crit,
                                           monster_savage_attacker, crit=crit_extra_dmg)
                hits.append("crit" + str(roll))
                dmgs1.append(dmg1)
                dmgs2.append(dmg2)  # Rolled a crit

            elif roll == 1 and GSM.Nat1_always_miss_bool.get():
                hits.append("nat1")

            elif GSM.Meets_it_beats_it_bool.get():
                if final_tohit_roll >= ac:
                    dmg1, dmg2 = ComputeDamage(monster_dmg_1_n_die, monster_dmg_1_die_type,
                                               monster_dmg_1_flat,
                                               monster_dmg_2_n_die, monster_dmg_2_die_type,
                                               monster_dmg_2_flat,
                                               monster_GW_fighting_style, monster_brut_crit,
                                               monster_savage_attacker, crit=False)
                    hits.append(final_tohit_roll)
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)
            else:
                if final_tohit_roll > ac:
                    dmg1, dmg2 = ComputeDamage(monster_dmg_1_n_die, monster_dmg_1_die_type,
                                               monster_dmg_1_flat,
                                               monster_dmg_2_n_die, monster_dmg_2_die_type,
                                               monster_dmg_2_flat,
                                               monster_GW_fighting_style, monster_brut_crit,
                                               monster_savage_attacker, crit=False)
                    hits.append(final_tohit_roll)
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)

        result_package = (hits, dmgs1, dmgs2, monster_object.dmg_type_1.get(), monster_object.dmg_type_2.get(),
                          [monster_object.on_hit_force_saving_throw_bool.get(), monster_object.on_hit_save_dc.get(),
                 monster_object.on_hit_save_type.get()])
        print(result_package)
        return result_package

    def ButtonSingleAttackAndDisplay(defender_name: str, attacker_name: str, override_rolltype: str) -> None:
        log_size = 7
        log_result_space = 55
        #For single attacking button, calls a function to display result
        monster_map = {monster.name_str.get(): monster for monster in GSM.Monsters_list}
        target_map = {target.name_str.get(): target for target in GSM.Target_obj_list}

        #Attacker (monster only)
        monster_obj = monster_map.get(attacker_name, None)  # Retrieve attacker object
        if monster_obj is None:
            print("No attacker selected!")
            return

        #Defender (monster, player or none)
        defender_obj = target_map.get(defender_name, None)  # Check if it's a target object
        if defender_obj is None:  # If not a target, check if it's a monster
            defender_obj = monster_map.get(defender_name, None)

        # If defender_name is "None", treat it as a pure attack
        if defender_name == "None":
            defender_obj = None
        # tuple(To hit, dmg1, dmg2, dmg_type_1, dmg_type_2, [has_save_bool, dc, type])
        result = list(ComputeSingleAttack(defender_obj, monster_obj, override_rolltype))

        # Filter out the trash from results
        if (result[0] and result[0][0] == "nat1") or result[0] == []: #Critical fail or no hits (brings empty lists)
            result[1] = [0] #Put zeroes into nat1 dmg's
            result[2] = [0]
            result[0] = ["miss"] if result[0] == [] else ["nat1"]
        first_row = f"{result[0][0]} to hit,  {result[1][0]} {result[3]} damage,\n"
        if result[2][0] == 0: #no secondary dmg, no need to display
            second_row = ""
        else:
            second_row = f"{result[2][0]} {result[4]} damage; "
        if result[5][0]: #Has saving throw:
            if result[0][0] == "miss" or result[0][0] == "nat1": #Don't roll on miss
                n_throws = 0
            else:
                n_throws = 1
            third_row = f"{n_throws}x DC {result[5][1]} {result[5][2]} save"
        else:
            third_row = ""

        #Determine text color for nat1 or nat20
        if type(result[0][0]) == int or result[0][0] == "miss": #Default case
            text_colour = "black"
        elif result[0][0] == "nat1":
            text_colour = "red"
        elif result[0][0].startswith("crit"):
            text_colour = "green"
        else:
            raise Exception("Invalid roll - must be int, nat1 or crit")

        result_label = tk.Label(GSM.Attack_frame, text=f"{attacker_name} >>> {defender_name}:", font=GSM.Target_font)
        result_label2 = tk.Label(GSM.Attack_frame, text=(first_row + second_row + third_row), fg=text_colour)
        GSM.OneAttackLogResults.append(result_label) #Stores just one attack results for queue
        GSM.OneAttackLogResults.append(result_label2)

        if len(GSM.OneAttackLogResults) / 2 > log_size:
            # Remove the oldest label from the queue
            oldest_label = GSM.OneAttackLogResults.pop(0)
            oldest_label.destroy()  # Destroy the widget to free up space
            oldest_label2 = GSM.OneAttackLogResults.pop(0)
            oldest_label2.destroy()  # Destroy the widget to free up space

        # Reposition the remaining labels to maintain consistent spacing
        for idx, widget in enumerate(GSM.OneAttackLogResults):
            if (idx + 1) % 2 != 0:  # Part 1
                widget.place(
                    x=GSM.RelPosROLL.checkpoint_get("x"),
                    y=GSM.RelPosROLL.set("y", GSM.RelPosROLL.checkpoint_get("y") + idx / 2 * log_result_space))
            else:  # Part 2
                widget.place(
                    x=GSM.RelPosROLL.checkpoint_get("x") + 30,
                    y=GSM.RelPosROLL.increase("y", 20))

    def TreeviewDisplayResults(hits: list, dmgs1: list, dmgs1_type: list, dmgs2: list, dmgs2_type: list, target_name: str,
                       monster_names: list, n_monsters_list: list, saving_throw_package: list) -> None:
        '''Index of lists is a sublist of individual monster related hits/dmgs etc,
        is called once for each target '''

        for i in range(len(monster_names)):
            print(n_monsters_list[i], monster_names[i], hits[i], dmgs1[i], dmgs1_type[i], dmgs2[i], dmgs2_type[i])
            # 1 Fire zombie 1 ['crit20'] [16] bludgeoning [6] fire
            # 1 Fire zombie 2 [19, 17] [4, 6] magic piercing [3, 4] cold
        # Insert Target parent
        GSM.Tree_item_id += 1
        GSM.Roll_Treeview.insert(parent="", index="end", iid=GSM.Tree_item_id,
                                 text=target_name, values=(""), tags=("bold"))
        GSM.Treeview_target_id_list.append(GSM.Tree_item_id)
        expand = False
        # Insert monster children
        for i, monster in enumerate(monster_names):
            GSM.Tree_item_id += 1

            if hits[i]:  # If 'Hits' is not empty, color row
                tag = 'has_hits'
                expand = True
            else:
                tag = 'no_hits'

            # saving_throw_package[i] = [bool, dc, save_type]
            if saving_throw_package[i][0]:  # If has saving throw
                dc = str(saving_throw_package[i][1])
                save_type = str(saving_throw_package[i][2])
                n_times = len(hits[i])
                write_save = str(f"{str(n_times)}x DC{dc} {save_type}")
                GSM.Roll_Treeview.insert(parent=GSM.Treeview_target_id_list[-1], index="end", iid=GSM.Tree_item_id,
                                         text=monster, values=(hits[i], dmgs1[i], sum(dmgs1[i]), dmgs1_type[i],
                                                               dmgs2[i], sum(dmgs2[i]), dmgs2_type[i], write_save),
                                         tags=tag)
            else:
                GSM.Roll_Treeview.insert(parent=GSM.Treeview_target_id_list[-1], index="end", iid=GSM.Tree_item_id,
                                         text=monster, values=(hits[i], dmgs1[i], sum(dmgs1[i]), dmgs1_type[i],
                                                               dmgs2[i], sum(dmgs2[i]), dmgs2_type[i]), tags=tag)
            GSM.Roll_Treeview.item(GSM.Treeview_target_id_list[-1], open=expand)  # This expands the parent node
    def ComputeAllAttacks() -> None:
        for TargetObj in GSM.Target_obj_list:
            n_monsters = len(GSM.Monsters_list)  # Number of monsters dynamically
            # Created nested lists with number of lists inside the big one depending on how many monsters, [[]] for 1, [[], []] for 2 etc.
            hits = [[] for _ in range(n_monsters)]
            dmgs1 = [[] for _ in range(n_monsters)]
            dmgs2 = [[] for _ in range(n_monsters)]
            dmgs1_type = [[] for _ in range(n_monsters)]
            dmgs2_type = [[] for _ in range(n_monsters)]
            monster_names_list = [[] for _ in range(n_monsters)]
            n_monsters_list = [[] for _ in range(n_monsters)]
            saving_throw_package = [[] for _ in range(n_monsters)]

            print(f"-----{TargetObj.name_str.get()}-----")

            for i, monster_object in enumerate(GSM.Monsters_list):
                # Grabs the correct number for each monster amount
                n_monsters = TargetObj.n_monsters_list_ints[i].get()
                # Gets this stuff in case 0 monsters so it can be passed on to display
                _monster_dmg_1_type = monster_object.dmg_die_type_1.get()
                _monster_dmg_2_type = monster_object.dmg_die_type_2.get()
                _saving_throw_package = [monster_object.on_hit_force_saving_throw_bool.get(), monster_object.on_hit_save_dc.get(),
                 monster_object.on_hit_save_type.get()]
                for j in range(n_monsters):
                    (_hits, _dmgs1, _dmgs2, _monster_dmg_1_type, _monster_dmg_2_type,
                     _saving_throw_package) = ComputeSingleAttack(TargetObj, monster_object)
                    hits[i] = _hits
                    dmgs1[i] = _dmgs1
                    dmgs2[i] = _dmgs2


                # Pack things to send to display
                dmgs1_type[i] = _monster_dmg_1_type
                dmgs2_type[i] = _monster_dmg_2_type
                monster_names_list[i] = monster_object.name_str.get()
                n_monsters_list[i] = n_monsters
                saving_throw_package[i] = _saving_throw_package

            TreeviewDisplayResults(hits, dmgs1, dmgs1_type, dmgs2, dmgs2_type, TargetObj.name_str.get(), monster_names_list,
                           n_monsters_list, saving_throw_package)

    def OneAttackUI() -> None:
        ClearUI()
        one_attack_label = tk.Label(GSM.Attack_frame, text="Select attacker: ")
        one_attack_label.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.set("y", 150))


        attacker_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.OneAttacker_str, *GSM.Monsters_list )
        GSM.OneAttacker_str.set(GSM.Monsters_list[0])
        attacker_dropdown.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", -4))
        GSM.OnTab_Attack_reset_widgets.append([attacker_dropdown, GSM.RelPosROLL.same("x"), GSM.RelPosROLL.same("y"), "attacker_dropdown"])

        one_attack_label2 = tk.Label(GSM.Attack_frame, text="Select defender: ")
        one_attack_label2.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 40))
        defender_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.OneDefender_str,
                                          *[*GSM.Monsters_list, *GSM.Target_obj_list, "None"])
        GSM.OneDefender_str.set("None")
        defender_dropdown.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", -4))
        GSM.OnTab_Attack_reset_widgets.append([defender_dropdown, GSM.RelPosROLL.same("x"), GSM.RelPosROLL.same("y"), "defender_dropdown"])


        one_attack_label3 = tk.Label(GSM.Attack_frame, text="Roll with:")
        one_attack_label3.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 40))
        rolltype_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.Override_roll_type_str,
                                          *GSM.Roll_types)
        GSM.Override_roll_type_str.set("Normal")
        rolltype_dropdown.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", -4))
        one_attack_label4 = tk.Label(GSM.Attack_frame, text="Note: this overrides ALL rolltypes")
        one_attack_label4.place(x=GSM.RelPosROLL.increase("x", 100), y=GSM.RelPosROLL.increase("y", 4))
        one_attack_label5 = tk.Label(GSM.Attack_frame, text="Note: Ignores multiattack")
        one_attack_label5.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 30))

        RollAttack_button = tk.Button(GSM.Attack_frame, text="Roll attack", state="normal",
                                      command=lambda: ButtonSingleAttackAndDisplay(GSM.OneDefender_str.get(),
                                        GSM.OneAttacker_str.get(), GSM.Override_roll_type_str.get()),
                                      font=GSM.Target_font, padx=3, background="grey")
        RollAttack_button.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", 30))

        GSM.RelPosROLL.checkpoint_set("x", 420) # set a checkpoint for displaying results
        GSM.RelPosROLL.checkpoint_set("y", 100)

        GSM.Results_display_widgets_list.append(one_attack_label)
        GSM.Results_display_widgets_list.append(one_attack_label2)
        GSM.Results_display_widgets_list.append(one_attack_label3)
        GSM.Results_display_widgets_list.append(one_attack_label4)
        GSM.Results_display_widgets_list.append(one_attack_label5)
        GSM.Results_display_widgets_list.append(attacker_dropdown)
        GSM.Results_display_widgets_list.append(defender_dropdown)
        GSM.Results_display_widgets_list.append(rolltype_dropdown)
        GSM.Results_display_widgets_list.append(RollAttack_button)


    def ResolveCombat() -> None:
        # TODO: Add a "Copy results to clipboard" button!
        # TODO: Add a single monster attack, such as for reaction or whatever
        print("")
        print("NEW ROLL")
        ClearUI()
        def CreateTreeview():

            GSM.Tree_item_id = 0
            GSM.Roll_Treeview = ttk.Treeview(GSM.Attack_frame)
            GSM.Roll_Treeview.place(x=RelPosROLL.set("x", 30), y=RelPosROLL.set("y", 100), height=465, width=765)
            GSM.Results_display_widgets_list.append(GSM.Roll_Treeview)

            style = ttk.Style(GSM.Attack_frame)
            style.map("Treeview", background=[("selected", "green")])
            GSM.Roll_Treeview.tag_configure('has_hits', background="silver")
            GSM.Roll_Treeview.tag_configure('no_hits', background="white")
            GSM.Roll_Treeview.tag_configure('bold', background="white", font=("Roboco", 9, "bold"))

            # Define columns
            GSM.Roll_Treeview["columns"] = ('Hits', 'Dmg rolls 1', 'Total dmg 1',
                                            'Dmg Type 1', 'Dmg rolls 2', 'Total dmg 2', 'Dmg Type 2',
                                            'Save')
            # Format columns
            GSM.Roll_Treeview.column("#0", anchor="w", width=80, minwidth=30)  # Target column
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
        ComputeAllAttacks()

    #Resolve combat button
    Resolve_combat_text_label = tk.Label(GSM.Attack_frame, text="Roll attacks", font=GSM.Title_font)
    Resolve_combat_text_label.place(x=GSM.RelPosROLL.reset("x"), y=GSM.RelPosROLL.reset("y"))
    ROLL_button = tk.Button(GSM.Attack_frame, text="Resolve Combat", state="normal", command=ResolveCombat,
                            font=GSM.Title_font, padx=9, background="red")
    ROLL_button.place(x=GSM.RelPosROLL.increase("x", 10), y=GSM.RelPosROLL.increase("y", GSM.RelPosROLL.constant_y*1.5))

    # One attack combat button
    Oneattack_button = tk.Button(GSM.Attack_frame, text="Attack once", state="normal", command=OneAttackUI,
                            font=GSM.Target_font, padx=3, background="grey")
    Oneattack_button.place(x=GSM.RelPosROLL.increase("x", 180), y=GSM.RelPosROLL.increase("y", 4))
