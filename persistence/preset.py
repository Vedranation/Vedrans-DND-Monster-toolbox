"""Named-preset persistence — schema v2 JSON.

The presets directory is resolved at call time so the host can point it anywhere:
an explicit override via `set_presets_dir(...)`, else the `DND_PRESETS_DIR` env var,
else `./Presets`. The Android wrapper sets it to the app's internal storage dir.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Explicit override (highest priority); None → fall back to env / default.
_PRESETS_DIR: Path | None = None


def set_presets_dir(path) -> None:
    """Point preset storage at a specific directory (e.g. Android internal storage)."""
    global _PRESETS_DIR
    _PRESETS_DIR = Path(path) if path else None


def _dir() -> Path:
    if _PRESETS_DIR is not None:
        return _PRESETS_DIR
    return Path(os.environ.get("DND_PRESETS_DIR", "Presets"))


def save_preset(name: str, data: dict) -> None:
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 2, "name": name, "data": data}
    (d / f"{name}.json").write_text(json.dumps(payload, indent=4), encoding="utf-8")


def load_preset(name: str) -> dict:
    path = _dir() / f"{name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "schema_version" not in raw:
        raw = migrate_v1_to_v2(raw, name)
    return raw["data"]


def list_presets() -> list[str]:
    d = _dir()
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def delete_preset(name: str) -> None:
    path = _dir() / f"{name}.json"
    if path.exists():
        path.unlink()


def migrate_v1_to_v2(v1_dict: dict, name: str = "preset1") -> dict:
    return {"schema_version": 2, "name": name, "data": v1_dict}
