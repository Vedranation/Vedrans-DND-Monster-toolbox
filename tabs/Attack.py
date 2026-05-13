from GlobalStateManager import GSM
import tkinter as tk
from tkinter import ttk

from engine.combat import CombatSettings
from engine.combat import compute_single_attack as _engine_compute
from tabs.PlayerCreation import PlayerStats
from utilities import RollDice, ReturnMaxPossibleDie

def Attack(RelPosROLL):
    _spec_trace_ids: list[str] = []  # attacker→spec trace IDs; cleared on each OneAttackUI rebuild

    def ClearUI() -> None:
        for widget in GSM.Results_display_widgets_list:
            widget.destroy()
        GSM.Results_display_widgets_list.clear()
        GSM.Treeview_target_id_list.clear()
        GSM.OnTab_Attack_reset_widgets.clear()

    def CombineRollTypes(monster_type: str, target_type: str) -> str:
        from engine.combat import combine_roll_types
        return combine_roll_types(
            monster_type, target_type,
            adv_combine=GSM.Adv_combine_bool.get(),
            adv_mode=GSM.Adv_mode.get(),
        )

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

    def ComputeDamage(
        dmg_1_n_die: int,
        dmg_1_die_type: str,
        dmg_1_flat: int,
        dmg_2_n_die: int,
        dmg_2_die_type: str,
        dmg_2_flat: int,
        GW_fighting_style: bool,
        brut_crit: bool,
        savage_attacker: bool,
        crit=False,
    ) -> (int, int):
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
                    dmg2 = dmg2 + +RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_2_die_type)
                dmg2 = dmg2 * 2
            else:
                if not GSM.Crits_extra_die_is_max_bool.get():  # Roll crit normally
                    dmg1 = dmg_1_flat
                    for dice in range(dmg_1_n_die * 2):
                        dmg1 = dmg1 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_1_die_type)
                    dmg2 = dmg_2_flat
                    for dice in range(dmg_2_n_die * 2):
                        dmg2 = dmg2 + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_2_die_type)
                else:  # Anti snake eyes crit rule
                    dmg1 = dmg_1_flat
                    for dice in range(dmg_1_n_die):
                        dmg1 = (
                            dmg1
                            + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_1_die_type)
                            + ReturnMaxPossibleDie(dmg_1_die_type)
                        )
                    dmg2 = dmg_2_flat
                    for dice in range(dmg_2_n_die):
                        dmg2 = (
                            dmg2
                            + RollWithStyleIsCrit(GW_fighting_style, savage_attacker, brut_crit, dmg_2_die_type)
                            + ReturnMaxPossibleDie(dmg_1_die_type)
                        )
        return dmg1, dmg2

    def ComputeSingleAttack(
        target_obj: object, monster_object: object, override_rolltype: str = None
    ) -> (list, list, list, str, str, list):
        # If target_obj is None or monster_object, it will miss AC or monster_roll_type_against_str so we'll have to define that
        # Its those cases when a singular attack is called - we should also override any rollTypes
        # Attack once, ignoring multiattack
        hits = []
        dmgs1 = []
        dmgs2 = []

        if override_rolltype:  # Called by a OneAttack function
            crit_extra_dmg = True
            if target_obj:  # Is not None,
                ac = int(target_obj.ac_int.get())
                if isinstance(target_obj, PlayerStats):
                    crit_extra_dmg = not target_obj.adamantine.get()  # Adamantine overrides crit dmg
            else:  # Display all results
                ac = 0
            final_rolltype = override_rolltype
            monster_n_attacks = 1
        else:  # Called by ResolveAll, behave normally
            ac = int(target_obj.ac_int.get())
            final_rolltype = CombineRollTypes(
                monster_object.roll_type.get(), target_obj.monster_roll_type_against_str.get()
            )
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

        "Actual attack logic"
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
                dmg1, dmg2 = ComputeDamage(
                    monster_dmg_1_n_die,
                    monster_dmg_1_die_type,
                    monster_dmg_1_flat,
                    monster_dmg_2_n_die,
                    monster_dmg_2_die_type,
                    monster_dmg_2_flat,
                    monster_GW_fighting_style,
                    monster_brut_crit,
                    monster_savage_attacker,
                    crit=crit_extra_dmg,
                )
                hits.append("crit" + str(roll))
                dmgs1.append(dmg1)
                dmgs2.append(dmg2)  # Rolled a crit

            elif roll == 1 and GSM.Nat1_always_miss_bool.get():
                hits.append("nat1")

            elif GSM.Meets_it_beats_it_bool.get():
                if final_tohit_roll >= ac:
                    dmg1, dmg2 = ComputeDamage(
                        monster_dmg_1_n_die,
                        monster_dmg_1_die_type,
                        monster_dmg_1_flat,
                        monster_dmg_2_n_die,
                        monster_dmg_2_die_type,
                        monster_dmg_2_flat,
                        monster_GW_fighting_style,
                        monster_brut_crit,
                        monster_savage_attacker,
                        crit=False,
                    )
                    hits.append(final_tohit_roll)
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)
            else:
                if final_tohit_roll > ac:
                    dmg1, dmg2 = ComputeDamage(
                        monster_dmg_1_n_die,
                        monster_dmg_1_die_type,
                        monster_dmg_1_flat,
                        monster_dmg_2_n_die,
                        monster_dmg_2_die_type,
                        monster_dmg_2_flat,
                        monster_GW_fighting_style,
                        monster_brut_crit,
                        monster_savage_attacker,
                        crit=False,
                    )
                    hits.append(final_tohit_roll)
                    dmgs1.append(dmg1)
                    dmgs2.append(dmg2)

        result_package = (
            hits,
            dmgs1,
            dmgs2,
            monster_object.dmg_type_1.get(),
            monster_object.dmg_type_2.get(),
            [
                monster_object.on_hit_force_saving_throw_bool.get(),
                monster_object.on_hit_save_dc.get(),
                monster_object.on_hit_save_type.get(),
            ],
        )
        print(result_package)
        return result_package

    def ButtonSingleAttackAndDisplay(defender_name: str, attacker_name: str,
                                     override_rolltype: str, spec_name: str = "") -> None:
        from dataclasses import replace as _replace
        from engine.models import AttackSpec, PlayerData
        log_size = 7
        log_result_space = 55

        monster_map = {m.name_str.get(): m for m in GSM.Monster_obj_list}
        target_map = {t.name_str.get(): t for t in GSM.Target_obj_list}

        monster_obj = monster_map.get(attacker_name)
        if monster_obj is None:
            return

        monster_data = monster_obj.to_data()

        # Select the requested attack spec (or first if none matched)
        if monster_data.attacks:
            spec = next((a for a in monster_data.attacks if a.name == spec_name),
                        monster_data.attacks[0])
        else:
            spec = AttackSpec()

        # Apply override roll type and force a single attack
        spec = _replace(spec, roll_type=override_rolltype, n_attacks=1)
        single_monster = _replace(monster_data, attacks=[spec])

        # Build target (dummy AC-0 target when "None" selected → always hits)
        if defender_name != "None":
            defender_obj = target_map.get(defender_name) or monster_map.get(defender_name)
        else:
            defender_obj = None
        if defender_obj is not None and hasattr(defender_obj, "to_data"):
            player_data = defender_obj.to_data()
        else:
            player_data = PlayerData(ac=0)

        settings = CombatSettings(
            meets_it_beats_it=GSM.Meets_it_beats_it_bool.get(),
            crits_double_dmg=GSM.Crits_double_dmg_bool.get(),
            crits_extra_die_is_max=GSM.Crits_extra_die_is_max_bool.get(),
            nat1_always_miss=GSM.Nat1_always_miss_bool.get(),
            adv_combine=GSM.Adv_combine_bool.get(),
            adv_mode=GSM.Adv_mode.get(),
        )

        eng_result = _engine_compute(single_monster, player_data, settings)
        hits  = eng_result.hits
        dmgs1 = eng_result.dmgs1 or [0]
        dmgs2 = eng_result.dmgs2 or [0]

        # Normalise miss/nat1
        if not hits:
            hits = ["miss"]
            dmgs1 = [0]
            dmgs2 = [0]

        first_row = f"{hits[0]} to hit,  {dmgs1[0]} {eng_result.dmg_type_1} damage,\n"
        second_row = f"{dmgs2[0]} {eng_result.dmg_type_2} damage; " if dmgs2[0] else ""

        force_save, save_dc, save_type = eng_result.save_info
        if force_save and hits[0] not in ("miss", "nat1"):
            third_row = f"DC {save_dc} {save_type} save"
        else:
            third_row = ""

        hit0 = hits[0]
        if isinstance(hit0, int) or hit0 == "miss":
            text_colour = "black"
        elif hit0 == "nat1":
            text_colour = "red"
        else:
            text_colour = "green"  # crit

        result_label  = tk.Label(GSM.Attack_frame,
                                 text=f"{attacker_name} [{spec.name}] >>> {defender_name}:",
                                 font=GSM.Target_font)
        result_label2 = tk.Label(GSM.Attack_frame,
                                 text=(first_row + second_row + third_row), fg=text_colour)
        GSM.OneAttackLogResults.append(result_label)
        GSM.OneAttackLogResults.append(result_label2)

        if len(GSM.OneAttackLogResults) / 2 > log_size:
            GSM.OneAttackLogResults.pop(0).destroy()
            GSM.OneAttackLogResults.pop(0).destroy()

        for idx, widget in enumerate(GSM.OneAttackLogResults):
            if (idx + 1) % 2 != 0:
                widget.place(
                    x=GSM.RelPosROLL.checkpoint_get("x"),
                    y=GSM.RelPosROLL.set("y", GSM.RelPosROLL.checkpoint_get("y") + idx / 2 * log_result_space),
                )
            else:
                widget.place(x=GSM.RelPosROLL.checkpoint_get("x") + 30, y=GSM.RelPosROLL.increase("y", 20))

    def TreeviewDisplayResults(
        hits: list,
        dmgs1: list,
        dmgs1_type: list,
        dmgs2: list,
        dmgs2_type: list,
        target_name: str,
        monster_names: list,
        n_monsters_list: list,
        saving_throw_package: list,
    ) -> None:
        """Index of lists is a sublist of individual monster related hits/dmgs etc,
        is called once for each target"""

        for i in range(len(monster_names)):
            print(n_monsters_list[i], monster_names[i], hits[i], dmgs1[i], dmgs1_type[i], dmgs2[i], dmgs2_type[i])
            # 1 Fire zombie 1 ['crit20'] [16] bludgeoning [6] fire
            # 1 Fire zombie 2 [19, 17] [4, 6] magic piercing [3, 4] cold
        # Insert Target parent
        GSM.Tree_item_id += 1
        GSM.Roll_Treeview.insert(
            parent="", index="end", iid=GSM.Tree_item_id, text=target_name, values=(""), tags=("bold")
        )
        GSM.Treeview_target_id_list.append(GSM.Tree_item_id)
        expand = False
        # Insert monster children
        for i, monster in enumerate(monster_names):
            GSM.Tree_item_id += 1

            if hits[i]:  # If 'Hits' is not empty, color row
                tag = "has_hits"
                expand = True
            else:
                tag = "no_hits"

            # saving_throw_package[i] = [bool, dc, save_type]
            if saving_throw_package[i][0]:  # If has saving throw
                dc = str(saving_throw_package[i][1])
                save_type = str(saving_throw_package[i][2])
                n_times = len(hits[i])
                write_save = str(f"{str(n_times)}x DC{dc} {save_type}")
                GSM.Roll_Treeview.insert(
                    parent=GSM.Treeview_target_id_list[-1],
                    index="end",
                    iid=GSM.Tree_item_id,
                    text=monster,
                    values=(
                        hits[i],
                        dmgs1[i],
                        sum(dmgs1[i]),
                        dmgs1_type[i],
                        dmgs2[i],
                        sum(dmgs2[i]),
                        dmgs2_type[i],
                        write_save,
                    ),
                    tags=tag,
                )
            else:
                GSM.Roll_Treeview.insert(
                    parent=GSM.Treeview_target_id_list[-1],
                    index="end",
                    iid=GSM.Tree_item_id,
                    text=monster,
                    values=(hits[i], dmgs1[i], sum(dmgs1[i]), dmgs1_type[i], dmgs2[i], sum(dmgs2[i]), dmgs2_type[i]),
                    tags=tag,
                )
            GSM.Roll_Treeview.item(GSM.Treeview_target_id_list[-1], open=expand)  # This expands the parent node

    def ComputeAllAttacks() -> None:
        _settings = CombatSettings(
            meets_it_beats_it=GSM.Meets_it_beats_it_bool.get(),
            crits_double_dmg=GSM.Crits_double_dmg_bool.get(),
            crits_extra_die_is_max=GSM.Crits_extra_die_is_max_bool.get(),
            nat1_always_miss=GSM.Nat1_always_miss_bool.get(),
            adv_combine=GSM.Adv_combine_bool.get(),
        )

        for TargetObj in GSM.Target_obj_list:
            n_monsters = len(GSM.Monster_obj_list)
            hits = [[] for _ in range(n_monsters)]
            dmgs1 = [[] for _ in range(n_monsters)]
            dmgs2 = [[] for _ in range(n_monsters)]
            dmgs1_type = [[] for _ in range(n_monsters)]
            dmgs2_type = [[] for _ in range(n_monsters)]
            monster_names_list = [[] for _ in range(n_monsters)]
            n_monsters_list = [[] for _ in range(n_monsters)]
            saving_throw_package = [[] for _ in range(n_monsters)]

            print(f"-----{TargetObj.name_str.get()}-----")

            player_data = TargetObj.to_data()

            for i, monster_object in enumerate(GSM.Monster_obj_list):
                n_attacks_this = TargetObj.n_monsters_list_ints[i].get()
                monster_data = monster_object.to_data()
                _result = None

                for _ in range(n_attacks_this):
                    _result = _engine_compute(monster_data, player_data, _settings)
                    hits[i] = _result.hits
                    dmgs1[i] = _result.dmgs1
                    dmgs2[i] = _result.dmgs2

                if _result is not None:
                    dmgs1_type[i] = _result.dmg_type_1
                    dmgs2_type[i] = _result.dmg_type_2
                    saving_throw_package[i] = list(_result.save_info)
                else:
                    dmgs1_type[i] = monster_data.attacks[0].dmg_type_1 if monster_data.attacks else ""
                    dmgs2_type[i] = monster_data.attacks[0].dmg_type_2 if monster_data.attacks else ""
                    saving_throw_package[i] = [False, 0, ""]

                monster_names_list[i] = monster_object.name_str.get()
                n_monsters_list[i] = n_attacks_this

            TreeviewDisplayResults(
                hits,
                dmgs1,
                dmgs1_type,
                dmgs2,
                dmgs2_type,
                TargetObj.name_str.get(),
                monster_names_list,
                n_monsters_list,
                saving_throw_package,
            )

    def OneAttackUI() -> None:
        # Remove any leftover attacker→spec traces from prior UI builds
        for tid in list(_spec_trace_ids):
            try:
                GSM.OneAttacker_str.trace_remove("write", tid)
            except Exception:
                pass
        _spec_trace_ids.clear()

        ClearUI()

        # ── Attacker ──────────────────────────────────────────────────────────
        lbl_atk = tk.Label(GSM.Attack_frame, text="Select attacker: ")
        lbl_atk.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.set("y", 150))

        attacker_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.OneAttacker_str, *GSM.Monster_obj_list)
        GSM.OneAttacker_str.set(GSM.Monster_obj_list[0])
        attacker_dropdown.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", -4))
        GSM.OnTab_Attack_reset_widgets.append(
            [attacker_dropdown, GSM.RelPosROLL.same("x"), GSM.RelPosROLL.same("y"), "attacker_dropdown"]
        )

        # ── Attack spec selector (dynamic, rebuilds when attacker changes) ────
        lbl_spec = tk.Label(GSM.Attack_frame, text="Select attack: ")
        lbl_spec.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 40))

        _spec_dd_holder: list = [None]  # mutable ref so the trace can replace the widget

        def _get_spec_names() -> list[str]:
            name = GSM.OneAttacker_str.get()
            mo = next((m for m in GSM.Monster_obj_list if m.name_str.get() == name), None)
            if mo is None:
                return ["Attack"]
            specs = mo._attack_specs or [{"name": "Attack"}]
            return [s.get("name", "Attack") for s in specs] or ["Attack"]

        def _rebuild_spec_dd(*_) -> None:
            if _spec_dd_holder[0] and _spec_dd_holder[0].winfo_exists():
                _spec_dd_holder[0].destroy()
            names = _get_spec_names()
            GSM.OneAttack_spec_str.set(names[0])
            dd = tk.OptionMenu(GSM.Attack_frame, GSM.OneAttack_spec_str, *names)
            dd.place(x=_spec_x, y=_spec_y)
            _spec_dd_holder[0] = dd
            GSM.Results_display_widgets_list.append(dd)

        _spec_x = GSM.RelPosROLL.increase("x", 90)
        _spec_y = GSM.RelPosROLL.increase("y", -4)
        _tid = GSM.OneAttacker_str.trace_add("write", _rebuild_spec_dd)
        _spec_trace_ids.append(_tid)
        _rebuild_spec_dd()  # populate on open

        # ── Defender ─────────────────────────────────────────────────────────
        lbl_def = tk.Label(GSM.Attack_frame, text="Select defender: ")
        lbl_def.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 40))
        defender_dropdown = tk.OptionMenu(
            GSM.Attack_frame, GSM.OneDefender_str, *[*GSM.Monster_obj_list, *GSM.Target_obj_list, "None"]
        )
        GSM.OneDefender_str.set("None")
        defender_dropdown.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", -4))
        GSM.OnTab_Attack_reset_widgets.append(
            [defender_dropdown, GSM.RelPosROLL.same("x"), GSM.RelPosROLL.same("y"), "defender_dropdown"]
        )

        # ── Roll type override ────────────────────────────────────────────────
        lbl_rt = tk.Label(GSM.Attack_frame, text="Roll with:")
        lbl_rt.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 40))
        rolltype_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.Override_roll_type_str, *GSM.Roll_types)
        GSM.Override_roll_type_str.set("Normal")
        rolltype_dropdown.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", -4))
        lbl_rt2 = tk.Label(GSM.Attack_frame, text="Note: this overrides ALL rolltypes")
        lbl_rt2.place(x=GSM.RelPosROLL.increase("x", 100), y=GSM.RelPosROLL.increase("y", 4))
        lbl_rt3 = tk.Label(GSM.Attack_frame, text="Note: Ignores multiattack")
        lbl_rt3.place(x=GSM.RelPosROLL.set("x", 20), y=GSM.RelPosROLL.increase("y", 30))

        # ── Roll button ───────────────────────────────────────────────────────
        def _do_roll() -> None:
            ButtonSingleAttackAndDisplay(
                GSM.OneDefender_str.get(),
                GSM.OneAttacker_str.get(),
                GSM.Override_roll_type_str.get(),
                spec_name=GSM.OneAttack_spec_str.get(),
            )

        RollAttack_button = tk.Button(
            GSM.Attack_frame, text="Roll attack", state="normal",
            command=_do_roll, font=GSM.Target_font, padx=3, background="grey",
        )
        RollAttack_button.place(x=GSM.RelPosROLL.increase("x", 90), y=GSM.RelPosROLL.increase("y", 30))

        GSM.RelPosROLL.checkpoint_set("x", 420)
        GSM.RelPosROLL.checkpoint_set("y", 100)

        for w in (lbl_atk, attacker_dropdown, lbl_spec, lbl_def, defender_dropdown,
                  lbl_rt, lbl_rt2, lbl_rt3, rolltype_dropdown, RollAttack_button):
            GSM.Results_display_widgets_list.append(w)

    def ResolveCombat() -> None:
        # TODO: Add a "Copy results to clipboard" button (so it can be pasted in chat like discord or VTT)
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
            GSM.Roll_Treeview.tag_configure("has_hits", background="silver")
            GSM.Roll_Treeview.tag_configure("no_hits", background="white")
            GSM.Roll_Treeview.tag_configure("bold", background="white", font=("Roboco", 9, "bold"))

            # Define columns
            GSM.Roll_Treeview["columns"] = (
                "Hits",
                "Dmg rolls 1",
                "Total dmg 1",
                "Dmg Type 1",
                "Dmg rolls 2",
                "Total dmg 2",
                "Dmg Type 2",
                "Save",
            )
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

    # Resolve combat button
    Resolve_combat_text_label = tk.Label(GSM.Attack_frame, text="Roll attacks", font=GSM.Title_font)
    Resolve_combat_text_label.place(x=GSM.RelPosROLL.reset("x"), y=GSM.RelPosROLL.reset("y"))
    ROLL_button = tk.Button(
        GSM.Attack_frame,
        text="Resolve Combat",
        state="normal",
        command=ResolveCombat,
        font=GSM.Title_font,
        padx=9,
        background="red",
    )
    ROLL_button.place(
        x=GSM.RelPosROLL.increase("x", 10), y=GSM.RelPosROLL.increase("y", GSM.RelPosROLL.constant_y * 1.5)
    )

    # One attack combat button
    Oneattack_button = tk.Button(
        GSM.Attack_frame,
        text="Attack once",
        state="normal",
        command=OneAttackUI,
        font=GSM.Target_font,
        padx=3,
        background="grey",
    )
    Oneattack_button.place(x=GSM.RelPosROLL.increase("x", 180), y=GSM.RelPosROLL.increase("y", 4))
