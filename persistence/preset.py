"""Named-preset persistence — schema v2 JSON in the Presets/ directory."""

from __future__ import annotations

import json
from pathlib import Path

_PRESETS_DIR = Path("Presets")


def save_preset(name: str, data: dict) -> None:
    _PRESETS_DIR.mkdir(exist_ok=True)
    payload = {"schema_version": 2, "name": name, "data": data}
    (_PRESETS_DIR / f"{name}.json").write_text(json.dumps(payload, indent=4), encoding="utf-8")


def load_preset(name: str) -> dict:
    path = _PRESETS_DIR / f"{name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "schema_version" not in raw:
        raw = migrate_v1_to_v2(raw, name)
    return raw["data"]


def list_presets() -> list[str]:
    if not _PRESETS_DIR.exists():
        return []
    return sorted(p.stem for p in _PRESETS_DIR.glob("*.json"))


def delete_preset(name: str) -> None:
    path = _PRESETS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()


def migrate_v1_to_v2(v1_dict: dict, name: str = "preset1") -> dict:
    return {"schema_version": 2, "name": name, "data": v1_dict}
