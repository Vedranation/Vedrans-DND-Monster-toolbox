"""API tests for the Phase 1 Flask server (no Tkinter)."""

import pytest

from server import state as app_state
from server.app import create_app


@pytest.fixture
def client():
    app_state.reset()
    app = create_app()
    app.testing = True
    return app.test_client()


# ── constants & state ────────────────────────────────────────────────────────

def test_constants(client):
    data = client.get("/api/constants").get_json()
    assert data["roll_types"][0] == "Normal"
    assert "fire" in data["dmg_types"]
    assert data["saving_throw_types"] == ["STR", "DEX", "CON", "WIS", "INT", "CHA"]
    assert "frightened" in data["conditions"]


def test_initial_state_empty(client):
    data = client.get("/api/state").get_json()
    assert data["monsters"] == [] and data["players"] == []
    assert "settings" in data


# ── monster CRUD ───────────────────────────────────────────────────────────────

def test_monster_crud(client):
    # Create (default)
    r = client.post("/api/monsters", json={})
    assert r.status_code == 201
    mid = r.get_json()["id"]

    # List
    assert len(client.get("/api/monsters").get_json()) == 1

    # Update
    body = r.get_json()
    body["name_str"] = "Goblin"
    body["ac_int"] = 15
    upd = client.put(f"/api/monsters/{mid}", json=body).get_json()
    assert upd["name_str"] == "Goblin" and upd["ac_int"] == 15

    # Get
    assert client.get(f"/api/monsters/{mid}").get_json()["name_str"] == "Goblin"

    # Delete
    assert client.delete(f"/api/monsters/{mid}").status_code == 204
    assert client.get(f"/api/monsters/{mid}").status_code == 404


def test_monster_import_5etools(client):
    treant = {
        "name": "Treant", "size": ["H"], "type": "plant", "ac": [16],
        "hp": {"average": 138}, "speed": {"walk": 30},
        "str": 23, "dex": 8, "con": 21, "int": 12, "wis": 16, "cha": 12,
        "passive": 13, "resist": ["bludgeoning", "piercing"], "vulnerable": ["fire"],
    }
    r = client.post("/api/monsters/import-5etools", json=treant)
    assert r.status_code == 201
    entry = r.get_json()
    assert entry["name_str"] == "Treant"
    assert entry["damage_vulnerabilities"] == ["fire"]
    assert set(entry["damage_resistances"]) == {"bludgeoning", "piercing"}


def test_monster_import_conditional_nonmagical_resist(client):
    # 5etools nests "from nonmagical attacks" physical resistance in a conditional
    # object; it must port as our plain (nonmagical) physical types.
    vampire = {
        "name": "Vampire", "ac": [{"ac": 16}], "hp": {"average": 144}, "speed": {"walk": 30},
        "resist": ["necrotic",
                   {"resist": ["bludgeoning", "piercing", "slashing"],
                    "note": "from nonmagical attacks", "cond": True}],
    }
    entry = client.post("/api/monsters/import-5etools", json=vampire).get_json()
    assert set(entry["damage_resistances"]) == {"necrotic", "bludgeoning", "piercing", "slashing"}


def test_monster_import_damage_type_is_nearest():
    # "Slashing damage plus … Lightning damage" must tag each roll with its OWN type
    # (regression: the longer word 'lightning' used to win for both).
    from persistence.import_5etools import parse_5etools_monster
    m = parse_5etools_monster({
        "name": "Dragon", "ac": [22], "hp": {"average": 100}, "skill": {"perception": "+17"},
        "languages": ["Common", "Draconic"],
        "action": [{"name": "Rend", "entries": [
            "{@atkr m} {@hit 16}, reach 15 ft. {@h}18 ({@damage 2d8 + 9}) Slashing damage "
            "plus 11 ({@damage 2d10}) Lightning damage."]}],
    })
    atk = m.attacks[0]
    assert atk.dmg_type_1 == "slashing" and atk.dmg_type_2 == "lightning"
    assert m.skills["perception"] == (17, "Normal")
    assert m.languages == ["Common", "Draconic"]


