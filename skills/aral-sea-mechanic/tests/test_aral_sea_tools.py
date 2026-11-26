import importlib.util
import sys
import gc
import tempfile
import warnings
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COST_CHECK_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_generic_costs.py"
AUDIT_PATH = ROOT / "skills" / "aral-sea-mechanic" / "scripts" / "mech_audit.py"
SIMULATOR_PATH = ROOT / "skills" / "aral-sea-mechanic" / "scripts" / "aral_model_sim.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cost_checker = load_module("aral_cost_checker", COST_CHECK_PATH)
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

STATE_UPDATE_SOURCE = """
if = {
  limit = { is_owned_by = KAZ }
  set_variable = { aral_s_prod = KAZ.aral_deficit }
  set_variable = { aral_s_slots = KAZ.aral_deficit }
  set_variable = { aral_s_recruit = KAZ.aral_deficit }
  add_dynamic_modifier = { modifier = aral_state_modifier }
  force_update_dynamic_modifier = yes
}
"""


class AralSimulatorTests(unittest.TestCase):
    def test_parser_does_not_require_kazakhstan_history_file(self):
        constants, decisions = simulator.parse(str(ROOT / "mdredux"))
        self.assertEqual(constants["treasury0"], 0.245)
        self.assertIn("ifas", decisions)

    def test_custom_starting_treasury_is_respected(self):
        constants, decisions = simulator.parse(str(ROOT / "mdredux"), treasury0=0.5)
        self.assertEqual(constants["treasury0"], 0.5)
        self.assertTrue(decisions)

    def test_parser_reads_state_scoped_penalties_and_regional_event_chain(self):
        constants, projects = simulator.parse(str(ROOT / "mdredux"))
        self.assertEqual(constants["state_weights"], [
            (717, 1.0), (1224, 0.5), (1231, 0.5),
            (1226, 0.5), (1230, 0.25), (718, 0.25),
        ])
        self.assertEqual(constants["state_mods"], {
            "aral_s_prod": -0.001,
            "aral_s_slots": -0.0006,
            "aral_s_recruit": -0.001,
        })
        self.assertAlmostEqual(constants["regional_warning_threshold"], 69.99)
        self.assertEqual(constants["regional_warning_delay"], 14)
        self.assertEqual(constants["regional_neglect_days"], 730)
        self.assertEqual(constants["regional_followup_days"], 540)
        self.assertAlmostEqual(constants["regional_monitor_cost"], 0.5)
        self.assertEqual(constants["regional_monitor_pp"], 25)
        self.assertAlmostEqual(constants["regional_response_cost"], 1.0)
        self.assertEqual(constants["regional_response_pp"], 50)
        self.assertAlmostEqual(constants["regional_recovery_cost"], 1.5)
        self.assertAlmostEqual(constants["sib"]["canal"]["fee"], 0.6)
        self.assertAlmostEqual(constants["sib"]["pipe"]["fee"], 0.4)
        self.assertAlmostEqual(constants["sib"]["fee_cap"], 1.500015)
        expected_costs = {
            "ifas": 0.5,
            "loan": 0.5,
            "dike": 0.5,
            "channel": 1.5,
            "kokaral": 4.5,
            "aklak": 1.0,
            "irrigation": 8.0,
            "fish": 1.0,
            "saxaul1": 1.5,
            "saxaul2": 8.0,
            "uzb": 0.5,
            "amanotkel": 8.0,
            "phase2": 10.0,
            "dam2": 25.0,
            "sibaral": 0.5,
            "sib_canal": 40.0,
            "sib_pipe": 50.0,
            "regional_response": 1.5,
        }
        for decision, cash_cost in expected_costs.items():
            with self.subTest(decision=decision):
                self.assertAlmostEqual(projects[decision]["tre"], cash_cost)
                self.assertNotIn("debt", projects[decision])
        self.assertEqual(constants["regional_spirits"]["neglect"], {
            "stability_factor": -0.02, "political_power_factor": -0.03,
        })
        self.assertEqual(constants["regional_spirits"]["crisis"], {
            "stability_factor": -0.04, "political_power_factor": -0.05,
        })


    def test_projects_can_be_started_with_negative_treasury(self):
        import random
        constants, projects = simulator.parse(str(ROOT / "mdredux"))
        result = simulator.run(
            constants, projects, income=0.0, pp_m=0.0, route="phase2",
            dike_policy="no", buy=False, rebuild=False, months=1,
            rng=random.Random(1),
        )
        self.assertLess(result["treasury"], 0.0)
        self.assertGreater(result["spent"], 0.0)

    def test_script_readers_close_files(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "reader.txt"
            source.write_text("value = 1\\n", encoding="utf-8")
            for reader in (simulator.rd, audit.rd):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ResourceWarning)
                    self.assertTrue(reader(str(source)))
                    gc.collect()
                self.assertFalse(
                    any(issubclass(item.category, ResourceWarning) for item in caught),
                    "script reader left its file handle open"
                )


