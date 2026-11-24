import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "tdf_audit.py"
SPEC = importlib.util.spec_from_file_location("tdf_audit", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class ParserTests(unittest.TestCase):
    def test_comments_and_braces_inside_quoted_strings(self):
        parsed = audit.parse_hoi(r'''
value = "text # not a comment { } and \"quoted\""
# a real comment with { unbalanced
block = { x = yes }
''')
        self.assertEqual(parsed.issues, [])
        self.assertEqual(parsed.brace_balance, 0)
        value = audit.get_scalar(parsed.root, "value")
        self.assertIn("# not a comment", value)
        self.assertIn("{ }", value)
        self.assertIn('"quoted"', value)

    def test_nested_blocks_and_bare_list_items(self):
        parsed = audit.parse_hoi('''
search_filters = { FOCUS_FILTER_ECONOMY FOCUS_FILTER_INDUSTRY }
prerequisite = { OR = { focus = KAZ_a AND = { focus = KAZ_b focus = KAZ_c } } }
''')
        self.assertEqual(parsed.issues, [])
        filters = audit.get_block(parsed.root, "search_filters")
        self.assertEqual([item.value for item in filters.items if isinstance(item, audit.Token)],
                         ["FOCUS_FILTER_ECONOMY", "FOCUS_FILTER_INDUSTRY"])
        wrapper = audit.get_block(parsed.root, "prerequisite")
        self.assertEqual([audit.scalar(item) for item in audit.nested_entries(wrapper, "focus")],
                         ["KAZ_a", "KAZ_b", "KAZ_c"])

    def test_unclosed_brace_is_reported(self):
        parsed = audit.parse_hoi("focus = { id = KAZ_test")
        self.assertNotEqual(parsed.brace_balance, 0)
        self.assertTrue(any("не закрыт" in issue.message for issue in parsed.issues))

    def test_extra_closing_brace_is_reported(self):
        parsed = audit.parse_hoi("focus = { id = KAZ_test } }")
        self.assertTrue(any("лишняя закрывающая" in issue.message for issue in parsed.issues))

    def test_unclosed_string_is_reported(self):
        parsed = audit.parse_hoi('name = "unfinished')
        self.assertTrue(any("незакрытая строка" in issue.message for issue in parsed.issues))

    def test_prerequisites_nested_under_or_are_collected(self):
        parsed = audit.parse_hoi('''
focus = {
  id = KAZ_target
  prerequisite = { OR = { focus = KAZ_a focus = KAZ_b } }
}
''')
        focus = audit.find_named_blocks(parsed.root, "focus")[0]
        self.assertEqual(audit.focus_prerequisite_ids(focus), ["KAZ_a", "KAZ_b"])


class RepositoryAuditTests(unittest.TestCase):
    def make_repo(self, root: Path):
        mod = root / "mdredux"
        nf = mod / "common" / "national_focus"
        loc = mod / "localisation" / "english"
        events = mod / "events"
        ideas = mod / "common" / "ideas"
        scripted_loc = mod / "common" / "scripted_localisation"
        nf.mkdir(parents=True)
        loc.mkdir(parents=True)
        events.mkdir(parents=True)
        ideas.mkdir(parents=True)
        scripted_loc.mkdir(parents=True)
        (nf / "Kazakhstan_Focus_Tree.txt").write_text('''
focus_tree = {
  country = { modifier = { original_tag = KAZ add = 20 } }
  focus = { id = KAZ_hidden allow_branch = { always = no } completion_reward = { log = "[GetDateText]: Focus KAZ_hidden" } }
  focus = { id = KAZ_visible completion_reward = { log = "[GetDateText]: Focus KAZ_visible" country_event = { id = mdc4.16 } } }
  focus = { id = KAZ_or_child prerequisite = { OR = { focus = KAZ_hidden focus = KAZ_visible } } completion_reward = { log = "[GetDateText]: Focus KAZ_or_child" } }
  focus = { id = KAZ_hidden_child prerequisite = { focus = KAZ_hidden } completion_reward = { log = "[GetDateText]: Focus KAZ_hidden_child" } }
  focus = { id = KAZ_broken prerequisite = { OR = { focus = KAZ_visible focus = KAZ_missing } } completion_reward = { log = "[GetDateText]: Focus KAZ_broken" add_ideas = KAZ_missing_idea } }
}
''', encoding="utf-8")
        (loc / "kazakhstan_a_l_english.yml").write_text('''l_english:
 KAZ_hidden:0 "Hidden"
 KAZ_hidden_desc:0 "A sufficiently long description for testing. "
 KAZ_visible:0 "Visible"
 KAZ_visible_desc:0 "A sufficiently long description for testing. "
''', encoding="utf-8")
        (loc / "zz_extra_l_english.yml").write_text('''l_english:
 KAZ_visible:0 "Duplicate Visible"
 KAZ_or_child:0 "OR Child"
 KAZ_or_child_desc:0 "A sufficiently long description for testing. "
 KAZ_hidden_child:0 "Hidden Child"
 KAZ_hidden_child_desc:0 "A sufficiently long description for testing. "
 KAZ_broken:0 "Broken [KAZ_missing_script]"
 KAZ_broken_desc:0 "A sufficiently long description for testing. "
 KAZ_loc1:0 "A scripted localisation value."
''', encoding="utf-8")
        (events / "Kazakhstan.txt").write_text('''
add_namespace = kaz_test
country_event = { id = kaz_test.1 option = { name = KAZ_visible log = "selected" } }
''', encoding="utf-8")
        (ideas / "Kazakhstan_ideas.txt").write_text(
            'ideas = { country = { KAZ_valid_idea = { allowed = { always = yes } } } }\n', encoding="utf-8")
        (scripted_loc / "99_KAZ_scripted_localisation.txt").write_text(
            'defined_text = { name = KAZ_defined_script text = { trigger = { has_idea = KAZ_valid_idea } localization_key = KAZ_loc1 } }\n', encoding="utf-8")

    def audit_fixture(self, root):
        countries, loc_index = audit.discover(root)
        all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries)
        content = audit.build_content_indexes(root, countries, loc_index)
        result = audit.audit_country("KAZ", countries["KAZ"], loc_index, all_focus,
                                     set(countries), defined_events, namespaces, event_parsed, content)
        return result

    def test_discover_uses_country_selector_not_target_tags_in_focus_logic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            text = tree.read_text(encoding="utf-8")
            text = text.replace(
                "id = KAZ_visible completion_reward",
                "id = KAZ_visible available = { tag = PER } "
                "ai_will_do = { modifier = { strength_ratio = { tag = CHI } } } "
                "completion_reward",
            )
            tree.write_text(text, encoding="utf-8")
            countries, _ = audit.discover(root)
            self.assertIn("KAZ", countries)
            self.assertNotIn("PER", countries)
            self.assertNotIn("CHI", countries)

    def test_discover_includes_eng_tree_from_standard_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "United Kingdom_Focus_Tree.txt"
            tree.write_text("""
focus_tree = {
  country = { original_tag = ENG }
  focus = { id = ENG_test completion_reward = { log = "Focus ENG_test" } }
}
""", encoding="utf-8")
            countries, _ = audit.discover(root)
            self.assertIn("ENG", countries)
            self.assertEqual(countries["ENG"]["tree"], tree)

    def test_localisation_duplicates_are_found_across_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = self.audit_fixture(root)
            self.assertIn("KAZ_visible", result["dup_loc_keys"])

    def test_nested_or_does_not_hide_focus_with_visible_alternative(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = self.audit_fixture(root)
            self.assertIn("KAZ_hidden_child", result["hidden_branch_focus"])
            self.assertNotIn("KAZ_or_child", result["hidden_branch_focus"])
            self.assertIn(("KAZ_broken", "KAZ_missing"), result["prereq_missing"])

    def test_own_idea_and_scripted_loc_references_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = self.audit_fixture(root)
            self.assertIn(("KAZ_broken", "KAZ_missing_idea"), result["idea_not_found"])
            self.assertIn("KAZ_missing_script", result["scripted_loc_missing"])
            self.assertIn(("KAZ_visible", "mdc4.16"), result["event_external"])
            self.assertNotIn("event_external", audit.ERRORS)
            self.assertNotIn("idea_not_found", audit.ERRORS)

    def test_cli_returns_nonzero_for_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_missing_event_in_declared_namespace_is_an_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            text = tree.read_text(encoding="utf-8")
            text = text.replace("mdc4.16", "kaz_test.999")
            tree.write_text(text, encoding="utf-8")
            result = self.audit_fixture(root)
            self.assertIn(("KAZ_visible", "kaz_test.999"), result["event_not_found"])

    def test_cli_returns_zero_for_clean_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            text = tree.read_text(encoding="utf-8")
            text = text.replace("focus = KAZ_missing", "focus = KAZ_hidden")
            text = text.replace(" add_ideas = KAZ_missing_idea", "")
            tree.write_text(text, encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "zz_extra_l_english.yml"
            text = loc.read_text(encoding="utf-8")
            text = text.replace(' KAZ_visible:0 "Duplicate Visible"\n', "")
            text = text.replace("[KAZ_missing_script]", "[KAZ_defined_script]")
            loc.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_rejects_unknown_tag(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "XXX"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 2)

    def test_swap_same_idea_pairs_within_each_swap_block(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            text = tree.read_text(encoding="utf-8")
            text = text.replace(
                'log = "[GetDateText]: Focus KAZ_visible" country_event = { id = mdc4.16 }',
                'log = "[GetDateText]: Focus KAZ_visible" '
                'swap_ideas = { remove_idea = KAZ_old_idea add_idea = KAZ_new_idea } '
                'swap_ideas = { remove_idea = KAZ_other_idea add_idea = KAZ_other_idea } '
                'country_event = { id = mdc4.16 }',
            )
            tree.write_text(text, encoding="utf-8")
            result = self.audit_fixture(root)
            self.assertIn(("KAZ_visible", "KAZ_other_idea"), result["swap_same_idea"])
            self.assertNotIn(("KAZ_visible", "KAZ_old_idea"), result["swap_same_idea"])

    def test_event_ideas_and_external_option_labels_are_classified_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            text = events.read_text(encoding="utf-8")
            text = text.replace(
                'country_event = { id = kaz_test.1 option = { name = KAZ_visible log = "selected" } }',
                'country_event = { id = kaz_test.1 add_ideas = KAZ_missing_from_event '
                'option = { name = GENERIC_accept log = "selected" } }',
            )
            events.write_text(text, encoding="utf-8")
            result = self.audit_fixture(root)
            self.assertIn(("kaz_test.1", "KAZ_missing_from_event"), result["idea_not_found"])
            self.assertIn("GENERIC_accept", result["event_option_label_external"])
            self.assertNotIn("GENERIC_accept", result["event_option_label_missing"])


    def test_event_calls_support_scalar_and_block_syntax(self):
        parsed = audit.parse_hoi("""
country_event = kaz_test.1
news_event = { id = kaz_test.2 days = 1 }
""")
        calls = list(audit.iter_event_calls(parsed.root))
        self.assertEqual([(kind, event_id) for kind, event_id, _ in calls],
                         [("country_event", "kaz_test.1"), ("news_event", "kaz_test.2")])

    def test_event_audit_checks_duplicate_ids_namespaces_reused_keys_and_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_test
add_namespace = kaz_test
country_event = {
  id = kaz_test.1
  title = kaz_test.1.t
  desc = kaz_test.1.d
  is_triggered_only = yes
  option = {
    name = kaz_test.1.a
    country_event = kaz_test.2
  }
}
country_event = {
  id = kaz_test.2
  title = kaz_test.1.t
  desc = kaz_test.2.d
  is_triggered_only = yes
  option = { name = kaz_test.2.a }
}
country_event = {
  id = kaz_test.2
  title = kaz_test.2.t
  desc = kaz_test.2.d
  is_triggered_only = yes
}
country_event = {
  id = kaz_test.3
  title = kaz_test.3.t
  desc = kaz_test.3.d
  is_triggered_only = yes
  trigger = { tag = KAZ FROM = { tag = CHI } }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_test.1.t:0 "Same title"
 kaz_test.1.d:0 "Description one."
 kaz_test.1.a:0 "Continue"
 kaz_test.2.d:0 "Description two."
 kaz_test.2.a:0 "Finish"
 kaz_test.2.t:0 "Other title"
 kaz_test.3.t:0 "Third title"
 kaz_test.3.d:0 "Third description"
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            report = audit.build_event_audit(root, countries, loc_index, parsed)
            self.assertEqual(len(report["duplicate_namespaces"]), 1)
            self.assertEqual(len(report["duplicate_event_ids"]), 1)
            self.assertTrue(any(item["key"] == "kaz_test.1.t"
                                for item in report["reused_title_desc_keys"]))
            self.assertTrue(any(item["id"] == "kaz_test.3"
                                for item in report["unreachable_triggered_events"]))
            self.assertEqual(report["counts"]["country_event"], 4)
            self.assertEqual(report["counts"]["news_event"], 0)

    def test_event_reference_audit_scans_decisions_and_marks_missing_vs_external(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            decisions = root / "mdredux" / "common" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "Kazakhstan.txt").write_text("""
KAZ_category = {
  KAZ_test_decision = {
    complete_effect = {
      country_event = { id = kaz_test.404 }
      news_event = base_md_event.1
    }
  }
}
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            report = audit.build_event_audit(root, countries, loc_index, parsed)
            self.assertTrue(any(item["target"] == "kaz_test.404"
                                for item in report["unresolved_references"]))
            self.assertTrue(any(item["target"] == "base_md_event.1"
                                for item in report["external_references"]))
            self.assertTrue(any(item["source_kind"] == "decision"
                                for item in report["unresolved_references"]))

    def test_event_keys_and_option_keys_use_event_namespace_for_locality(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_test
country_event = {
  id = kaz_test.1
  title = kaz_test.1.t
  desc = kaz_test.1.d
  is_triggered_only = yes
  option = { name = kaz_test.1.a }
}
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            result = audit.audit_country("KAZ", countries["KAZ"], loc_index, all_focus,
                                         set(countries), defined_events, namespaces, event_parsed, content)
            self.assertIn(("kaz_test.1", "kaz_test.1.t"), result["event_title_key_missing"])
            self.assertIn(("kaz_test.1", "kaz_test.1.d"), result["event_desc_key_missing"])
            self.assertIn("kaz_test.1.a", result["event_option_label_missing"])


    def test_effect_tooltips_are_not_calls_and_scripted_effects_are_uncertain_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_test
country_event = {
  id = kaz_test.1
  title = kaz_test.1.t
  desc = kaz_test.1.d
  option = { name = kaz_test.1.a effect_tooltip = { country_event = kaz_test.4 } }
}
country_event = { id = kaz_test.2 title = kaz_test.2.t desc = kaz_test.2.d is_triggered_only = yes }
country_event = { id = kaz_test.3 title = kaz_test.3.t desc = kaz_test.3.d is_triggered_only = yes }
country_event = { id = kaz_test.4 title = kaz_test.4.t desc = kaz_test.4.d is_triggered_only = yes }
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_test.1.t:0 "One"
 kaz_test.1.d:0 "One description."
 kaz_test.1.a:0 "Continue"
 kaz_test.2.t:0 "Two"
 kaz_test.2.d:0 "Two description."
 kaz_test.3.t:0 "Three"
 kaz_test.3.d:0 "Three description."
 kaz_test.4.t:0 "Four"
 kaz_test.4.d:0 "Four description."
""", encoding="utf-8")
            on_actions = root / "mdredux" / "common" / "on_actions"
            on_actions.mkdir(parents=True)
            (on_actions / "00_on_actions.txt").write_text(
                "on_monthly = { effect = { country_event = { id = kaz_test.2 } } }", encoding="utf-8")
            scripted = root / "mdredux" / "common" / "scripted_effects"
            scripted.mkdir(parents=True)
            (scripted / "KAZ_effects.txt").write_text(
                "KAZ_test_effect = { country_event = kaz_test.3 }", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_event_audit(root, countries, loc_index, parsed, content)
            self.assertFalse(any(item["id"] == "kaz_test.2" for item in report["unreachable_triggered_events"]))
            self.assertFalse(any(item["id"] == "kaz_test.3" for item in report["unreachable_triggered_events"]))
            self.assertTrue(any(item["target"] == "kaz_test.3" for item in report["scripted_effect_references"]))
            self.assertTrue(any(item["id"] == "kaz_test.4" for item in report["unreachable_triggered_events"]))
            self.assertEqual(list(audit.iter_event_calls(
                audit.parse_hoi("effect_tooltip = { country_event = kaz_test.4 }").root)), [])

    def test_global_event_audit_checks_ideas_scripted_loc_and_generic_options(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_test
country_event = {
  id = kaz_test.1
  title = kaz_test.1.t
  desc = kaz_test.1.d
  option = { name = kaz_test.1.a add_ideas = KAZ_missing_idea }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_test.1.t:0 "A title [KAZ_missing_script]"
 kaz_test.1.d:0 "A description."
 kaz_test.1.a:0 "Good"
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_event_audit(root, countries, loc_index, parsed, content)
            self.assertTrue(any(item["idea"] == "KAZ_missing_idea" for item in report["missing_event_idea_candidates"]))
            self.assertTrue(any(item["scripted_localisation"] == "KAZ_missing_script"
                                for item in report["missing_event_scripted_localisation"]))
            self.assertTrue(any(item["label"] == "Good" for item in report["generic_option_labels"]))

    def test_decision_audit_checks_local_ids_refs_costs_and_repeatability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            decisions = root / "mdredux" / "common" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "Kazakhstan.txt").write_text("""
KAZ_test_category = {
  KAZ_test_decision = {
    cost = 10
    visible = { AND = { has_completed_focus = KAZ_visible NOT = { has_decision = KAZ_missing_decision } } }
    available = { OR = { has_idea = KAZ_valid_idea FROM = { has_decision = BASE_MD_DECISION } } }
    highlight_states = { highlight_state_targets = { state = 123 } }
    complete_effect = { set_temp_variable = { treasury_change = -5 } modify_treasury_effect = yes country_event = { id = kaz_test.1 } }
  }
  KAZ_repeat_decision = {
    fire_only_once = yes
    days_remove = 30
    days_re_enable = 365
    custom_cost_trigger = { check_variable = { treasury > 5 } }
    custom_cost_text = KAZ_cost_text
    visible = { has_decision = KAZ_missing_decision }
    available = { has_country_flag = KAZ_missing_flag }
    complete_effect = {
      add_political_power = 5
      country_event = kaz_test.404
      add_ideas = KAZ_missing_idea
      has_completed_focus = KAZ_missing_focus
    }
    custom_effect_tooltip = KAZ_missing_tooltip
  }
}
KAZ_duplicate_category = {
  KAZ_test_decision = { cost = 10 complete_effect = { add_political_power = 1 } }
}
KAZ_duplicate_category = {
  KAZ_another_decision = { cost = -1 }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "zz_extra_l_english.yml"
            text = loc.read_text(encoding="utf-8")
            text += """
 KAZ_test_category:0 "Test category"
 KAZ_duplicate_category:0 "Duplicate category"
 KAZ_test_decision:0 "Test decision"
 KAZ_repeat_decision:0 "Repeat decision"
 KAZ_another_decision:0 "Another decision"
 KAZ_cost_text:0 "Treasury 5"
"""
            loc.write_text(text, encoding="utf-8")
            countries, loc_index = audit.discover(root)
            all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_decision_audit(root, countries, loc_index, all_focus,
                                                defined_events, namespaces, event_parsed, content)
            self.assertEqual(report["counts"], {"files": 1, "categories": 3, "decisions": 4})
            self.assertEqual(report["duplicate_category_ids"][0]["scope"], "same_file")
            self.assertEqual(len(report["duplicate_decision_ids"]), 1)
            self.assertTrue(any(item["target"] == "KAZ_missing_decision" for item in report["missing_decision_references"]))
            self.assertTrue(any(item["target"] == "BASE_MD_DECISION" for item in report["external_decision_references"]))
            self.assertTrue(any(item["target"] == "KAZ_missing_focus" for item in report["missing_focus_references"]))
            self.assertTrue(any(item["target"] == "kaz_test.404" for item in report["missing_event_references"]))
            self.assertTrue(any(item["idea"] == "KAZ_missing_idea" for item in report["idea_reference_candidates"]))
            self.assertTrue(any(item["flag"] == "KAZ_missing_flag" for item in report["flag_reference_candidates"]))
            self.assertTrue(any(item["decision"] == "KAZ_repeat_decision" for item in report["custom_cost_without_debit"]))
            self.assertTrue(any(item["decision"] == "KAZ_repeat_decision" for item in report["repeatability_warnings"]))
            self.assertTrue(any(item["decision"] == "KAZ_another_decision" and item["field"] == "cost"
                                for item in report["invalid_numeric_fields"]))
            self.assertFalse(report["state_inventory_available"])
            self.assertFalse(report["unknown_highlight_states"])

    def test_decision_audit_separates_external_refs_and_accepts_timer_and_custom_cost_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            decisions = root / "mdredux" / "common" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "Kazakhstan.txt").write_text("""
KAZ_category = {
  KAZ_external = {
    days_remove = -1
    custom_cost_trigger = { check_variable = { treasury > 10 } }
    custom_cost_text = cost_10_0
    visible = { has_decision = BASE_MD_DECISION }
    complete_effect = { subtract_from_variable = { treasury = 10 } news_event = base_md_event.1 }
  }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "zz_extra_l_english.yml"
            text = loc.read_text(encoding="utf-8")
            text += """
 KAZ_category:0 "Category"
 KAZ_external:0 "External"
"""
            loc.write_text(text, encoding="utf-8")
            countries, loc_index = audit.discover(root)
            all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_decision_audit(root, countries, loc_index, all_focus,
                                                defined_events, namespaces, event_parsed, content)
            self.assertTrue(any(item["target"] == "BASE_MD_DECISION" for item in report["external_decision_references"]))
            self.assertTrue(any(item["target"] == "base_md_event.1" for item in report["external_event_references"]))
            self.assertFalse(report["invalid_numeric_fields"])
            self.assertFalse(report["custom_cost_without_debit"])


    def test_industry_audit_indexes_global_mio_equipment_and_variant_references(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)

            mio_dir = root / "mdredux" / "common" / "military_industrial_organization" / "organizations"
            mio_dir.mkdir(parents=True)
            (mio_dir / "MIO.txt").write_text("""\
KAZ_local_mio = {
  allowed = { original_tag = KAZ }
  visible = { has_completed_focus = KAZ_visible }
  name = KAZ_local_mio_name
  include = generic_tank_equipment_organization
}
USA_foreign_mio = {
  allowed = { original_tag = USA }
  name = USA_foreign_mio_name
}
KAZ_wrong_company_mio = {
  allowed = { original_tag = KAZ }
  name = KAZ_name_target
}
KAZ_name_target = {
  allowed = { original_tag = KAZ }
  name = KAZ_name_target_name
}
KAZ_missing_loc_mio = {
  allowed = { original_tag = KAZ }
  name = KAZ_missing_localisation
}
""", encoding="utf-8")

            equipment_dir = root / "mdredux" / "common" / "units" / "equipment"
            equipment_dir.mkdir(parents=True)
            (equipment_dir / "test_equipment.txt").write_text("""\
equipments = {
  KAZ_test_equipment = {
    year = 2020
    is_buildable = yes
  }
}
""", encoding="utf-8")
            modules_dir = equipment_dir / "modules"
            modules_dir.mkdir()
            (modules_dir / "test_modules.txt").write_text("""\
equipment_modules = {
  test_module = {
    category = test_category
  }
}
""", encoding="utf-8")
            technology_dir = root / "mdredux" / "common" / "technologies"
            technology_dir.mkdir(parents=True)
            (technology_dir / "test_tech.txt").write_text("""\
technologies = {
  KAZ_test_equipment_tech = {
    research_cost = 1
  }
}
""", encoding="utf-8")

            focus_path = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            source = focus_path.read_text(encoding="utf-8")
            source = source.rsplit("}", 1)[0] + """
  focus = {
    id = KAZ_mio_equipment_test
    completion_reward = {
      mio:KAZ_local_mio = { add_mio_funds = 100 }
      unlock_military_industrial_organization_tooltip = mio:USA_foreign_mio
      mio:KAZ_missing_mio = { add_mio_funds = 50 }
      mio:USA_external_mio = { add_mio_funds = 50 }
      create_equipment_variant = {
        name = "KAZ Test Variant"
        type = KAZ_test_equipment
        design_team = mio:USA_foreign_mio
        allow_without_tech = yes
        modules = { main_armament_slot = test_module }
      }
      create_equipment_variant = {
        name = "Missing Variant"
        type = KAZ_missing_equipment
      }
      add_equipment_to_stockpile = {
        type = KAZ_test_equipment
        amount = 5
        producer = KAZ
        variant_name = "KAZ Test Variant"
      }
    }
  }
}
"""
            focus_path.write_text(source, encoding="utf-8")

            loc_path = root / "mdredux" / "localisation" / "english" / "zz_extra_l_english.yml"
            loc_text = loc_path.read_text(encoding="utf-8") + """
 KAZ_local_mio_name:0 "Local MIO"
 USA_foreign_mio_name:0 "Foreign MIO"
 KAZ_name_target:0 "Company name"
 KAZ_name_target_name:0 "Target MIO"
 KAZ_test_equipment:0 "KAZ test equipment"
"""
            loc_path.write_text(loc_text, encoding="utf-8")

            countries, loc_index = audit.discover(root)
            all_focus, _, _, event_parsed = audit.build_global_indexes(countries)
            report = audit.build_industry_audit(root, countries, loc_index, all_focus, event_parsed)

            self.assertEqual(report["counts"]["mio_files"], 1)
            self.assertEqual(report["counts"]["mio_definitions"], 5)
            self.assertIn("USA_foreign_mio", {item["id"] for item in report["mio_definitions"]})
            self.assertTrue(any(item["mio"] == "KAZ_missing_mio"
                                for item in report["missing_local_mio_references"]))
            self.assertTrue(any(item["mio"] == "USA_external_mio"
                                for item in report["external_mio_references"]))
            self.assertFalse(any(item["mio"] == "USA_foreign_mio"
                                 for item in report["missing_local_mio_references"]))
            self.assertTrue(any(item["mio"] == "KAZ_wrong_company_mio"
                                and item["other_mio_definition"] == "KAZ_name_target"
                                for item in report["mio_name_matches_other_mio"]))
            self.assertTrue(any(item["name_key"] == "KAZ_missing_localisation"
                                for item in report["missing_local_mio_name_localisation"]))
            self.assertTrue(any(item["type"] == "KAZ_missing_equipment"
                                for item in report["unknown_equipment_type_references"]))
            self.assertFalse(any(item["type"] == "KAZ_test_equipment"
                                 for item in report["unknown_equipment_type_references"]))
            self.assertFalse(report["unknown_module_references"])
            self.assertEqual(report["counts"]["technology_ids"], 1)
            self.assertTrue(any(item["amount"] == "5" and item["producer"] == "KAZ"
                                for item in report["stockpile_grants"]))

    def test_idea_lifecycle_audit_keeps_legacy_ids_and_checks_tooltip_modes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)

            ideas_path = root / "mdredux" / "common" / "ideas" / "Kazakhstan_ideas.txt"
            ideas_path.write_text("""\
ideas = {
  country = {
    KAZ_valid_idea = {
      picture = generic_company
      modifier = { stability_factor = 0.02 }
    }
    KAZ_legacy = {
      name = KAZ_legacy_name
      picture = generic_company
      on_add = { add_to_array = { global.KAZ_registry = THIS } }
      on_remove = { remove_from_array = { global.KAZ_registry = THIS } }
      cancel = { has_war = yes }
      allowed_civil_war = { always = yes }
      modifier = { custom_modifier_tooltip = KAZ_static_tt }
    }
    KAZ_legacy_stage1 = {
      name = KAZ_legacy
      picture = generic_company
      modifier = { custom_modifier_tooltip = KAZ_dynamic_tt }
    }
    CPLP_member = {
      name = CPLP_member
      picture = generic_company
      modifier = { stability_factor = 0.01 }
    }
  }
  hidden_ideas = {
    KAZ_hidden_component = {
      name = KAZ_legacy
      on_add = { set_country_flag = KAZ_hidden_live }
      on_remove = { clr_country_flag = KAZ_hidden_live }
      modifier = { consumer_goods_factor = -0.01 }
    }
  }
}
""", encoding="utf-8")

            focus_path = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            focus_text = focus_path.read_text(encoding="utf-8")
            focus_text = focus_text.rsplit("}", 1)[0] + """
  focus = {
    id = KAZ_idea_lifecycle_test
    completion_reward = {
      add_ideas = CPLP_member
      add_timed_idea = { idea = KAZ_hidden_component days = 30 }
      swap_ideas = { remove_idea = KAZ_legacy add_idea = KAZ_legacy_stage1 }
    }
  }
}
"""
            focus_path.write_text(focus_text, encoding="utf-8")

            script_path = root / "mdredux" / "common" / "scripted_localisation" / "99_KAZ_scripted_localisation.txt"
            script_text = script_path.read_text(encoding="utf-8") + """
defined_text = {
  name = KAZ_dynamic_loc
  text = {
    trigger = { has_idea = KAZ_hidden_component }
    localization_key = KAZ_dynamic_piece
  }
}
"""
            script_path.write_text(script_text, encoding="utf-8")

            loc_path = root / "mdredux" / "localisation" / "english" / "zz_extra_l_english.yml"
            loc_text = loc_path.read_text(encoding="utf-8") + """
 KAZ_valid_idea:0 "Valid idea"
 KAZ_legacy_name:0 "Legacy spirit"
 KAZ_legacy:0 "Legacy spirit"
 CPLP_member:0 "CPLP member"
 KAZ_static_tt:0 "$KAZ_static_piece$"
 KAZ_static_piece:0 "Static component."
 KAZ_dynamic_tt:0 "[KAZ_dynamic_loc]"
 KAZ_dynamic_piece:0 "Dynamic component."
"""
            loc_path.write_text(loc_text, encoding="utf-8")

            countries, loc_index = audit.discover(root)
            all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_idea_lifecycle_audit(root, countries, loc_index, content, event_parsed)

            self.assertIn("CPLP_member", content["idea_ids"]["KAZ"])
            self.assertEqual(report["counts"]["idea_files"], 1)
            self.assertEqual(report["counts"]["definitions"], 5)
            self.assertTrue(any(item["idea"] == "KAZ_legacy"
                                for item in report["legacy_ids_without_idea_suffix"]))
            self.assertTrue(any(item["idea"] == "KAZ_legacy_stage1" and item["base_idea"] == "KAZ_legacy"
                                for item in report["stage_name_links"]))
            self.assertTrue(any(item["idea"] == "KAZ_hidden_component" and item["usage"] == "timed_add"
                                for item in report["idea_references"]))
            self.assertTrue(any(item["idea"] == "CPLP_member" and item["usage"] == "add"
                                for item in report["idea_references"]))
            self.assertTrue(any(item["idea"] == "KAZ_legacy" and item["usage"] == "remove"
                                for item in report["idea_references"]))
            self.assertFalse(any(item["tooltip_key"] == "KAZ_static_tt"
                                 for item in report["custom_modifier_tooltip_scripted_loc_candidates"]))
            self.assertTrue(any(item["tooltip_key"] == "KAZ_dynamic_tt"
                                and "KAZ_dynamic_loc" in item["bracket_references"]
                                for item in report["custom_modifier_tooltip_scripted_loc_candidates"]))
            self.assertFalse(report["missing_name_localisation"])
            self.assertTrue(any(item["idea"] == "KAZ_missing_idea"
                                for item in report["missing_local_idea_references"]))

    def test_invalid_utf8_is_reported_instead_of_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.txt"
            path.write_bytes(b"name = \"ok\"\nvalue = \xff")
            with self.assertRaises(audit.AuditInputError):
                audit.read(path)

    def test_json_report_is_written_as_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            report = root / "reports" / "audit.json"
            report.parent.mkdir()
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ", "--json", str(report)],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            data = __import__("json").loads(report.read_text(encoding="utf-8"))
            self.assertIn("KAZ", data)


if __name__ == "__main__":
    unittest.main()