def test_monster_skill_checks(client):
    import engine.dice as dice
    dice.seed(2)
    mid = client.post("/api/monsters/import-5etools", json={
        "name": "Dragon", "ac": [22], "hp": {"average": 100}, "skill": {"perception": "+17"},
        "action": [],
    }).get_json()["id"]
    # quick check
    q = client.post("/api/rolls/monster-skill-check",
                    json={"monster_id": mid, "skill": "perception", "roll_type": "Monster default"}).get_json()
    assert q["modifier"] == 17 and q["total"] == q["d20"] + 17
    # mass check
    out = client.post("/api/rolls/mass-skill-check", json={
        "skill": "perception", "dc": 15, "roll_type": "Monster default",
        "groups": [{"monster_id": mid, "count": 4}]}).get_json()
    assert out["total"] == 4 and out["results"][0]["modifier"] == 17
    assert out["results"][0]["passes"] + out["results"][0]["fails"] == 4


# ── player CRUD ──────────────────────────────────────────────────────────────

def test_player_crud(client):
    r = client.post("/api/players", json={"name_str": "Aria", "ac_int": 17})
    assert r.status_code == 201
    pid = r.get_json()["id"]
    assert client.get(f"/api/players/{pid}").get_json()["ac_int"] == 17
    assert client.delete(f"/api/players/{pid}").status_code == 204


# ── roll-attack ──────────────────────────────────────────────────────────────

def test_roll_attack(client):
    import engine.dice as dice
    dice.seed(1)
    mid = client.post("/api/monsters", json={"name_str": "Orc", "ac_int": 13}).get_json()["id"]
    # No defender → AC-0 dummy, so every swing hits.
    res = client.post("/api/roll-attack", json={"attacker_id": mid}).get_json()
    assert res["rolls"], "expected at least one swing"
    first = res["rolls"][0]
    assert {"d20", "total", "is_hit", "attack_name"} <= set(first)
    assert isinstance(res["breakdown"], str)


def test_roll_attack_unknown_attacker_404(client):
    assert client.post("/api/roll-attack", json={"attacker_id": "nope"}).status_code == 404


# ── settings ─────────────────────────────────────────────────────────────────

def test_settings_get_and_patch(client):
    s = client.get("/api/settings").get_json()
    assert "ignore_resistances" in s and s["ignore_resistances"] is False
    upd = client.put("/api/settings", json={"ignore_resistances": True,
                                            "board_range_mode": "block"}).get_json()
    assert upd["ignore_resistances"] is True
    assert upd["board_range_mode"] == "block"
    # Unspecified keys unchanged
    assert upd["adv_mode"] == s["adv_mode"]


# ── presets ──────────────────────────────────────────────────────────────────

def test_preset_save_and_load(client, tmp_path, monkeypatch):
    import persistence.preset as preset
    monkeypatch.setattr(preset, "_PRESETS_DIR", tmp_path)

    # Build some state, save it.
    client.post("/api/monsters/import-5etools", json={
        "name": "Treant", "size": ["H"], "type": "plant", "ac": [16],
        "hp": {"average": 138}, "speed": {"walk": 30},
        "str": 23, "dex": 8, "con": 21, "int": 12, "wis": 16, "cha": 12,
        "passive": 13, "vulnerable": ["fire"],
    })
    client.post("/api/players", json={"name_str": "Aria", "ac_int": 17})
    client.put("/api/settings", json={"ignore_resistances": True})

    assert client.post("/api/presets", json={"name": "enc1"}).status_code == 200
    assert "enc1" in client.get("/api/presets").get_json()["presets"]

    # Wipe state, then load the preset back.
    app_state.reset()
    snap = client.get(f"/api/presets/enc1").get_json()
    assert len(snap["monsters"]) == 1
    assert snap["monsters"][0]["damage_vulnerabilities"] == ["fire"]
    assert len(snap["players"]) == 1
    assert snap["settings"]["ignore_resistances"] is True


def test_load_missing_preset_404(client, tmp_path, monkeypatch):
    import persistence.preset as preset
    monkeypatch.setattr(preset, "_PRESETS_DIR", tmp_path)
    assert client.get("/api/presets/nope").status_code == 404


# ── board ────────────────────────────────────────────────────────────────────

def test_board_default_teams(client):
    b = client.get("/api/board").get_json()
    assert [t["name"] for t in b["teams"]] == ["Players", "Monsters"]
    assert b["tokens"] == []


