"""Build a canonical name catalog from the 5e.tools data mirror.

Run offline to (re)generate ``search/data/names_index.json``::

    python -m search.build_names

The bundled index seeds fuzzy "did you mean" correction so misheard or
misspelled input resolves to the real entity name before searching.
Requires network access to the 5e.tools GitHub mirror.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

_BASE = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/master/data/"
_OUT = Path(__file__).parent / "data" / "names_index.json"


def _get(rel_path: str) -> dict:
    with urllib.request.urlopen(_BASE + rel_path, timeout=25) as resp:
        return json.load(resp)


def _add(into: dict[str, str], entry: dict) -> None:
    """Record name → source (first source wins, for a stable deep-link)."""
    name = entry.get("name")
    source = entry.get("source", "")
    if name:
        into.setdefault(name, source)


def _names_from_indexed(folder: str, entry_key: str) -> dict[str, str]:
    """Collect {name: source} from a folder that has an index.json of source files."""
    names: dict[str, str] = {}
    try:
        index = _get(f"{folder}/index.json")
    except Exception as exc:  # noqa: BLE001 — network/parse failures are non-fatal
        print(f"  ! skipped {folder}: {exc}")
        return {}
    for i, fname in enumerate(index.values(), 1):
        try:
            data = _get(f"{folder}/{fname}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {fname}: {exc}")
            continue
        for entry in data.get(entry_key, []):
            _add(names, entry)
        print(f"  {folder}: {i}/{len(index)} files, {len(names)} names", end="\r")
    print()
    return names


def _names_from_file(rel_path: str, *entry_keys: str) -> dict[str, str]:
    """Collect {name: source} from a single data file (one or more top-level keys)."""
    names: dict[str, str] = {}
    try:
        data = _get(rel_path)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! skipped {rel_path}: {exc}")
        return {}
    for key in entry_keys:
        for entry in data.get(key, []):
            _add(names, entry)
    return names


def build() -> dict[str, dict[str, str]]:
    print("Fetching spells…")
    spells = _names_from_indexed("spells", "spell")
    print("Fetching bestiary (monsters)…")
    monsters = _names_from_indexed("bestiary", "monster")
    print("Fetching items…")
    items = _names_from_file("items.json", "item")
    for name, source in _names_from_file("items-base.json", "baseitem").items():
        items.setdefault(name, source)
    print("Fetching feats…")
    feats = _names_from_file("feats.json", "feat")

    index = {
        "spell": spells,
        "monster": monsters,
        "item": items,
        "feat": feats,
    }
    for cat, names in index.items():
        print(f"  {cat}: {len(names)}")
    return index


def main() -> None:
    index = build()
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    with _OUT.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0)
    total = sum(len(v) for v in index.values())
    print(f"Wrote {total} names to {_OUT}")


if __name__ == "__main__":
    main()
