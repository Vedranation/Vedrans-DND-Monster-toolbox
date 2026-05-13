"""Tests for persistence.preset — no Tkinter required."""

import pytest

from persistence.preset import delete_preset, list_presets, load_preset, migrate_v1_to_v2, save_preset


@pytest.fixture(autouse=True)
def isolated_presets_dir(tmp_path, monkeypatch):
    import persistence.preset as pm

    monkeypatch.setattr(pm, "_PRESETS_DIR", tmp_path / "Presets")
    yield


class TestSaveLoad:
    def test_roundtrip(self):
        data = {"foo": 1, "bar": [1, 2, 3]}
        save_preset("test_enc", data)
        assert load_preset("test_enc") == data

    def test_file_contains_schema_v2(self, tmp_path, monkeypatch):
        import json

        import persistence.preset as pm

        monkeypatch.setattr(pm, "_PRESETS_DIR", tmp_path / "Presets")
        save_preset("v2check", {"x": 99})
        raw = json.loads((tmp_path / "Presets" / "v2check.json").read_text())
        assert raw["schema_version"] == 2
        assert raw["name"] == "v2check"

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_preset("does_not_exist")

    def test_overwrites_existing(self):
        save_preset("enc", {"v": 1})
        save_preset("enc", {"v": 2})
        assert load_preset("enc")["v"] == 2


class TestListDelete:
    def test_list_empty_when_no_presets(self):
        assert list_presets() == []

    def test_list_returns_sorted_names(self):
        save_preset("beta", {})
        save_preset("alpha", {})
        save_preset("gamma", {})
        assert list_presets() == ["alpha", "beta", "gamma"]

    def test_delete_removes_preset(self):
        save_preset("todelete", {})
        assert "todelete" in list_presets()
        delete_preset("todelete")
        assert "todelete" not in list_presets()

    def test_delete_nonexistent_is_silent(self):
        delete_preset("ghost")  # must not raise


class TestMigration:
    def test_migrate_wraps_v1_dict(self):
        v1 = {"Meets_it_beats_it_bool": True, "N_monsters_int": 2}
        result = migrate_v1_to_v2(v1, "mypreset")
        assert result["schema_version"] == 2
        assert result["name"] == "mypreset"
        assert result["data"] == v1

    def test_load_auto_migrates_v1_file(self, tmp_path, monkeypatch):
        import json

        import persistence.preset as pm

        presets_dir = tmp_path / "Presets"
        presets_dir.mkdir()
        monkeypatch.setattr(pm, "_PRESETS_DIR", presets_dir)
        v1_data = {"some_key": "some_value"}
        (presets_dir / "legacy.json").write_text(json.dumps(v1_data))
        assert load_preset("legacy") == v1_data
