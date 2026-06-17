"""Pure (de)serialization between domain models and preset-JSON dicts.

Relocated out of tabs/MainSettings.py so the logic is reusable by both the
desktop UI and the future web server, with no Tkinter/GSM dependency. The dict
shape is the schema-v2 preset format (see persistence/preset.py); field keys are
kept verbatim for backward compatibility with existing saved presets.
"""

from __future__ import annotations

from engine.models import AttackSpec, MonsterData, PlayerData


# ── AttackSpec ⇄ dict ───────────────────────────────────────────────────────

def attack_spec_to_dict(atk: AttackSpec) -> dict:
    return {
        "name": atk.name,
        "to_hit_mod": atk.to_hit_mod,
        "roll_type": atk.roll_type,
        "n_attacks": atk.n_attacks,
        "dmg_n_die_1": atk.dmg_n_die_1,
        "dmg_die_type_1": atk.dmg_die_type_1,
        "dmg_flat_1": atk.dmg_flat_1,
        "dmg_type_1": atk.dmg_type_1,
        "dmg_n_die_2": atk.dmg_n_die_2,
        "dmg_die_type_2": atk.dmg_die_type_2,
        "dmg_flat_2": atk.dmg_flat_2,
        "dmg_type_2": atk.dmg_type_2,
        "crit_number": atk.crit_number,
        "brutal_critical": atk.brutal_critical,
        "savage_attacker": atk.savage_attacker,
        "reroll_1_on_hit": atk.reroll_1_on_hit,
        "reroll_1_2_dmg": atk.reroll_1_2_dmg,
        "bane": atk.bane,
        "bless": atk.bless,
        "on_hit_force_save": atk.on_hit_force_save,
        "on_hit_save_dc": atk.on_hit_save_dc,
        "on_hit_save_type": atk.on_hit_save_type,
    }


def dict_to_attack_spec(d: dict) -> AttackSpec:
    return AttackSpec(
        name=d.get("name", "Attack"),
        to_hit_mod=d.get("to_hit_mod", 5),
        roll_type=d.get("roll_type", "Normal"),
        n_attacks=d.get("n_attacks", 1),
        dmg_n_die_1=d.get("dmg_n_die_1", 1),
        dmg_die_type_1=d.get("dmg_die_type_1", "d6"),
        dmg_flat_1=d.get("dmg_flat_1", 0),
        dmg_type_1=d.get("dmg_type_1", "slashing"),
        dmg_n_die_2=d.get("dmg_n_die_2", 0),
        dmg_die_type_2=d.get("dmg_die_type_2", "d6"),
        dmg_flat_2=d.get("dmg_flat_2", 0),
        dmg_type_2=d.get("dmg_type_2", "None"),
        crit_number=d.get("crit_number", 20),
        brutal_critical=d.get("brutal_critical", False),
        savage_attacker=d.get("savage_attacker", False),
        reroll_1_on_hit=d.get("reroll_1_on_hit", False),
        reroll_1_2_dmg=d.get("reroll_1_2_dmg", False),
        bane=d.get("bane", False),
        bless=d.get("bless", False),
        on_hit_force_save=d.get("on_hit_force_save", d.get("on_hit_force_saving_throw_bool", False)),
        on_hit_save_dc=d.get("on_hit_save_dc", 8),
        on_hit_save_type=d.get("on_hit_save_type", "CON"),
    )


# ── MonsterData ⇄ dict ──────────────────────────────────────────────────────

