from GlobalStateManager import GSM
import tkinter as tk

from engine.combat import CombatSettings, format_damage_breakdown
from engine.combat import compute_single_attack as _engine_compute
from engine.models import PlayerData

# NOTE: The batch "Resolve Combat" feature was sunset — the Battle Board's
# Resolve replaced it. This tab does single-roll attacks: pick an attacker,
# tick which of its attacks to use (multiattack), pick a defender, roll.
# Results mirror the Battle Board (per-swing d20s, hit/miss with the number,
# both dice on adv/disadv) and accumulate in a scrollable log (newest on top).
# All combat math lives in engine/combat.py.

# Layout coordinates on GSM.Attack_frame.
_X_LABEL, _X_FIELD = 20, 110
_Y_ATTACKER, _Y_ATTACKS, _Y_DEFENDER, _Y_ROLLTYPE, _Y_BUTTON = 50, 88, 126, 164, 202

_F8, _F8B = ("Helvetica", 8), ("Helvetica", 8, "bold")
_LOG_CAP = 12  # keep this many past rolls in the queue


def Attack(RelPosROLL):
    # Per-attacker checkbox state, rebuilt whenever the attacker changes.
    _attack_state: dict = {"specs": [], "vars": []}  # parallel lists
    _log_blocks: list = []  # message queue, newest first
    _trace_ids: list[str] = []

    def _monster_by_name(name: str):
        return next((m for m in GSM.Monster_obj_list if m.name_str.get() == name), None)

    def _defender_data(name: str) -> PlayerData:
        """Resolve the chosen defender to a PlayerData defense view.

        'None'/unknown → AC-0 dummy that always gets hit. A player uses its own
        data; a monster defender is adapted into a PlayerData view (supports
        monster-vs-monster single rolls). imposed_roll_type is blanked because
        "Roll with" is the sole authority over the roll type (see _do_roll).
        """
        if name == "None":
            return PlayerData(ac=0)
        pobj = next((p for p in GSM.Target_obj_list if p.name_str.get() == name), None)
        if pobj is not None:
            return pobj.to_data()
        mobj = _monster_by_name(name)
        if mobj is not None:
            md = mobj.to_data()
            return PlayerData(name=md.name, ac=md.ac, max_hp=md.max_hp,
                              passive_perception=md.passive_perception, conditions=md.conditions)
        return PlayerData(ac=0)

    if not GSM.Monster_obj_list:
        tk.Label(GSM.Attack_frame, text="Create a monster first to roll attacks.",
                 font=GSM.Title_font).place(x=_X_LABEL, y=20)
        return

    # ── title ────────────────────────────────────────────────────────────────
    tk.Label(GSM.Attack_frame, text="Attack roll", font=GSM.Title_font).place(x=_X_LABEL, y=12)

    # ── attacker ─────────────────────────────────────────────────────────────
    tk.Label(GSM.Attack_frame, text="Attacker:").place(x=_X_LABEL, y=_Y_ATTACKER)
    attacker_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.OneAttacker_str, *GSM.Monster_obj_list)
    GSM.OneAttacker_str.set(str(GSM.Monster_obj_list[0]))
    attacker_dropdown.place(x=_X_FIELD, y=_Y_ATTACKER - 4)
    GSM.OnTab_Attack_reset_widgets.append(
        [attacker_dropdown, _X_FIELD, _Y_ATTACKER - 4, "attacker_dropdown"]
    )

    # ── attacks (multi-select checkboxes, rebuilt on attacker change) ─────────
    tk.Label(GSM.Attack_frame, text="Use attacks:").place(x=_X_LABEL, y=_Y_ATTACKS)
    cb_frame = tk.Frame(GSM.Attack_frame)
    cb_frame.place(x=_X_FIELD, y=_Y_ATTACKS - 2)

    def _rebuild_attack_checkboxes(*_args) -> None:
        for w in cb_frame.winfo_children():
            w.destroy()
        _attack_state["specs"].clear()
        _attack_state["vars"].clear()
        mo = _monster_by_name(GSM.OneAttacker_str.get())
        specs = mo.to_data().attacks if mo else []
        _attack_state["specs"] = specs
        for spec in specs:
            var = tk.BooleanVar(value=True)  # default: use all attacks (dragon-style)
            label = spec.name or "Attack"
            if spec.n_attacks > 1:
                label += f" ×{spec.n_attacks}"
            tk.Checkbutton(cb_frame, text=label, variable=var).pack(side="left")
            _attack_state["vars"].append(var)

    # ── defender ─────────────────────────────────────────────────────────────
    tk.Label(GSM.Attack_frame, text="Defender:").place(x=_X_LABEL, y=_Y_DEFENDER)
    defender_dropdown = tk.OptionMenu(
        GSM.Attack_frame, GSM.OneDefender_str, *[*GSM.Monster_obj_list, *GSM.Target_obj_list, "None"]
    )
    GSM.OneDefender_str.set("None")
    defender_dropdown.place(x=_X_FIELD, y=_Y_DEFENDER - 4)
    GSM.OnTab_Attack_reset_widgets.append(
        [defender_dropdown, _X_FIELD, _Y_DEFENDER - 4, "defender_dropdown"]
    )

    # ── roll type override ────────────────────────────────────────────────────
    tk.Label(GSM.Attack_frame, text="Roll with:").place(x=_X_LABEL, y=_Y_ROLLTYPE)
    rolltype_dropdown = tk.OptionMenu(GSM.Attack_frame, GSM.Override_roll_type_str, *GSM.Roll_types)
    GSM.Override_roll_type_str.set("Normal")
    rolltype_dropdown.place(x=_X_FIELD, y=_Y_ROLLTYPE - 4)
    tk.Label(GSM.Attack_frame, text="Note: this overrides ALL rolltypes",
             font=("Helvetica", 7), fg="#666").place(x=_X_FIELD + 90, y=_Y_ROLLTYPE)

    # ── results log (scrollable message queue) ────────────────────────────────
    log_outer = tk.Frame(GSM.Attack_frame)
    log_outer.place(x=18, y=_Y_BUTTON + 38, width=785, height=345)
    log_scroll = tk.Scrollbar(log_outer, orient="vertical")
    log_canvas = tk.Canvas(log_outer, highlightthickness=0, yscrollcommand=log_scroll.set)
    log_scroll.config(command=log_canvas.yview)
    log_scroll.pack(side="right", fill="y")
    log_canvas.pack(side="left", fill="both", expand=True)
    log_inner = tk.Frame(log_canvas)
    log_canvas.create_window((0, 0), window=log_inner, anchor="nw")
    log_inner.bind("<Configure>", lambda _e: log_canvas.configure(scrollregion=log_canvas.bbox("all")))
    log_canvas.bind("<MouseWheel>", lambda e: log_canvas.yview_scroll(-int(e.delta / 120), "units"))

    def _build_block(parent, result, attacker_name: str, defender_name: str, override: str) -> None:
        row = 0
        tag = f"  [{override}]" if override != "Normal" else ""
        tk.Label(parent, text=f"{attacker_name} → {defender_name}{tag}", font=_F8B,
                 anchor="w").grid(row=row, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 1))
        row += 1
        if not result.rolls:
            tk.Label(parent, text="Select at least one attack.", font=_F8, fg="#cc3333").grid(
                row=row, column=0, sticky="w", padx=4, pady=(0, 2))
            return
        for r in result.rolls:
            outcome = "CRIT" if r.is_crit else ("MISS" if not r.is_hit else "HIT")
            dice_frame = tk.Frame(parent)
            tk.Label(dice_frame, text=f"  [{r.attack_name}]  d20=", font=_F8).pack(side="left")
            tk.Label(dice_frame, text=str(r.all_d20s[0] if r.all_d20s else r.d20),
                     font=_F8B).pack(side="left")
            for dropped in (r.all_d20s[1:] if r.all_d20s else []):
                tk.Label(dice_frame, text=f"|{dropped}", fg="#aaaaaa", font=_F8).pack(side="left")
            tk.Label(dice_frame, text=f" → total {r.total}", font=_F8).pack(side="left")
            dice_frame.grid(row=row, column=0, sticky="w", padx=4, pady=1)

            color = "#cc3333" if outcome == "MISS" else ("#cc7700" if outcome == "CRIT" else "#228822")
            tk.Label(parent, text=outcome, fg=color, font=_F8B, width=5).grid(
                row=row, column=1, padx=2, pady=1)

            if r.is_hit:
                parts = [f"{r.dmg1} {r.dmg_type_1}"]
                if r.dmg2 > 0:
                    parts.append(f"{r.dmg2} {r.dmg_type_2}")
                dmg_str = " + ".join(parts) + f" = {r.dmg1 + r.dmg2}"
                force_save, save_dc, save_type = r.save_info
                if force_save:
                    dmg_str += f"  | DC {save_dc} {save_type} save"
            else:
                dmg_str = "—"
            tk.Label(parent, text=dmg_str, anchor="w", font=_F8).grid(
                row=row, column=2, sticky="w", padx=4, pady=1)
            row += 1

        tk.Label(parent, text=f"  Total damage: {format_damage_breakdown(result.rolls)}",
                 font=("Helvetica", 9, "bold"), anchor="w").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=4, pady=(2, 2))

    def _log_roll(result, attacker_name: str, defender_name: str, override: str) -> None:
        block = tk.Frame(log_inner, bd=1, relief="groove")
        _build_block(block, result, attacker_name, defender_name, override)
        if _log_blocks:
            block.pack(side="top", fill="x", anchor="w", padx=2, pady=2, before=_log_blocks[0])
        else:
            block.pack(side="top", fill="x", anchor="w", padx=2, pady=2)
        _log_blocks.insert(0, block)
        while len(_log_blocks) > _LOG_CAP:
            _log_blocks.pop().destroy()
        log_canvas.update_idletasks()
        log_canvas.yview_moveto(0.0)  # show newest

    # ── roll ──────────────────────────────────────────────────────────────────
    def _do_roll() -> None:
        from dataclasses import replace as _replace

        attacker_name = GSM.OneAttacker_str.get()
        mo = _monster_by_name(attacker_name)
        if mo is None:
            return
        monster_data = mo.to_data()
        override = GSM.Override_roll_type_str.get()

        # Selected specs, each forced to the chosen roll type.
        chosen_specs = [
            _replace(spec, roll_type=override)
            for spec, var in zip(_attack_state["specs"], _attack_state["vars"])
            if var.get()
        ]
        single_monster = _replace(monster_data, attacks=chosen_specs)

        defender_name = GSM.OneDefender_str.get()
        player_data = _defender_data(defender_name)
        # "Roll with" overrides EVERYTHING — blank the defender's imposed adv/disadv
        # so it can't combine with (and dilute) the user's chosen roll type.
        player_data.imposed_roll_type = "Normal"

        settings = CombatSettings(
            meets_it_beats_it=GSM.Meets_it_beats_it_bool.get(),
            crits_double_dmg=GSM.Crits_double_dmg_bool.get(),
            crits_extra_die_is_max=GSM.Crits_extra_die_is_max_bool.get(),
            nat1_always_miss=GSM.Nat1_always_miss_bool.get(),
            adv_combine=GSM.Adv_combine_bool.get(),
            adv_mode=GSM.Adv_mode.get(),
        )

        if chosen_specs:
            result = _engine_compute(single_monster, player_data, settings)
        else:
            from engine.combat import AttackResult
            result = AttackResult(hits=[], dmgs1=[], dmgs2=[], dmg_type_1="", dmg_type_2="",
                                  save_info=(False, 0, ""), rolls=[])
        _log_roll(result, attacker_name, defender_name, override)

    tk.Button(GSM.Attack_frame, text="Roll attack", command=_do_roll,
              font=GSM.Title_font, padx=9, background="grey").place(x=_X_LABEL, y=_Y_BUTTON)

    # Rebuild attack checkboxes whenever the attacker changes; populate now.
    _trace_ids.append(GSM.OneAttacker_str.trace_add("write", _rebuild_attack_checkboxes))
    _rebuild_attack_checkboxes()