class GenericTreasuryCostCheckerTests(unittest.TestCase):
    def test_full_price_uses_shared_key_without_a_treasury_balance_gate(self):
        source = """
KAZ_aral_sea_category = {
    aral_test = {
        custom_cost_trigger = { always = yes }
        custom_cost_text = cost_4_5
        complete_effect = {
            set_temp_variable = { treasury_change = -4.5 }
            modify_treasury_effect = yes
        }
    }
}
"""
        self.assertEqual(cost_checker.validate_costs(source), [])

    def test_old_cash_threshold_and_explicit_debt_are_rejected(self):
        source = """
KAZ_aral_sea_category = {
    aral_test = {
        custom_cost_trigger = { check_variable = { treasury > 4 } }
        custom_cost_text = cost_4_5
        complete_effect = {
            set_temp_variable = { treasury_change = -1.5 }
            modify_treasury_effect = yes
            set_temp_variable = { debt_change = 3 }
            modify_debt_effect = yes
        }
    }
}
"""
        findings = cost_checker.validate_costs(source)
        self.assertTrue(any("treasury" in finding.lower() for finding in findings))
        self.assertTrue(any("debt" in finding.lower() for finding in findings))
        self.assertTrue(any("does not match" in finding.lower() for finding in findings))

    def test_only_confirmed_generic_price_keys_are_allowed(self):
        source = """
KAZ_aral_sea_category = {
    aral_test = {
        custom_cost_trigger = { always = yes }
        custom_cost_text = aral_custom_cost_label
        complete_effect = {
            set_temp_variable = { treasury_change = -0.5 }
            modify_treasury_effect = yes
        }
    }
}
"""
        self.assertTrue(cost_checker.validate_costs(source))


class SiberianPriceReviewTests(unittest.TestCase):
    def test_simulator_reads_the_same_acceptance_gate_as_the_game_event(self):
        event = """
option = {
    name = aral_sea.9.a
    trigger = {
        check_variable = { aral_sib_fee > -1.00001 }
    }
    multiply_variable = { aral_sib_fee = 1.5 }
}
"""
        current_fee_limit = simulator.parse_siberian_fee_current_limit(event)
        self.assertAlmostEqual(current_fee_limit, 1.00001)
        self.assertAlmostEqual(current_fee_limit * 1.5, 1.500015)

    def test_missing_price_acceptance_gate_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "price-acceptance limit missing"):
            simulator.parse_siberian_fee_current_limit("option = { name = aral_sea.9.a }")


