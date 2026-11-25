import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_cost_localisation.py"
AUDIT_PATH = ROOT / "skills" / "md-hoi4-country-content" / "scripts" / "mech_audit.py"
SIMULATOR_PATH = ROOT / "skills" / "md-hoi4-country-content" / "scripts" / "aral_model_sim.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


generator = load_module("aral_cost_generator", GENERATOR_PATH)
audit = load_module("aral_mech_audit", AUDIT_PATH)
simulator = load_module("aral_sea_simulator", SIMULATOR_PATH)

FOCUS_TRIGGER_SOURCE = """
aral_unlocked_program = { has_completed_focus = KAZ_economy }
aral_unlocked_syrdarya = { has_completed_focus = KAZ_fight_capacity_deficit }
aral_unlocked_agri = { has_completed_focus = KAZ_ABP }
aral_unlocked_green = { has_completed_focus = KAZ_ecologization }
aral_unlocked_phase2 = { has_completed_focus = KAZ_balance_north_and_south }
aral_unlocked_diplomacy = { has_completed_focus = KAZ_foreign_policy }
"""



class CostLocalisationGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.decisions = """
KAZ_aral_sea_category = {
\taral_test = {
\t\tcustom_cost_trigger = { check_variable = { treasury > 0.1 } }
\t\tcustom_cost_text = aral_test_cost
\t\tcomplete_effect = { custom_effect_tooltip = aral_test_cost_tt }
\t}
}
"""
        self.localisations = {
            "en": """l_english:
 aral_test_cost:0 "$0.1 bn + 10 PP"
 aral_test_cost_tt:0 "Total cost: $0.2 bn; borrowed: $0.1 bn."
""",
            "ru": """l_russian:
 aral_test_cost:0 "0,1 млрд $ + 10 ПВ"
 aral_test_cost_tt:0 "Полная стоимость: 0,2 млрд $; в долг: 0,1 млрд $."
""",
        }

    def test_generates_blocked_and_hover_keys_from_existing_sources(self):
        generated = generator.generate_entries(self.decisions, self.localisations)
        self.assertEqual(generated["en"]["aral_test_cost_blocked"], "§R$0.1 bn + 10 PP§!")
        self.assertEqual(
            generated["en"]["aral_test_cost_tooltip"],
            "Total cost: $0.2 bn; borrowed: $0.1 bn.",
        )
        self.assertEqual(generated["ru"]["aral_test_cost_blocked"], "§R0,1 млрд $ + 10 ПВ§!")

    def test_merge_is_idempotent(self):
        generated = generator.generate_entries(self.decisions, self.localisations)
        first, added1 = generator.merge_missing_keys(
            self.localisations["en"], generated["en"], "en"
        )
        second, added2 = generator.merge_missing_keys(first, generated["en"], "en")
        self.assertEqual(len(added1), 2)
        self.assertEqual(added2, [])
        self.assertEqual(first, second)

    def test_conflicting_generated_key_is_not_overwritten(self):
        generated = generator.generate_entries(self.decisions, self.localisations)
        text = self.localisations["en"] + ' aral_test_cost_blocked:0 "wrong"\n'
        with self.assertRaises(ValueError):
            generator.merge_missing_keys(text, generated["en"], "en")

    def test_missing_source_tooltip_fails_clearly(self):
        broken = dict(self.localisations)
        broken["en"] = broken["en"].replace(
            ' aral_test_cost_tt:0 "Total cost: $0.2 bn; borrowed: $0.1 bn."\n', ""
        )
        with self.assertRaisesRegex(ValueError, "missing full cost tooltip"):
            generator.generate_entries(self.decisions, broken)


class SiberianPriceReviewTests(unittest.TestCase):
    def test_simulator_reads_the_same_acceptance_gate_as_the_game_event(self):
        event = """
option = {
    name = aral_sea.9.a
    trigger = {
        check_variable = { aral_sib_fee > -0.10001 }
    }
    multiply_variable = { aral_sib_fee = 1.5 }
}
"""
        current_fee_limit = simulator.parse_siberian_fee_current_limit(event)
        self.assertAlmostEqual(current_fee_limit, 0.10001)
        self.assertAlmostEqual(current_fee_limit * 1.5, 0.150015)

    def test_missing_price_acceptance_gate_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "price-acceptance limit missing"):
            simulator.parse_siberian_fee_current_limit("option = { name = aral_sea.9.a }")


class MechanicAuditRegressionTests(unittest.TestCase):
    def test_custom_cost_suffixes_are_implicitly_referenced(self):
        decisions = {
            "aral_test": """
custom_cost_text = aral_test_cost
"""
        }
        self.assertEqual(
            audit.implied_custom_cost_localisation_keys(decisions),
            {"aral_test_cost_blocked", "aral_test_cost_tooltip"},
        )

    def test_missing_blocked_variant_is_error_but_optional_tooltip_is_not(self):
        decisions = {"aral_test": "custom_cost_text = aral_test_cost"}
        loc = {
            "en": {"aral_test_cost": "$0.1 bn"},
            "ru": {"aral_test_cost": "0,1 млрд $"},
        }
        issues = audit.custom_cost_blocked_key_issues(decisions, loc, ["en", "ru"])
        self.assertEqual(len(issues), 2)
        loc["en"]["aral_test_cost_blocked"] = "§R$0.1 bn§!"
        loc["ru"]["aral_test_cost_blocked"] = "§R0,1 млрд $§!"
        self.assertEqual(audit.custom_cost_blocked_key_issues(decisions, loc, ["en", "ru"]), [])

    def test_valid_aral_decision_and_update_ownership_contract_has_no_findings(self):
        decisions = {
            "aral_ifas": """
visible = { NOT = { has_country_flag = aral_ifas_done } }
available = {
  custom_trigger_tooltip = { tooltip = aral_unlock_program_tt aral_unlocked_program = yes }
  custom_trigger_tooltip = { tooltip = aral_req_coast_tt owns_state = 717 }
}
fire_only_once = yes
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
            "aral_monthly_tick": "if = { limit = { owns_state = 717 } aral_calc_drift = yes }",
        }
        code = """
on_startup = {
  effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } }
}
on_monthly = {
  effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } }
}
"""
        code += FOCUS_TRIGGER_SOURCE
        self.assertEqual(audit.aral_ownership_issues(decisions, effects, code), [])

    def test_aral_projects_require_coast_for_start_but_are_not_cancelled_mid_timer(self):
        decisions = {
            "aral_ifas": """