def serialize_monster(m: MonsterData) -> dict:
    st = m.saving_throws
    sp = m.speeds
    se = m.senses
    return {
        "name_str": m.name,
        "ac_int": m.ac,
        "max_hp_int": m.max_hp,
        "attack_range_ft": m.attack_range_ft,
        "ignore_ranged_in_melee": m.ignore_ranged_in_melee,
        "highlight_range_ft": m.highlight_range_ft,
        "attacks": [attack_spec_to_dict(a) for a in m.attacks],
        "walking_speed_int": sp.get("walk", 0),
        "flying_speed_int": sp.get("fly", 0),
        "climbing_speed_int": sp.get("climb", 0),
        "burrowing_speed_int": sp.get("burrow", 0),
        "swimming_speed_int": sp.get("swim", 0),
        "creature_type": m.creature_type,
        "creature_size": m.creature_size,
        "senses_darkvision": se.get("darkvision", 0),
        "senses_blindsight": se.get("blindsight", 0),
        "senses_tremorsense": se.get("tremorsense", 0),
        "senses_truesight": se.get("truesight", 0),
        "damage_resistances": list(m.damage_resistances),
        "damage_immunities": list(m.damage_immunities),
        "damage_vulnerabilities": list(m.damage_vulnerabilities),
        "condition_immunities": list(m.condition_immunities),
        "savingthrow_str_mod_int": st.get("STR", (0, "Normal"))[0],
        "savingthrow_str_roll_type_str": st.get("STR", (0, "Normal"))[1],
        "savingthrow_dex_mod_int": st.get("DEX", (0, "Normal"))[0],
        "savingthrow_dex_roll_type_str": st.get("DEX", (0, "Normal"))[1],
        "savingthrow_con_mod_int": st.get("CON", (0, "Normal"))[0],
        "savingthrow_con_roll_type_str": st.get("CON", (0, "Normal"))[1],
        "savingthrow_int_mod_int": st.get("INT", (0, "Normal"))[0],
        "savingthrow_int_roll_type_str": st.get("INT", (0, "Normal"))[1],
        "savingthrow_wis_mod_int": st.get("WIS", (0, "Normal"))[0],
        "savingthrow_wis_roll_type_str": st.get("WIS", (0, "Normal"))[1],
        "savingthrow_cha_mod_int": st.get("CHA", (0, "Normal"))[0],
        "savingthrow_cha_roll_type_str": st.get("CHA", (0, "Normal"))[1],
        "passiveperception_int": m.passive_perception,
        "initiative_mod": m.initiative_mod,
    }


def deserialize_monster(d: dict) -> MonsterData:
    if "attacks" in d:
        attacks = [dict_to_attack_spec(a) for a in d["attacks"]]
    else:
        # Backward compat: single flat attack from old preset format
        attacks = [AttackSpec(
            name="Attack",
            to_hit_mod=d.get("to_hit_mod", 5),
            roll_type=d.get("roll_type", "Normal"),
            n_attacks=d.get("n_attacks", 1),
            dmg_n_die_1=d.get("dmg_n_die_1", 1),
            dmg_die_type_1=d.get("dmg_die_type_1", "d6"),
            dmg_flat_1=d.get("dmg_flat_1", 0),
            dmg_type_1=d.get("dmg_type_1", "slashing"),
            dmg_n_die_2=d.get("dmg_n_die_2", 0),
            dmg_die_type_2=d.get("dmg_die_type_2", "d6"),
            dmg_flat_2=d.get("dmg_flat_2", 0),
            dmg_type_2=d.get("dmg_type_2", "None"),
            crit_number=d.get("crit_number", 20),
            brutal_critical=d.get("brutal_critical", False),
            savage_attacker=d.get("savage_attacker", False),
            reroll_1_on_hit=d.get("reroll_1_on_hit", False),
            reroll_1_2_dmg=d.get("reroll_1_2_dmg", False),
            bane=d.get("bane", False),
            bless=d.get("bless", False),
            on_hit_force_save=d.get("on_hit_force_saving_throw_bool", False),
            on_hit_save_dc=d.get("on_hit_save_dc", 8),
            on_hit_save_type=d.get("on_hit_save_type", "CON"),
        )]
    return MonsterData(
        name=d.get("name_str", "Monster"),
        ac=d.get("ac_int", 13),
        max_hp=d.get("max_hp_int", 0),
        attack_range_ft=d.get("attack_range_ft", 5),
        ignore_ranged_in_melee=d.get("ignore_ranged_in_melee", False),
        highlight_range_ft=d.get("highlight_range_ft", 5),
        attacks=attacks,
        saving_throws={
            "STR": (d.get("savingthrow_str_mod_int", 0), d.get("savingthrow_str_roll_type_str", "Normal")),
            "DEX": (d.get("savingthrow_dex_mod_int", 0), d.get("savingthrow_dex_roll_type_str", "Normal")),
            "CON": (d.get("savingthrow_con_mod_int", 0), d.get("savingthrow_con_roll_type_str", "Normal")),
            "INT": (d.get("savingthrow_int_mod_int", 0), d.get("savingthrow_int_roll_type_str", "Normal")),
            "WIS": (d.get("savingthrow_wis_mod_int", 0), d.get("savingthrow_wis_roll_type_str", "Normal")),
            "CHA": (d.get("savingthrow_cha_mod_int", 0), d.get("savingthrow_cha_roll_type_str", "Normal")),
        },
        speeds={
            "walk": d.get("walking_speed_int", 0),
            "fly": d.get("flying_speed_int", 0),
            "climb": d.get("climbing_speed_int", 0),
            "burrow": d.get("burrowing_speed_int", 0),
            "swim": d.get("swimming_speed_int", 0),
        },
        passive_perception=d.get("passiveperception_int", 10),
        initiative_mod=d.get("initiative_mod", 0),
        creature_type=d.get("creature_type", ""),
        creature_size=d.get("creature_size", "Medium"),
        senses={
            "darkvision": d.get("senses_darkvision", 0),
            "blindsight": d.get("senses_blindsight", 0),
            "tremorsense": d.get("senses_tremorsense", 0),
            "truesight": d.get("senses_truesight", 0),
        },
        damage_resistances=d.get("damage_resistances", []),
        damage_immunities=d.get("damage_immunities", []),
        damage_vulnerabilities=d.get("damage_vulnerabilities", []),
        condition_immunities=set(d.get("condition_immunities", [])),
    )