def test_board_add_move_and_patch_token(client):
    mid = client.post("/api/monsters", json={"name_str": "Orc", "max_hp_int": 15}).get_json()["id"]
    tok = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid}).get_json()
    assert tok["team"] == "Monsters" and tok["hp"] == 15
    moved = client.patch(f"/api/board/tokens/{tok['id']}",
                         json={"col": 3, "row": 4, "conditions": ["poisoned"], "team": "Players"}).get_json()
    assert (moved["col"], moved["row"]) == (3, 4)
    assert moved["conditions"] == ["poisoned"] and moved["team"] == "Players"


def test_board_hp_zero_auto_disables(client):
    mid = client.post("/api/monsters", json={"name_str": "Goblin", "max_hp_int": 7}).get_json()["id"]
    tok = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid}).get_json()
    out = client.patch(f"/api/board/tokens/{tok['id']}", json={"hp": 0}).get_json()
    assert out["hp"] == 0 and out["active"] is False


def test_board_team_lifecycle(client):
    client.post("/api/board/teams", json={"name": "Goblins"})
    b = client.patch("/api/board/teams/Goblins", json={"new_name": "Warband"}).get_json()
    assert "Warband" in [t["name"] for t in b["teams"]]
    b = client.delete("/api/board/teams/Warband").get_json()
    assert "Warband" not in [t["name"] for t in b["teams"]]
    # last team can't be deleted
    client.delete("/api/board/teams/Players")
    assert client.delete("/api/board/teams/Monsters").status_code == 400


def test_board_retarget_cycles_enemies(client):
    m = client.post("/api/monsters", json={"name_str": "Orc", "attack_range_ft": 30}).get_json()["id"]
    e1 = client.post("/api/players", json={"name_str": "A"}).get_json()["id"]
    e2 = client.post("/api/players", json={"name_str": "B"}).get_json()["id"]
    mt = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": m, "col": 0, "row": 0}).get_json()
    a = client.post("/api/board/tokens", json={"kind": "player", "ref_id": e1, "col": 1, "row": 0}).get_json()
    b = client.post("/api/board/tokens", json={"kind": "player", "ref_id": e2, "col": 8, "row": 0}).get_json()
    # auto-target = nearest (A)
    assert client.get(f"/api/board/inference/{mt['id']}").get_json()["target_id"] == a["id"]
    # retarget cycles to B, then resolve uses B, then wraps back to A
    assert client.post("/api/board/retarget", json={"token_id": mt["id"]}).get_json()["target_id"] == b["id"]
    assert client.post("/api/board/resolve").get_json()["pairs"][0]["defender_id"] == b["id"]
    assert client.post("/api/board/retarget", json={"token_id": mt["id"]}).get_json()["target_id"] == a["id"]


def test_board_retarget_multi_assigns_same_target(client):
    m = client.post("/api/monsters", json={"name_str": "Orc", "attack_range_ft": 60}).get_json()["id"]
    e1 = client.post("/api/players", json={"name_str": "A"}).get_json()["id"]
    e2 = client.post("/api/players", json={"name_str": "B"}).get_json()["id"]
    m1 = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": m, "col": 0, "row": 0}).get_json()
    m2 = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": m, "col": 0, "row": 2}).get_json()
    a = client.post("/api/board/tokens", json={"kind": "player", "ref_id": e1, "col": 1, "row": 1}).get_json()
    b = client.post("/api/board/tokens", json={"kind": "player", "ref_id": e2, "col": 9, "row": 1}).get_json()
    # both monsters cycle together → same chosen target assigned to each
    r = client.post("/api/board/retarget",
                    json={"token_ids": [m1["id"], m2["id"]], "primary_id": m1["id"]}).get_json()
    chosen = r["target_id"]
    assert chosen in (a["id"], b["id"])
    lines = {ln["from_id"]: ln["to_id"] for ln in client.get("/api/board/targets").get_json()["lines"]}
    assert lines[m1["id"]] == chosen and lines[m2["id"]] == chosen


