"""Tests for domain models and conditions — no Tkinter required."""

from engine.conditions import CONDITION_EFFECTS, Condition
from engine.models import AttackSpec, MonsterData, PlayerData


class TestAttackSpecDefaults:
    def test_default_to_hit_mod(self):
        assert AttackSpec().to_hit_mod == 5

    def test_default_n_attacks(self):
        assert AttackSpec().n_attacks == 1

    def test_default_crit_number(self):
        assert AttackSpec().crit_number == 20

    def test_default_dmg_die(self):
        spec = AttackSpec()
        assert spec.dmg_n_die_1 == 1
        assert spec.dmg_die_type_1 == "d6"
        assert spec.dmg_flat_1 == 0
        assert spec.dmg_n_die_2 == 0  # secondary damage off by default

    def test_all_booleans_default_false(self):
        spec = AttackSpec()
        assert not spec.brutal_critical
        assert not spec.savage_attacker
        assert not spec.reroll_1_on_hit
        assert not spec.reroll_1_2_dmg
        assert not spec.bane
        assert not spec.bless
        assert not spec.on_hit_force_save


class TestMonsterDataDefaults:
    def test_default_name_and_ac(self):
        m = MonsterData()
        assert m.name == "Monster"
        assert m.ac == 13

    def test_has_attack_spec(self):
        m = MonsterData()
        assert len(m.attacks) == 1
        assert isinstance(m.attacks[0], AttackSpec)

    def test_empty_saving_throws(self):
        assert MonsterData().saving_throws == {}

    def test_empty_speeds(self):
        assert MonsterData().speeds == {}

    def test_no_conditions_by_default(self):
        assert MonsterData().conditions == set()

    def test_conditions_are_independent_per_instance(self):
        m1, m2 = MonsterData(), MonsterData()
        m1.conditions.add(Condition.POISONED)
        assert Condition.POISONED not in m2.conditions

    def test_attack_specs_are_independent_per_instance(self):
        m1, m2 = MonsterData(), MonsterData()
        m1.attacks[0].to_hit_mod = 99
        assert m2.attacks[0].to_hit_mod == 5  # default, not 99


class TestPlayerDataDefaults:
    def test_default_name_and_ac(self):
        p = PlayerData()
        assert p.name == "Player"
        assert p.ac == 13

    def test_default_roll_type(self):
        assert PlayerData().imposed_roll_type == "Normal"

    def test_not_adamantine_by_default(self):
        assert not PlayerData().adamantine

    def test_no_conditions_by_default(self):
        assert PlayerData().conditions == set()

    def test_conditions_are_independent_per_instance(self):
        p1, p2 = PlayerData(), PlayerData()
        p1.conditions.add(Condition.STUNNED)
        assert Condition.STUNNED not in p2.conditions


class TestConditions:
    def test_all_conditions_exist(self):
        names = {c.value for c in Condition}
        assert names == {
            "blinded", "charmed", "deafened", "frightened", "grappled",
            "incapacitated", "invisible", "paralyzed", "petrified",
            "poisoned", "prone", "restrained", "stunned", "unconscious",
        }

    def test_conditions_are_hashable(self):
        s: set[Condition] = {Condition.POISONED, Condition.STUNNED}
        assert len(s) == 2

    def test_condition_effects_covers_all_conditions(self):
        assert set(CONDITION_EFFECTS.keys()) == set(Condition)

    def test_poisoned_imposes_disadvantage(self):
        assert CONDITION_EFFECTS[Condition.POISONED]["attack_roll_type"] == "disadvantage"

    def test_restrained_imposes_disadvantage_and_advantage_against(self):
        effects = CONDITION_EFFECTS[Condition.RESTRAINED]
        assert effects["attack_roll_type"] == "disadvantage"
        assert effects["defense_roll_type"] == "advantage"

    def test_prone_grants_melee_adv(self):
        assert CONDITION_EFFECTS[Condition.PRONE].get("melee_vs_prone_adv") is True

    def test_stunned_imposes_disadvantage_and_advantage_against(self):
        effects = CONDITION_EFFECTS[Condition.STUNNED]
        assert effects["attack_roll_type"] == "disadvantage"
        assert effects["defense_roll_type"] == "advantage"

    def test_frightened_imposes_disadvantage(self):
        assert CONDITION_EFFECTS[Condition.FRIGHTENED]["attack_roll_type"] == "disadvantage"

    def test_invisible_grants_attack_advantage(self):
        assert CONDITION_EFFECTS[Condition.INVISIBLE]["attack_roll_type"] == "advantage"

    def test_invisible_gives_attackers_disadvantage(self):
        assert CONDITION_EFFECTS[Condition.INVISIBLE]["defense_roll_type"] == "disadvantage"

    def test_blinded_imposes_disadvantage_and_advantage_against(self):
        effects = CONDITION_EFFECTS[Condition.BLINDED]
        assert effects["attack_roll_type"] == "disadvantage"
        assert effects["defense_roll_type"] == "advantage"
