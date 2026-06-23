"""Round-trip tests for preset (de)serialization (persistence/appstate.py)."""

from engine.models import AttackSpec, MonsterData, PlayerData
from persistence.appstate import (
    deserialize_monster,
    deserialize_player,
    serialize_monster,
    serialize_player,
)


def _full_monster() -> MonsterData:
    return MonsterData(
        name="Treant",
        ac=16,
        max_hp=138,
        attack_range_ft=10,
        ignore_ranged_in_melee=True,
        highlight_range_ft=15,
        attacks=[
            AttackSpec(name="Slam", to_hit_mod=10, n_attacks=2, dmg_n_die_1=3,
                       dmg_die_type_1="d6", dmg_flat_1=6, dmg_type_1="bludgeoning"),
            AttackSpec(name="Hail of Bark", to_hit_mod=10, dmg_n_die_1=4,
                       dmg_die_type_1="d10", dmg_flat_1=6, dmg_type_1="piercing"),
        ],
        saving_throws={
            "STR": (6, "Advantage"), "DEX": (-1, "Normal"), "CON": (5, "Normal"),
            "INT": (1, "Normal"), "WIS": (3, "Normal"), "CHA": (1, "Disadvantage"),
        },
        speeds={"walk": 30, "fly": 0, "climb": 0, "burrow": 0, "swim": 0},
        passive_perception=13,
        initiative_mod=-1,
        creature_type="Plant",
        creature_size="Huge",
        senses={"darkvision": 60, "blindsight": 0, "tremorsense": 0, "truesight": 0},
        damage_resistances=["bludgeoning", "piercing"],
        damage_immunities=[],
        damage_vulnerabilities=["fire"],
        condition_immunities={"frightened"},
    )


def test_monster_round_trip_preserves_everything():
    original = _full_monster()
    restored = deserialize_monster(serialize_monster(original))
    assert restored == original  # dataclass __eq__ covers every field incl. attacks


def test_monster_vulnerabilities_persist():
    # Regression: vulnerabilities were previously dropped during save.
    restored = deserialize_monster(serialize_monster(_full_monster()))
    assert restored.damage_vulnerabilities == ["fire"]


def test_monster_backward_compat_flat_attack():
    # Old presets stored a single flat attack (no "attacks" list).
    legacy = {
        "name_str": "Goblin", "ac_int": 15, "max_hp_int": 7,
        "to_hit_mod": 4, "dmg_n_die_1": 1, "dmg_die_type_1": "d6",
        "dmg_flat_1": 2, "dmg_type_1": "slashing",
    }
    m = deserialize_monster(legacy)
    assert m.name == "Goblin" and m.ac == 15
    assert len(m.attacks) == 1 and m.attacks[0].to_hit_mod == 4
    # Missing modern fields default cleanly.
    assert m.damage_vulnerabilities == []


def test_player_round_trip_preserves_everything():
    original = PlayerData(
        name="Aria", ac=17, max_hp=42, attack_range_ft=5,
        imposed_roll_type="Disadvantage", adamantine=True,
        skills={
            "perception": (5, "Advantage"), "investigation": (2, "Normal"),
            "arcana": (7, "Normal"), "insight": (3, "Normal"), "stealth": (4, "Disadvantage"),
        },
        passive_perception=15, initiative_mod=3,
    )
    restored = deserialize_player(serialize_player(original))
    assert restored == original


def test_serialized_output_is_json_safe():
    # Preset files are JSON; ensure no non-serializable types leak through.
    import json
    json.dumps(serialize_monster(_full_monster()))
    json.dumps(serialize_player(PlayerData(name="X")))