# ── PlayerData ⇄ dict ───────────────────────────────────────────────────────

def serialize_player(p: PlayerData) -> dict:
    sk = p.skills
    return {
        "name_str": p.name,
        "ac_int": p.ac,
        "max_hp_int": p.max_hp,
        "attack_range_ft": p.attack_range_ft,
        "ignore_ranged_in_melee": p.ignore_ranged_in_melee,
        "highlight_range_ft": p.highlight_range_ft,
        "monster_roll_type_against_str": p.imposed_roll_type,
        "adamantine": p.adamantine,
        "perception_mod_int": sk.get("perception", (0, "Normal"))[0],
        "perception_roll_type_str": sk.get("perception", (0, "Normal"))[1],
        "investigation_mod_int": sk.get("investigation", (0, "Normal"))[0],
        "investigation_roll_type_str": sk.get("investigation", (0, "Normal"))[1],
        "arcana_mod_int": sk.get("arcana", (0, "Normal"))[0],
        "arcana_roll_type_str": sk.get("arcana", (0, "Normal"))[1],
        "insight_mod_int": sk.get("insight", (0, "Normal"))[0],
        "insight_roll_type_str": sk.get("insight", (0, "Normal"))[1],
        "stealth_mod_int": sk.get("stealth", (0, "Normal"))[0],
        "stealth_roll_type_str": sk.get("stealth", (0, "Normal"))[1],
        "passiveperception_int": p.passive_perception,
        "initiative_mod": p.initiative_mod,
    }


def deserialize_player(d: dict) -> PlayerData:
    return PlayerData(
        name=d.get("name_str", "Player"),
        ac=d.get("ac_int", 13),
        max_hp=d.get("max_hp_int", 0),
        attack_range_ft=d.get("attack_range_ft", 5),
        ignore_ranged_in_melee=d.get("ignore_ranged_in_melee", False),
        highlight_range_ft=d.get("highlight_range_ft", 5),
        imposed_roll_type=d.get("monster_roll_type_against_str", "Normal"),
        adamantine=d.get("adamantine", False),
        skills={
            "perception": (d.get("perception_mod_int", 0), d.get("perception_roll_type_str", "Normal")),
            "investigation": (d.get("investigation_mod_int", 0), d.get("investigation_roll_type_str", "Normal")),
            "arcana": (d.get("arcana_mod_int", 0), d.get("arcana_roll_type_str", "Normal")),
            "insight": (d.get("insight_mod_int", 0), d.get("insight_roll_type_str", "Normal")),
            "stealth": (d.get("stealth_mod_int", 0), d.get("stealth_roll_type_str", "Normal")),
        },
        passive_perception=d.get("passiveperception_int", 10),
        initiative_mod=d.get("initiative_mod", 0),
    )