def test_incapacitated_monster_cannot_attack(client):
    m = client.post("/api/monsters", json={"name_str": "Orc", "attack_range_ft": 30}).get_json()["id"]
    p = client.post("/api/players", json={"name_str": "Hero"}).get_json()["id"]
    mt = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": m, "col": 0, "row": 0}).get_json()
    client.post("/api/board/tokens", json={"kind": "player", "ref_id": p, "col": 1, "row": 0})
    # normally it attacks
    assert len(client.post("/api/board/resolve").get_json()["pairs"]) == 1
    # incapacitated → no attack, no target arrow
    client.patch(f"/api/board/tokens/{mt['id']}", json={"conditions": ["incapacitated"]})
    out = client.post("/api/board/resolve").get_json()
    assert out["pairs"] == [] and any("incapacitated" in s for s in out["skipped"])
    assert client.get("/api/board/targets").get_json()["lines"] == []


def test_charmed_cannot_target_charmer(client):
    client.put("/api/settings", json={"board_range_mode": "block"})
    m = client.post("/api/monsters", json={"name_str": "Thrall", "attack_range_ft": 60}).get_json()["id"]
    p1 = client.post("/api/players", json={"name_str": "Charmer"}).get_json()["id"]
    p2 = client.post("/api/players", json={"name_str": "Other"}).get_json()["id"]
    mt = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": m, "col": 0, "row": 0}).get_json()
    c = client.post("/api/board/tokens", json={"kind": "player", "ref_id": p1, "col": 1, "row": 0}).get_json()
    o = client.post("/api/board/tokens", json={"kind": "player", "ref_id": p2, "col": 5, "row": 0}).get_json()
    # charmed by the (nearer) charmer → in block mode it must target Other instead
    client.patch(f"/api/board/tokens/{mt['id']}", json={"conditions": ["charmed"], "charmed_by": c["id"]})
    assert client.get(f"/api/board/inference/{mt['id']}").get_json()["target_id"] == o["id"]
    # warn mode → charmer allowed again, with a warning flagged on resolve
    client.put("/api/settings", json={"board_range_mode": "warn"})
    client.post("/api/board/retarget", json={"token_id": mt["id"]})  # cycle back toward charmer
    # removing the charmed condition clears the charmer reference
    client.patch(f"/api/board/tokens/{mt['id']}", json={"conditions": []})
    assert client.get("/api/board").get_json()["tokens"][0]["charmed_by"] is None


def test_concentration_warns_on_resolve(client):
    import engine.dice as dice
    dice.seed(1)
    atk = client.post("/api/monsters", json={"name_str": "Orc", "attack_range_ft": 30,
                                             "attacks": [{"name": "Hit", "to_hit_mod": 20, "n_attacks": 1}]}).get_json()["id"]
    def_ = client.post("/api/players", json={"name_str": "Wizard", "ac_int": 1}).get_json()["id"]
    client.post("/api/board/tokens", json={"kind": "monster", "ref_id": atk, "col": 0, "row": 0})
    dt = client.post("/api/board/tokens", json={"kind": "player", "ref_id": def_, "col": 1, "row": 0}).get_json()
    cid = client.post("/api/casters", json={"name": "Wizard", "level": 5}).get_json()["id"]
    client.patch(f"/api/casters/{cid}", json={"token_id": dt["id"], "concentrating": True})

    pair = client.post("/api/board/resolve").get_json()["pairs"][0]
    assert pair["applied"] > 0 and pair["defender_concentrating"] is True
    # toggling concentration off clears the warning
    client.patch(f"/api/casters/{cid}", json={"concentrating": False})
    assert client.post("/api/board/resolve").get_json()["pairs"][0]["defender_concentrating"] is False


def test_board_retarget_block_mode_reports_blocked(client):
    client.put("/api/settings", json={"board_range_mode": "block"})
    m = client.post("/api/monsters", json={"name_str": "Orc", "attack_range_ft": 5}).get_json()["id"]
    e1 = client.post("/api/players", json={"name_str": "Far"}).get_json()["id"]
    mt = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": m, "col": 0, "row": 0}).get_json()
    client.post("/api/board/tokens", json={"kind": "player", "ref_id": e1, "col": 10, "row": 0})
    r = client.post("/api/board/retarget", json={"token_id": mt["id"]}).get_json()
    assert r["blocked"] is True and r["target_id"] is None


