import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_cost_localisation.py"
AUDIT_PATH = ROOT / "skills" / "md-hoi4-country-content" / "scripts" / "mech_audit.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


generator = load_module("aral_cost_generator", GENERATOR_PATH)
audit = load_module("aral_mech_audit", AUDIT_PATH)


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


class MechanicAuditRegressionTests(unittest.TestCase):
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

    def test_valid_aral_ownership_contract_has_no_findings(self):
        decisions = {
            "aral_test": """
available = {
  custom_trigger_tooltip = { tooltip = aral_coast_tt owns_state = 717 }
}
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
        }
        code = """
on_startup = {
  effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } }
}
on_monthly = {
  effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } }
}
"""
        self.assertEqual(audit.aral_ownership_issues(decisions, effects, code), [])

    def test_old_control_gate_or_removal_of_state_modifier_is_flagged(self):
        decisions = {
            "aral_test": """
available = {
  custom_trigger_tooltip = { tooltip = aral_coast_tt controls_state = 717 }
}
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { controls_state = 717 } update_aral = yes }",
            "aral_state_update": "if = { limit = { is_owned_by = ROOT } force_update_dynamic_modifier = yes }",
        }
        code = """
on_startup = { effect = { KAZ = { update_aral_sea = yes } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ controls_state = 717 } aral_monthly_tick = yes } } }
remove_dynamic_modifier = { modifier = aral_state_modifier }
"""
        issues = audit.aral_ownership_issues(decisions, effects, code)
        self.assertGreaterEqual(len(issues), 4)


if __name__ == "__main__":
    unittest.main()