available = { aral_unlocked_program = yes owns_state = 717 }
fire_only_once = yes
days_remove = 120
complete_effect = { set_temp_variable = { treasury_change = -0.05 } modify_treasury_effect = yes }
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
            "aral_monthly_tick": "if = { limit = { owns_state = 717 } aral_calc_drift = yes }",
        }
        code = """
on_startup = { effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } } }
"""
        code += FOCUS_TRIGGER_SOURCE
        self.assertEqual(audit.aral_ownership_issues(decisions, effects, code), [])

        missing_coast = decisions["aral_ifas"].replace(
            "available = { aral_unlocked_program = yes owns_state = 717 }",
            "available = { aral_unlocked_program = yes }",
        )
        issues = audit.aral_ownership_issues({"aral_ifas": missing_coast}, effects, code)
        self.assertTrue(any("available must require owns_state = 717" in issue[1] for issue in issues))

        cancellable = decisions["aral_ifas"] + "\ncancel_trigger = { NOT = { owns_state = 717 } }\ncancel_effect = {}\n"
        issues = audit.aral_ownership_issues({"aral_ifas": cancellable}, effects, code)
        self.assertTrue(any("must not use ownership-based cancellation" in issue[1] for issue in issues))

        repeatable = decisions["aral_ifas"].replace("fire_only_once = yes", "fire_only_once = no")
        issues = audit.aral_ownership_issues({"aral_ifas": repeatable}, effects, code)
        self.assertTrue(any("fire_only_once = yes" in issue[1] for issue in issues))

    def test_treasury_and_debt_effects_must_not_be_hidden(self):
        decisions = {
            "aral_ifas": """
visible = { NOT = { has_country_flag = aral_ifas_done } }
available = { aral_unlocked_program = yes owns_state = 717 }
complete_effect = {
  hidden_effect = {
    modify_treasury_effect = yes
    modify_debt_effect = yes
  }
}
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
            "aral_monthly_tick": "if = { limit = { owns_state = 717 } aral_calc_drift = yes }",
        }
        code = """
on_startup = { effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } } }
"""
        issues = audit.aral_ownership_issues(decisions, effects, code)
        code += FOCUS_TRIGGER_SOURCE
        issues = audit.aral_ownership_issues(decisions, effects, code)
        self.assertTrue(any("outside hidden_effect" in issue[1] for issue in issues))

    def test_focus_group_triggers_are_bound_to_real_kaz_focus_ids(self):
        decisions = {
            "aral_ifas": """
visible = { NOT = { has_country_flag = aral_ifas_done } }
available = { aral_unlocked_program = yes owns_state = 717 }
fire_only_once = yes
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
            "aral_monthly_tick": "if = { limit = { owns_state = 717 } aral_calc_drift = yes }",
        }
        code = """
on_startup = { effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } } }
"""
        code += FOCUS_TRIGGER_SOURCE
        self.assertEqual(audit.aral_ownership_issues(decisions, effects, code), [])
        broken = code.replace(
            "aral_unlocked_program = { has_completed_focus = KAZ_economy }",
            "aral_unlocked_program = { always = yes }",
        )
        issues = audit.aral_ownership_issues(decisions, effects, broken)
        self.assertTrue(any("must not be left permanently open" in issue[1] for issue in issues))

    def test_monthly_tick_effect_itself_requires_ownership(self):
        decisions = {
            "aral_ifas": """
available = { aral_unlocked_program = yes owns_state = 717 }
fire_only_once = yes
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
            "aral_monthly_tick": "aral_calc_drift = yes",
        }
        code = """
on_startup = { effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } } }
"""
        code += FOCUS_TRIGGER_SOURCE
        issues = audit.aral_ownership_issues(decisions, effects, code)
        self.assertTrue(any(area == "scripted_effect aral_monthly_tick" for area, _ in issues))

    def test_old_control_gate_or_removal_of_state_modifier_is_flagged(self):
        decisions = {
            "aral_ifas": """
visible = { NOT = { has_country_flag = aral_ifas_done } }
available = {
  custom_trigger_tooltip = { tooltip = aral_unlock_program_tt aral_unlocked_program = yes }
  custom_trigger_tooltip = { tooltip = aral_coast_tt controls_state = 717 }
}
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { controls_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
            "aral_monthly_tick": "aral_calc_drift = yes",
        }
        code = """
on_startup = { effect = { KAZ = { update_aral_sea = yes } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ controls_state = 717 } aral_monthly_tick = yes } } }
remove_dynamic_modifier = { modifier = aral_state_modifier }
"""
        issues = audit.aral_ownership_issues(decisions, effects, code)
        code += FOCUS_TRIGGER_SOURCE
        issues = audit.aral_ownership_issues(decisions, effects, code)
        self.assertGreaterEqual(len(issues), 4)


if __name__ == "__main__":
    unittest.main()
