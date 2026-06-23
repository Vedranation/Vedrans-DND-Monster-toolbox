"""Parser for 5etools spell JSON → GSM spell library dict."""

from __future__ import annotations

import re

_SCHOOL_MAP = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "V": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
    "P": "Other",   # Psionic (rare)
    "G": "Other",   # Generic (rare)
}


# ── tag stripping ─────────────────────────────────────────────────────────────

def _strip_tags(text: str) -> str:
    """Replace 5etools {@tag content} markers with readable plain text."""
    def _replace(m: re.Match) -> str:
        tag = m.group(1).lower()
        content = m.group(2)
        parts = [p.strip() for p in content.split("|")]

        if tag in ("b", "bold", "i", "italic", "s", "strike", "u", "underline", "sup", "sub"):
            return parts[0]
        if tag in ("damage", "dice", "d20"):
            return parts[0]
        if tag == "scaledamage":
            # {@scaledamage base|range|per-slot} — show the per-slot increment
            return parts[-1] if len(parts) >= 3 else parts[0]
        if tag == "hit":
            val = parts[0]
            return f"+{val}" if not val.startswith(("+", "-")) else val
        if tag == "dc":
            return f"DC {parts[0]}"
        if tag == "chance":
            return f"{parts[0]}%"
        if tag in ("condition", "status"):
            return parts[0]
        # Generic: if a third segment exists it is the display override
        if len(parts) >= 3 and parts[2]:
            return parts[2]
        return parts[0]

    return re.sub(r'\{@(\w+)\s+([^}]*)\}', _replace, text)


# ── entry text extraction ─────────────────────────────────────────────────────

def _extract_text(entry) -> str:
    """Recursively extract plain text from a 5etools entry (string or nested dict)."""
    if isinstance(entry, str):
        return _strip_tags(entry)
    if not isinstance(entry, dict):
        return ""
    etype = entry.get("type", "")
    if etype in ("entries", "section"):
        name = entry.get("name", "")
        sub = "\n".join(filter(None, (_extract_text(e) for e in entry.get("entries", []))))
        return f"{name}:\n{sub}" if name else sub
    if etype == "list":
        return "\n".join(f"• {_extract_text(i)}" for i in entry.get("items", []))
    if etype == "table":
        cols = " | ".join(entry.get("colLabels", []))
        return f"[Table: {cols}]" if cols else "[Table]"
    if etype == "inset":
        name = entry.get("name", "")
        sub = "\n".join(filter(None, (_extract_text(e) for e in entry.get("entries", []))))
        return f"[{name}]\n{sub}" if name else sub
    return ""


# ── field parsers ─────────────────────────────────────────────────────────────

def _parse_casting_time(time_list: list) -> str:
    if not time_list:
        return ""
    first = time_list[0]
    number = first.get("number", 1)
    unit = first.get("unit", "action")
    plural = "s" if number > 1 and not unit.endswith("s") else ""
    return f"{number} {unit}{plural}"


def _parse_range(range_obj: dict) -> str:
    rtype = range_obj.get("type", "")
    if rtype == "touch":
        return "Touch"
    if rtype == "self":
        return "Self"
    if rtype == "special":
        return "Special"
    if rtype == "sight":
        return "Sight"
    if rtype == "unlimited":
        return "Unlimited"
    dist = range_obj.get("distance", {})
    dtype = dist.get("type", "")
    amount = dist.get("amount", 0)
    if dtype == "feet":
        return f"{amount} ft."
    if dtype == "miles":
        return f"{amount} mile{'s' if amount != 1 else ''}"
    if dtype in ("self", "touch", "unlimited", "sight", "special"):
        return dtype.capitalize()
    return str(amount) if amount else rtype.capitalize()


def _parse_duration(duration_list: list) -> tuple[str, bool]:
    """Returns (human-readable duration string, is_concentration)."""
    if not duration_list:
        return "Instantaneous", False
    first = duration_list[0]
    dtype = first.get("type", "instant")
    concentration = bool(first.get("concentration"))
    if dtype == "instant":
        return "Instantaneous", concentration
    if dtype == "permanent":
        ends = first.get("ends", [])
        return (f"Until {' or '.join(ends)}" if ends else "Permanent"), concentration
    if dtype == "special":
        return "Special", concentration
    if dtype == "timed":
        dur = first.get("duration", {})
        amount = dur.get("amount", 1)
        unit = dur.get("type", "round")
        plural = "s" if amount > 1 else ""
        return f"{amount} {unit}{plural}", concentration
    return dtype.capitalize(), concentration


def _extract_dice(data: dict) -> tuple[int, str]:
    """Find the spell's first damage dice expression (e.g. Fireball → (8, 'd6')).

    Scans the raw {@damage NdX} / {@dice NdX} tags in the entries. Returns
    (count, die) or (0, '') if none — lets the UI offer a one-click roll.
    """
    def _walk(entry):
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            parts = [_walk(e) for e in entry.get("entries", entry.get("items", []))]
            return " ".join(p for p in parts if p)
        return ""

    blob = " ".join(filter(None, (_walk(e) for e in data.get("entries", []))))
    m = re.search(r'\{@(?:damage|dice)\s+(\d+)d(\d+)', blob)
    if m:
        return int(m.group(1)), f"d{m.group(2)}"
    return 0, ""


# ── main entry point ──────────────────────────────────────────────────────────

def parse_5etools_spell(data: dict) -> dict:
    """Convert a 5etools spell JSON dict to a GSM spell library entry."""
    name = data.get("name", "Unknown")
    level = data.get("level", 0)
    school = _SCHOOL_MAP.get(data.get("school", ""), "Other")

    casting_time = _parse_casting_time(data.get("time", []))
    range_str = _parse_range(data.get("range", {}))
    duration_str, concentration = _parse_duration(data.get("duration", []))

    components = data.get("components", {})
    comp_v = bool(components.get("v"))
    comp_s = bool(components.get("s"))
    m_val = components.get("m")
    comp_m = m_val is not None and m_val is not False
    material_cost_gp = ""
    material_consumed = False
    if comp_m:
        material_text = ""
        if isinstance(m_val, str):
            material_text = m_val
        elif isinstance(m_val, dict):
            material_text = m_val.get("text", "")
            material_consumed = bool(m_val.get("consume"))
            raw_cp = m_val.get("cost")
            if raw_cp is not None:
                gp = int(raw_cp) // 100
                if gp > 0:
                    material_cost_gp = str(gp)
        # Fallback: regex first GP amount from description text
        if not material_cost_gp and material_text:
            gp_m = re.search(r'(\d+)\+?\s*[Gg][Pp]', material_text)
            if gp_m:
                material_cost_gp = gp_m.group(1)

    # Build description from main entries + higher-level scaling block
    desc_parts: list[str] = []
    for entry in data.get("entries", []):
        text = _extract_text(entry)
        if text:
            desc_parts.append(text)
    for hl_block in data.get("entriesHigherLevel", []):
        text = _extract_text(hl_block)
        if text:
            desc_parts.append(text)
    description = "\n\n".join(desc_parts)

    dice_count, dice_type = _extract_dice(data)

    return {
        "name": name,
        "level": level,
        "school": school,
        "casting_time": casting_time,
        "range": range_str,
        "duration": duration_str,
        "concentration": concentration,
        "component_v": comp_v,
        "component_s": comp_s,
        "component_m": comp_m,
        "material_cost": material_cost_gp,
        "material_consumed": material_consumed,
        "description": description,
        "dice_count": dice_count,
        "dice_type": dice_type,
    }