def test_force_crit_on_hit_upgrades_hits():
    import engine.dice as dice
    from engine.combat import CombatSettings, compute_single_attack
    from engine.models import AttackSpec, MonsterData, PlayerData
    dice.seed(3)
    m = MonsterData(name="Orc", attacks=[AttackSpec(name="Greataxe", to_hit_mod=20, n_attacks=4)])
    res = compute_single_attack(m, PlayerData(ac=10), CombatSettings(), force_crit_on_hit=True)
    hit_rolls = [r for r in res.rolls if r.is_hit]
    assert hit_rolls and all(r.is_crit for r in hit_rolls)   # every landed hit is a crit


def test_board_inference_panel_and_autocrit(client):
    mid = client.post("/api/monsters", json={
        "name_str": "Ogre", "ac_int": 11, "max_hp_int": 59, "attack_range_ft": 5,
        "walking_speed_int": 40, "flying_speed_int": 0,
        "damage_resistances": ["fire"], "condition_immunities": ["charmed"],
    }).get_json()["id"]
    pid = client.post("/api/players", json={"name_str": "Hero", "ac_int": 15}).get_json()["id"]
    mt = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid, "col": 0, "row": 0}).get_json()
    pt = client.post("/api/board/tokens", json={"kind": "player", "ref_id": pid, "col": 1, "row": 0}).get_json()

    panel = client.get(f"/api/board/inference/{mt['id']}").get_json()["panel"]
    assert panel["name"] == "Ogre" and panel["kind"] == "monster" and panel["ac"] == 11
    assert panel["speeds"] == {"walk": 40}            # 0-value speeds dropped
    assert panel["resistances"] == ["fire"] and panel["condition_immunities"] == ["charmed"]
    assert panel["attacks"] and panel["attacks"][0]["dmg1"] is not None
    assert panel["auto_crit"] is False                # target not helpless

    # Make the player unconscious → adjacent monster auto-crits it
    client.patch(f"/api/board/tokens/{pt['id']}", json={"conditions": ["unconscious"]})
    assert client.get(f"/api/board/inference/{mt['id']}").get_json()["panel"]["auto_crit"] is True
    pp = client.get(f"/api/board/inference/{pt['id']}").get_json()["panel"]
    assert pp["is_helpless"] is True


def test_rolls_mass_saves(client):
    import engine.dice as dice
    dice.seed(1)
    m = client.post("/api/monsters", json={"name_str": "Orc",
                    "savingthrow_con_mod_int": 3, "savingthrow_con_roll_type_str": "Normal"}).get_json()["id"]
    out = client.post("/api/rolls/mass-saves",
                      json={"save": "CON", "dc": 10, "roll_type": "Monster default",
                            "groups": [{"monster_id": m, "count": 5}]}).get_json()
    assert out["total"] == 5
    g = out["results"][0]
    assert g["name"] == "Orc" and g["modifier"] == 3 and len(g["rolls"]) == 5
    assert g["passes"] + g["fails"] == 5


def test_rolls_party_skill_check(client):
    client.post("/api/players", json={"name_str": "Aria", "perception_mod_int": 5})
    out = client.post("/api/rolls/party-skill-check", json={"skill": "perception", "dc": 10}).get_json()
    assert out["results"][0]["name"] == "Aria"
    assert out["results"][0]["status"] in ("Passed", "Failed", "Nat1", "Nat20")


def test_rolls_fumble(client):
    from engine.tables import FUMBLE_TABLE
    assert client.post("/api/rolls/fumble").get_json()["result"] in FUMBLE_TABLE


def test_rolls_dice(client):
    import engine.dice as dice
    dice.seed(1)
    out = client.post("/api/rolls/dice", json={"count": 3, "die": "d6", "modifier": 2}).get_json()
    assert out["die"] == "d6" and out["count"] == 3 and out["modifier"] == 2
    assert len(out["rolls"]) == 3 and all(1 <= r <= 6 for r in out["rolls"])
    assert out["sum"] == sum(out["rolls"])
    assert out["total"] == out["sum"] + 2