class MechanicAuditRegressionTests(unittest.TestCase):
    def test_aral_help_uses_existing_vanilla_help_sprite(self):
        gui = (ROOT / "mdredux" / "interface" / "aral_sea.gui").read_text(encoding="utf-8")
        self.assertIn('spriteType = "GFX_help_button"', gui)
        self.assertNotIn("GFX_help_button_custom", gui)

    def test_aral_dynamic_modifiers_use_existing_vanilla_icons(self):
        source = (
            ROOT / "mdredux" / "common" / "dynamic_modifiers" / "aral_sea_modifiers.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("icon = GFX_idea_generic_agrarian_society", source)
        self.assertIn("icon = GFX_idea_generic_agrarian_reform", source)
        self.assertNotIn("GFX_destroyed_dam", source)

    def test_native_pp_cost_does_not_need_to_be_repeated_in_treasury_label(self):
        body = """
cost = 25
custom_cost_text = aral_test_cash
"""
        localisations = {
            "en": {"aral_test_cash": "$0.05 bn"},
            "ru": {"aral_test_cash": "0,05 млрд $"},
        }
        self.assertEqual(
            audit.aral_pp_cost_label_issues("aral_test", body, localisations, ("en", "ru")),
            [],
        )

    def test_pp_cost_uses_native_decision_cost_and_separates_treasury(self):
        decisions = {
            "aral_test": """
cost = 25
custom_cost_trigger = { always = yes }
custom_cost_text = cost_0_5
complete_effect = {
  set_temp_variable = { treasury_change = -0.5 }
  modify_treasury_effect = yes
}
"""
        }
        self.assertEqual(audit.aral_decision_cost_issues(decisions), [])

        legacy = {
            "aral_test": """
custom_cost_trigger = {
  check_variable = { treasury > 0.05 }
  has_political_power > 24
}
custom_cost_text = aral_test_cost
ai_hint_pp_cost = 25
complete_effect = {
  add_political_power = -25
  set_temp_variable = { treasury_change = -0.05 }
  modify_treasury_effect = yes
}
"""
        }
        findings = audit.aral_decision_cost_issues(legacy)
        self.assertTrue(any("native decision cost = N" in message for _, message in findings))

    def test_aral_financing_uses_full_treasury_cost_without_debt_or_cash_gates(self):
        decisions = {
            "aral_test": """
custom_cost_trigger = { always = yes }
custom_cost_text = cost_4_5
complete_effect = {
  set_temp_variable = { treasury_change = -4.5 }
  modify_treasury_effect = yes
}
"""
        }
        events = {
            "aral_sea.1": "option = { trigger = { has_political_power = 15 } set_temp_variable = { treasury_change = -0.3 } modify_treasury_effect = yes }"
        }
        self.assertEqual(audit.aral_treasury_cost_issues(decisions, events), [])
        decisions["aral_test"] = decisions["aral_test"].replace("always = yes", "check_variable = { treasury > 4 }")
        events["aral_sea.1"] = events["aral_sea.1"].replace("has_political_power = 15", "check_variable = { treasury > 0.3 }")
        findings = audit.aral_treasury_cost_issues(decisions, events)
        self.assertTrue(any("treasury" in message.lower() for _, message in findings))

    def test_category_allowed_must_not_be_duplicated_in_each_aral_decision(self):
        decisions = {
            "aral_test": "allowed = { original_tag = KAZ }\\ncustom_cost_text = aral_test_cost"
        }
        self.assertTrue(any("parent decision category" in msg for _, msg in audit.aral_decision_cost_issues(decisions)))

    def test_aral_localisation_omits_optional_zero_version_suffix(self):
        self.assertEqual(audit.aral_localisation_style_issues(' aral_test: "text"'), [])
        findings = audit.aral_localisation_style_issues(' aral_test:0 "text"')
        self.assertEqual(len(findings), 1)
        self.assertIn(":0", findings[0][1])

    def test_documented_mdc_modifier_identifiers_are_not_rejected(self):
        dyn = {
            "aral_regional_neglect_modifier": (
                "stability_factor = -0.02\\n"
                "political_power_factor = -0.03"
            ),
            "aral_regional_crisis_modifier": (
                "stability_factor = -0.04\\n"
                "political_power_factor = -0.05"
            ),
            "aral_state_modifier": (
                "state_productivity_growth_modifier = aral_s_prod\\n"
                "local_building_slots_factor = aral_s_slots\\n"
                "recruitable_population_factor = aral_s_recruit"
            ),
        }
        effects = {"update_aral_sea": "set_variable = { aral_deficit = aral_sea_restoration }"}
        self.assertEqual(audit.aral_modifier_issues(dyn, effects), [])
        broken = dict(dyn)
        broken["aral_state_modifier"] = broken["aral_state_modifier"].replace(
            "state_productivity_growth_modifier", "unsupported_state_modifier"
        )
        self.assertTrue(any("state_productivity_growth_modifier" in msg for _, msg in audit.aral_modifier_issues(broken, effects)))
        broken = dict(dyn)
        broken["aral_regional_crisis_modifier"] = "stability_factor = -0.04"
        self.assertTrue(any("political_power_factor" in msg for _, msg in audit.aral_modifier_issues(broken, effects)))
        broken = dict(dyn)
        broken["aral_sea_dynamic_modifier"] = "monthly_population = -0.01"
        self.assertTrue(any("country-wide Aral ecological modifier" in msg for _, msg in audit.aral_modifier_issues(broken, effects)))

    def test_regional_crisis_audit_requires_warning_escalation_and_recovery(self):
        tick = """
if = {
    limit = {
        check_variable = { aral_deficit > 69.99 }
        NOT = { has_country_flag = aral_regional_warning_sent }
        NOT = { has_country_flag = aral_regional_monitoring_done }
    }
    set_country_flag = aral_regional_warning_sent
    country_event = { id = aral_sea.10 days = 14 }
}
"""
        events = {
            "aral_sea.10": """
option = { set_country_flag = aral_regional_monitoring_done }
option = {
    add_dynamic_modifier = { modifier = aral_regional_neglect_modifier days = 730 }
    country_event = { id = aral_sea.11 days = 540 }
}
""",
            "aral_sea.11": """
trigger = { has_country_flag = aral_regional_neglect_started }
option = { remove_dynamic_modifier = { modifier = aral_regional_neglect_modifier } }
option = {
    remove_dynamic_modifier = { modifier = aral_regional_neglect_modifier }
    add_dynamic_modifier = { modifier = aral_regional_crisis_modifier }
}
""",
        }
        decisions = {
            "aral_regional_response": """
visible = { has_country_flag = aral_regional_crisis }
available = { custom_trigger_tooltip = { tooltip = aral_req_coast_tt owns_state = 717 } }
cost = 60
complete_effect = { set_temp_variable = { treasury_change = -1.5 } modify_treasury_effect = yes }
remove_effect = {
    remove_dynamic_modifier = { modifier = aral_regional_crisis_modifier }
    clr_country_flag = aral_regional_crisis
}
"""
        }
        effects = {"aral_monthly_tick": tick}
        self.assertEqual(audit.aral_regional_crisis_issues(events, decisions, effects), [])
        events["aral_sea.10"] = events["aral_sea.10"].replace("days = 730", "days = 90")
        self.assertTrue(audit.aral_regional_crisis_issues(events, decisions, effects))

    def test_countrywide_aral_ecological_penalties_are_removed_from_gameplay_code(self):
        effects = (ROOT / "mdredux" / "common" / "scripted_effects" / "aral_sea_effects.txt").read_text(encoding="utf-8")
        modifiers = (ROOT / "mdredux" / "common" / "dynamic_modifiers" / "aral_sea_modifiers.txt").read_text(encoding="utf-8")
        events = (ROOT / "mdredux" / "events" / "aral_sea_events.txt").read_text(encoding="utf-8")
        self.assertNotIn("aral_sea_dynamic_modifier", effects + modifiers)
        self.assertNotIn("aral_mod_", effects + modifiers)
        self.assertIn("aral_regional_neglect_modifier", events)
        self.assertIn("aral_regional_crisis_modifier", events)
        self.assertIn("aral_regional_response", (ROOT / "mdredux" / "common" / "decisions" / "aral_sea_decisions.txt").read_text(encoding="utf-8"))

    def test_missing_aral_country_variables_are_initialized_without_resetting_saves(self):
        required = ("aral_sea_restoration", "aral_pending", "aral_relief", "aral_year_clock", "aral_gui_dirty")
        initializer = "\\n".join(
            "if = { limit = { NOT = { has_variable = %s } } set_variable = { %s = 0 } }" % (name, name)
            for name in required
        )
        effects = {
            "aral_initialize_variables": initializer,
            "update_aral_sea": "aral_initialize_variables = yes if = { limit = { owns_state = 717 } clamp_variable = { var = aral_sea_restoration min = -30 max = aral_cap } }",
            "aral_monthly_tick": "aral_initialize_variables = yes if = { limit = { owns_state = 717 } add_to_variable = { aral_year_clock = 1 } }",
        }
        self.assertEqual(audit.aral_initialization_issues(effects), [])

        broken = dict(effects)
        broken["update_aral_sea"] = "if = { limit = { owns_state = 717 } clamp_variable = { var = aral_sea_restoration min = -30 max = aral_cap } }"
        broken["aral_initialize_variables"] = initializer.replace("aral_sea_restoration = 0", "aral_pending = 0", 1)
        findings = audit.aral_initialization_issues(broken)
        self.assertTrue(any("aral_sea_restoration" in message for _, message in findings))
        self.assertTrue(any(area == "scripted effect update_aral_sea" for area, _ in findings))

    def test_shared_generic_cost_keys_do_not_require_local_suffix_entries(self):
        decisions = {"aral_test": "custom_cost_text = cost_4_5"}
        self.assertEqual(audit.implied_custom_cost_localisation_keys(decisions), set())
        self.assertEqual(
            audit.custom_cost_blocked_key_issues(decisions, {"en": {}, "ru": {}}, ["en", "ru"]),
            [],
        )

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
            "aral_state_update": STATE_UPDATE_SOURCE,
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

    def test_state_modifier_uses_kaz_scope_and_is_attached_after_state_variables(self):
        decisions = {
            "aral_ifas": """
available = { aral_unlocked_program = yes owns_state = 717 }
fire_only_once = yes
"""
        }
        effects = {
            "update_aral_sea": "if = { limit = { owns_state = 717 } update_aral = yes }",
            "aral_state_update": STATE_UPDATE_SOURCE,
            "aral_monthly_tick": "if = { limit = { owns_state = 717 } aral_calc_drift = yes }",
        }
        code = """
on_startup = { effect = { KAZ = { if = { limit = { owns_state = 717 } update_aral_sea = yes } } } }
on_monthly = { effect = { if = { limit = { original_tag = KAZ owns_state = 717 } aral_monthly_tick = yes } } }
"""
        code += FOCUS_TRIGGER_SOURCE
        self.assertEqual(audit.aral_ownership_issues(decisions, effects, code), [])

        broken = STATE_UPDATE_SOURCE.replace("is_owned_by = KAZ", "is_owned_by = ROOT")
        broken = broken.replace("KAZ.aral_deficit", "ROOT.aral_deficit")
        broken = broken.replace("add_dynamic_modifier = { modifier = aral_state_modifier }", "")
        findings = audit.aral_ownership_issues(
            decisions, {**effects, "aral_state_update": broken}, code
        )
        self.assertGreaterEqual(len(findings), 5)

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
            "aral_state_update": STATE_UPDATE_SOURCE,
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
            "aral_state_update": STATE_UPDATE_SOURCE,
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
            "aral_state_update": STATE_UPDATE_SOURCE,
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
            "aral_state_update": STATE_UPDATE_SOURCE,
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
            "aral_state_update": STATE_UPDATE_SOURCE,
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
