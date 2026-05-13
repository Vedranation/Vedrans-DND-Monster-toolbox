"""Parser for 5etools monster JSON statblocks → MonsterData."""

from __future__ import annotations

import math
import re

from engine.models import AttackSpec, MonsterData

_SIZE_MAP = {
    "T": "Tiny", "S": "Small", "M": "Medium",
    "L": "Large", "H": "Huge", "G": "Gargantuan",
}

_VALID_DICE = {"d4", "d6", "d8", "d10", "d12", "d20", "d100"}

# Damage types that exist in our tool
_KNOWN_DMG_TYPES = {
    "bludgeoning", "piercing", "slashing", "acid", "cold", "fire",
    "force", "lightning", "thunder", "necrotic", "poison", "psychic", "radiant",
}

# Condition values we track
_KNOWN_CONDITIONS = {
    "blinded", "charmed", "deafened", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified",
    "poisoned", "prone", "restrained", "stunned", "unconscious",
}

_WORDS_TO_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}

_SAVE_ABBREVS = {
    "strength": "STR", "dexterity": "DEX", "constitution": "CON",
    "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ability_mod(score: int) -> int:
    return math.floor((score - 10) / 2)


def _parse_signed_int(s: str) -> int:
    try:
        return int(str(s).strip().replace(" ", ""))
    except (ValueError, TypeError):
        return 0


def _parse_ac(ac_list: list) -> int:
    if not ac_list:
        return 10
    first = ac_list[0]
    if isinstance(first, int):
        return first
    if isinstance(first, dict):
        return first.get("ac", 10)
    return 10


def _parse_creature_type(type_field) -> str:
    if isinstance(type_field, str):
        return type_field.capitalize()
    if isinstance(type_field, dict):
        t = type_field.get("type", "")
        return t.capitalize() if isinstance(t, str) else ""
    return ""


def _parse_senses(senses_list: list) -> dict[str, int]:
    patterns = {
        "darkvision":  r"darkvision\s+(\d+)\s*ft",
        "blindsight":  r"blindsight\s+(\d+)\s*ft",
        "tremorsense": r"tremorsense\s+(\d+)\s*ft",
        "truesight":   r"truesight\s+(\d+)\s*ft",
    }
    result: dict[str, int] = {}
    for s in senses_list:
        sl = s.lower()
        for key, pat in patterns.items():
            m = re.search(pat, sl)
            if m:
                result[key] = int(m.group(1))
    return result


def _parse_dmg_list(items: list) -> list[str]:
    """Convert 5etools immune/resist list to our damage type strings."""
    result: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue  # skip complex conditional objects
        il = item.lower()
        # "bludgeoning, piercing, and slashing from nonmagical attacks" → extract all
        for dt in sorted(_KNOWN_DMG_TYPES, key=len, reverse=True):
            if dt in il and dt not in result:
                result.append(dt)
    return result


def _parse_condition_immunities(items: list) -> set[str]:
    result: set[str] = set()
    for item in items:
        if isinstance(item, str) and item.lower() in _KNOWN_CONDITIONS:
            result.add(item.lower())
    return result


def _parse_saving_throws(data: dict) -> dict[str, tuple[int, str]]:
    """Build saving throw dict from ability scores + proficiency saves."""
    key_map = {
        "str": "STR", "dex": "DEX", "con": "CON",
        "int": "INT", "wis": "WIS", "cha": "CHA",
    }
    scores = {
        "STR": data.get("str", 10),
        "DEX": data.get("dex", 10),
        "CON": data.get("con", 10),
        "INT": data.get("int", 10),
        "WIS": data.get("wis", 10),
        "CHA": data.get("cha", 10),
    }
    proficiency_saves = data.get("save", {})
    result: dict[str, tuple[int, str]] = {}
    for short, full in key_map.items():
        if short in proficiency_saves:
            mod = _parse_signed_int(proficiency_saves[short])
        else:
            mod = _ability_mod(scores[full])
        result[full] = (mod, "Normal")
    return result


# ── Damage roll parsing ───────────────────────────────────────────────────────

def _parse_damage_roll(dmg_str: str) -> tuple[int, str, int]:
    """'2d6 + 3' → (2, 'd6', 3).  '3d4' → (3, 'd4', 0)."""
    dmg_str = dmg_str.strip()
    m = re.match(r'(\d+)\s*d\s*(\d+)\s*([+\-]\s*\d+)?', dmg_str)
    if m:
        n = int(m.group(1))
        die = f"d{m.group(2)}"
        if die not in _VALID_DICE:
            die = "d6"
        flat = _parse_signed_int(m.group(3)) if m.group(3) else 0
        return n, die, flat
    try:
        return 0, "d6", int(dmg_str)
    except ValueError:
        return 1, "d6", 0


def _dmg_type_after(text: str, pos: int) -> str:
    """Return first recognised damage type within 90 chars after pos."""
    window = text[pos: pos + 90].lower()
    for dt in sorted(_KNOWN_DMG_TYPES, key=len, reverse=True):
        idx = window.find(dt)
        if idx != -1:
            return dt
    return "bludgeoning"


# ── Attack range detection ────────────────────────────────────────────────────

def _get_attack_range_ft(entry: str) -> int:
    """
    Return the effective attack range in feet from one action entry string.
    Prefers "range X ft" (ranged attack) over "reach X ft" (extended melee).
    Falls back to 5 ft (standard melee).
    """
    # "range 60 ft." or "range 100/400 ft."
    rm = re.search(r'\brange\b\s+(\d+)(?:/\d+)?\s*ft', entry, re.IGNORECASE)
    if rm:
        return int(rm.group(1))
    # "reach 10 ft."
    reach_m = re.search(r'\breach\b\s+(\d+)\s*ft', entry, re.IGNORECASE)
    if reach_m:
        return int(reach_m.group(1))
    return 5


# ── Multiattack count parsing ─────────────────────────────────────────────────

def _multiattack_counts(multiattack_text: str, names: list[str]) -> dict[str, int]:
    """Extract per-attack counts from multiattack prose."""
    counts: dict[str, int] = {}
    for name in names:
        # "two Branch attacks" / "3 Branch attacks"
        m = re.search(
            rf'(one|two|three|four|five|six|\d+)\s+{re.escape(name)}\b',
            multiattack_text, re.IGNORECASE
        )
        if m:
            val = m.group(1).lower()
            counts[name] = _WORDS_TO_NUM.get(val, int(val) if val.isdigit() else 1)
            continue
        # "one with its tentacles" / "one with its bite"
        m2 = re.search(
            rf'\bone\s+with\s+its\s+{re.escape(name)}\b',
            multiattack_text, re.IGNORECASE
        )
        if m2:
            counts[name] = 1
    return counts


# ── Attack parsing ────────────────────────────────────────────────────────────

def _parse_attacks(actions: list) -> list[tuple[AttackSpec, int]]:
    """
    Parse 5etools action list into (AttackSpec, range_ft) pairs.
    Skips Multiattack and actions that have no {@hit} tag.
    """
    # Collect multiattack prose for count extraction later
    multiattack_text = ""
    for action in actions:
        if action.get("name", "").lower() == "multiattack":
            entries = action.get("entries", [])
            multiattack_text = entries[0] if entries and isinstance(entries[0], str) else ""
            break

    results: list[tuple[AttackSpec, int]] = []
    attack_names: list[str] = []

    for action in actions:
        raw_name = action.get("name", "")
        if raw_name.lower() == "multiattack":
            continue

        # Strip inline recharge tags: "Acid Breath {@recharge 5}" → "Acid Breath"
        clean_name = re.sub(r'\s*\{@[^}]+\}.*', '', raw_name).strip()

        entries = action.get("entries", [])
        for entry in entries:
            if not isinstance(entry, str):
                continue

            hit_m = re.search(r'\{@hit\s+(-?\d+)\}', entry)
            if not hit_m:
                break  # No attack roll — skip this action

            to_hit = int(hit_m.group(1))
            range_ft = _get_attack_range_ft(entry)

            # All {@damage ...} in this entry
            dmg_iter = list(re.finditer(r'\{@damage\s+([^}]+)\}', entry))

            n1, die1, flat1, type1 = 1, "d6", 0, "bludgeoning"
            n2, die2, flat2, type2 = 0, "d6", 0, "None"

            if dmg_iter:
                n1, die1, flat1 = _parse_damage_roll(dmg_iter[0].group(1))
                type1 = _dmg_type_after(entry, dmg_iter[0].end())

            if len(dmg_iter) >= 2:
                n2, die2, flat2 = _parse_damage_roll(dmg_iter[1].group(1))
                type2 = _dmg_type_after(entry, dmg_iter[1].end())

            # On-hit saving throw
            force_save = False
            save_dc = 8
            save_stat = "CON"
            dc_m = re.search(r'\{@dc\s+(\d+)\}', entry)
            if dc_m:
                force_save = True
                save_dc = int(dc_m.group(1))
                st_m = re.search(
                    r'(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving\s+throw',
                    entry, re.IGNORECASE
                )
                if st_m:
                    save_stat = _SAVE_ABBREVS.get(st_m.group(1).lower(), "CON")

            spec = AttackSpec(
                name=clean_name,
                to_hit_mod=to_hit,
                roll_type="Normal",
                n_attacks=1,
                dmg_n_die_1=n1,
                dmg_die_type_1=die1,
                dmg_flat_1=flat1,
                dmg_type_1=type1,
                dmg_n_die_2=n2,
                dmg_die_type_2=die2,
                dmg_flat_2=flat2,
                dmg_type_2=type2 if n2 > 0 else "None",
                crit_number=20,
                on_hit_force_save=force_save,
                on_hit_save_dc=save_dc,
                on_hit_save_type=save_stat,
            )

            results.append((spec, range_ft))
            attack_names.append(clean_name)
            break  # one entry per action is enough

    # Apply multiattack repetition counts
    if multiattack_text and attack_names:
        counts = _multiattack_counts(multiattack_text, attack_names)
        for spec, _ in results:
            if spec.name in counts:
                spec.n_attacks = counts[spec.name]

    return results


# ── Main entry point ──────────────────────────────────────────────────────────

def parse_5etools_monster(data: dict) -> MonsterData:
    """Convert a 5etools monster JSON dict into a MonsterData instance."""

    name = data.get("name", "Unknown")

    size_code = (data.get("size") or ["M"])[0]
    creature_size = _SIZE_MAP.get(size_code, "Medium")

    creature_type = _parse_creature_type(data.get("type", ""))

    ac = _parse_ac(data.get("ac", [10]))
    max_hp = data.get("hp", {}).get("average", 0)

    # Speeds (fly can be True for "hover" without numeric speed — treat as 0)
    raw_speed = data.get("speed", {})
    def _speed_val(key: str) -> int:
        v = raw_speed.get(key, 0)
        return int(v) if isinstance(v, int) else 0

    speeds = {
        "walk":   _speed_val("walk"),
        "fly":    _speed_val("fly"),
        "climb":  _speed_val("climb"),
        "burrow": _speed_val("burrow"),
        "swim":   _speed_val("swim"),
    }

    saving_throws = _parse_saving_throws(data)
    senses = _parse_senses(data.get("senses", []))
    passive_perception = data.get("passive", 10)

    damage_immunities  = _parse_dmg_list(data.get("immune", []))
    damage_resistances = _parse_dmg_list(data.get("resist", []))
    condition_immunities = _parse_condition_immunities(data.get("conditionImmune", []))

    # Attacks
    attack_tuples = _parse_attacks(data.get("action", []))

    attacks = [spec for spec, _ in attack_tuples] if attack_tuples else [AttackSpec()]

    # Monster-level attack range = max range across all attacks
    attack_range_ft = max((r for _, r in attack_tuples), default=5)
    # Highlight range matches attack range by default
    highlight_range_ft = attack_range_ft

    dex_mod = _ability_mod(data.get("dex", 10))
    # 2024 rules: data["initiative"] may carry a proficiency bonus on top of DEX mod
    initiative_proficiency = data.get("initiative", {}).get("proficiency", 0) if isinstance(data.get("initiative"), dict) else 0
    initiative_mod = dex_mod + (initiative_proficiency if isinstance(initiative_proficiency, int) else 0)

    return MonsterData(
        name=name,
        ac=ac,
        max_hp=max_hp,
        attack_range_ft=attack_range_ft,
        ignore_ranged_in_melee=False,
        highlight_range_ft=highlight_range_ft,
        attacks=attacks,
        saving_throws=saving_throws,
        speeds=speeds,
        passive_perception=passive_perception,
        initiative_mod=initiative_mod,
        creature_type=creature_type,
        creature_size=creature_size,
        senses=senses,
        damage_resistances=damage_resistances,
        damage_immunities=damage_immunities,
        condition_immunities=condition_immunities,
    )