def test_rolls_dice_defaults_and_clamps(client):
    # bad die → d20; count clamped to >=1; missing modifier → 0
    out = client.post("/api/rolls/dice", json={"die": "d3", "count": 0}).get_json()
    assert out["die"] == "d20" and out["count"] == 1 and out["modifier"] == 0
    assert len(out["rolls"]) == 1


def test_caster_token_link(client):
    cid = client.post("/api/casters", json={"name": "Wizard", "level": 5}).get_json()["id"]
    assert client.get("/api/casters").get_json()["casters"][0]["token_id"] is None
    client.patch(f"/api/casters/{cid}", json={"token_id": "t3"})
    assert client.get("/api/casters").get_json()["casters"][0]["token_id"] == "t3"
    client.patch(f"/api/casters/{cid}", json={"token_id": None})
    assert client.get("/api/casters").get_json()["casters"][0]["token_id"] is None


def test_caster_duplicate(client):
    cid = client.post("/api/casters", json={"name": "Wizard", "level": 5}).get_json()["id"]
    client.post(f"/api/casters/{cid}/spells", json={"level": 3, "name": "Fireball"})
    client.patch(f"/api/casters/{cid}", json={"token_id": "t1"})
    dup = client.post(f"/api/casters/{cid}/duplicate").get_json()
    assert dup["id"] != cid
    assert dup["name"] == "Wizard (copy)" and dup["level"] == 5
    assert dup["spells"]["3"] == ["Fireball"]
    assert dup["token_id"] is None   # copy is unlinked
    assert len(client.get("/api/casters").get_json()["casters"]) == 2


def test_preset_roundtrip_extended(client, tmp_path, monkeypatch):
    import persistence.preset as preset_mod
    monkeypatch.setattr(preset_mod, "_PRESETS_DIR", tmp_path)
    # Build a scenario: monster + board token + caster linked to it + initiative.
    mid = client.post("/api/monsters", json={"name_str": "Orc", "max_hp_int": 15}).get_json()["id"]
    client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid})
    tok = client.get("/api/board").get_json()["tokens"][0]["id"]
    cid = client.post("/api/casters", json={"name": "Mage", "level": 3}).get_json()["id"]
    client.patch(f"/api/casters/{cid}", json={"token_id": tok})
    client.post("/api/initiative/entry", json={"name": "Goblin", "initiative": 12})

    assert client.post("/api/presets", json={"name": "scn"}).status_code == 200
    app_state.reset()
    assert client.get("/api/state").get_json()["monsters"] == []

    client.get("/api/presets/scn")
    casters = client.get("/api/casters").get_json()["casters"]
    tokens = client.get("/api/board").get_json()["tokens"]
    inits = client.get("/api/initiative").get_json()["entries"]
    assert len(tokens) == 1 and len(casters) == 1 and len(inits) == 1
    assert casters[0]["token_id"] == tokens[0]["id"]   # caster↔token link survives


def test_import_5etools_extracts_dice(client):
    fb = {"name": "Fireball", "level": 3, "school": "V",
          "entries": ["takes {@damage 8d6} Fire damage on a failed save"]}
    out = client.post("/api/spell-library/import-5etools", json=fb).get_json()
    sp = out["spells"][-1]
    assert sp["dice_count"] == 8 and sp["dice_type"] == "d6"


def test_initiative_quick_add_and_roll(client):
    client.post("/api/monsters", json={"name_str": "Orc", "initiative_mod": 2})
    client.post("/api/players", json={"name_str": "Aria", "initiative_mod": 3})
    client.post("/api/initiative/quick-add")
    entries = client.get("/api/initiative").get_json()["entries"]
    assert len(entries) == 2
    # sorted descending
    assert entries[0]["initiative"] >= entries[1]["initiative"]
    # manual high entry floats to top
    client.post("/api/initiative/entry", json={"name": "Trap", "initiative": 30})
    assert client.get("/api/initiative").get_json()["entries"][0]["name"] == "Trap"


def test_caster_slots_and_cast(client):
    cid = client.post("/api/casters", json={"name": "Wiz", "level": 5}).get_json()["id"]
    c = client.get("/api/casters").get_json()["casters"][0]
    assert c["slots"]["1"]["max"] == 4 and c["slots"]["3"]["max"] == 2  # level-5 full caster
    client.post(f"/api/casters/{cid}/spells", json={"level": 3, "name": "Fireball"})
    after = client.post(f"/api/casters/{cid}/cast", json={"level": 3}).get_json()
    assert after["slots"]["3"]["used"] == 1
    assert after["spells"]["3"] == ["Fireball"]
    reset = client.post(f"/api/casters/{cid}/reset-slots").get_json()
    assert reset["slots"]["3"]["used"] == 0


def test_spell_library_import(client):
    r = client.post("/api/spell-library/import-5etools", json={
        "name": "Fireball", "level": 3, "school": "V",
        "time": [{"number": 1, "unit": "action"}],
        "range": {"type": "point", "distance": {"type": "feet", "amount": 150}},
        "duration": [{"type": "instant"}], "components": {"v": True, "s": True},
        "entries": ["A bright streak..."],
    })
    assert r.status_code == 201 and r.get_json()["name"] == "Fireball"
    lib = client.get("/api/spell-library").get_json()["spells"]
    assert lib[0]["name"] == "Fireball" and lib[0]["level"] == 3


def test_search_catalog_and_local(client):
    client.post("/api/monsters", json={"name_str": "x"})  # ensure state exists
    data = client.get("/api/search?q=firebal").get_json()
    top = data["suggestions"][0]
    assert top["name"] == "Fireball"
    assert top["url"] == "https://5e.tools/spells.html#fireball_phb"


def test_board_clear_deactivated(client):
    mid = client.post("/api/monsters", json={"name_str": "Orc", "max_hp_int": 1}).get_json()["id"]
    a = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid}).get_json()
    client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid})
    client.patch(f"/api/board/tokens/{a['id']}", json={"active": False})
    b = client.post("/api/board/clear-deactivated").get_json()
    assert len(b["tokens"]) == 1


def test_monster_color_flows_to_token(client):
    mid = client.post("/api/monsters", json={"name_str": "Imp", "color_str": "#cc3333"}).get_json()["id"]
    assert client.get(f"/api/monsters/{mid}").get_json()["color_str"] == "#cc3333"
    tok = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid}).get_json()
    assert tok["color"] == "#cc3333"   # token inherits the roster color


def test_player_color_roundtrips(client):
    pid = client.post("/api/players", json={"name_str": "Bard", "color_str": "#3366cc"}).get_json()["id"]
    assert client.get(f"/api/players/{pid}").get_json()["color_str"] == "#3366cc"


def test_show_range_overlay_respects_diagonal_mode(client):
    # show_attack_range off → no overlay
    plain = client.post("/api/monsters", json={"name_str": "Grunt", "attack_range_ft": 10}).get_json()["id"]
    client.post("/api/board/tokens", json={"kind": "monster", "ref_id": plain, "col": 1, "row": 1})
    assert client.get("/api/board/targets").get_json()["ranges"] == []

    # show_attack_range on → overlay cells appear, honoring the diagonal rule
    mid = client.post("/api/monsters", json={
        "name_str": "Archer", "attack_range_ft": 10, "show_attack_range_bool": True}).get_json()["id"]
    client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid, "col": 5, "row": 5})
    client.put("/api/settings", json={"board_diagonal_mode": "standard"})
    std = next(r for r in client.get("/api/board/targets").get_json()["ranges"] if r["color"] or True)
    assert len(std["cells"]) == 25                      # 10 ft = 2 Chebyshev cells → 5x5 block
    client.put("/api/settings", json={"board_diagonal_mode": "5-10-5"})
    alt = client.get("/api/board/targets").get_json()["ranges"][0]
    assert len(alt["cells"]) < 25                        # diagonals cost more → fewer cells


def test_new_token_falls_back_to_existing_team(client):
    # Deleting the default "Monsters" team must not strand new monster tokens on a
    # phantom team — they should land on an existing team instead.
    mid = client.post("/api/monsters", json={"name_str": "Orc", "max_hp_int": 5}).get_json()["id"]
    teams = [t["name"] for t in client.delete("/api/board/teams/Monsters").get_json()["teams"]]
    assert "Monsters" not in teams
    tok = client.post("/api/board/tokens", json={"kind": "monster", "ref_id": mid}).get_json()
    assert tok["team"] in teams   # not the deleted "Monsters"
