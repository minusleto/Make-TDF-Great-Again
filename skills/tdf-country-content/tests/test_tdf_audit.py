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
}
country_event = {
  id = kaz_test.4
  title = kaz_test.4.t
  desc = kaz_test.4.d
  is_triggered_only = yes
}
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
                "on_monthly = { effect = { country_event = { id = kaz_test.2 } } }",
                encoding="utf-8")
            scripted = root / "mdredux" / "common" / "scripted_effects"
            scripted.mkdir(parents=True)
            (scripted / "KAZ_effects.txt").write_text(
                "KAZ_test_effect = { country_event = kaz_test.3 }",
                encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            report = audit.build_event_audit(root, countries, loc_index, parsed)
            self.assertFalse(any(item["id"] == "kaz_test.2"
                                 for item in report["unreachable_triggered_events"]))
            self.assertFalse(any(item["id"] == "kaz_test.3"
                                 for item in report["unreachable_triggered_events"]))
            self.assertTrue(any(item["target"] == "kaz_test.3"
                                for item in report["scripted_effect_references"]))
            self.assertTrue(any(item["id"] == "kaz_test.4"
                                for item in report["unreachable_triggered_events"]))
            self.assertEqual(list(audit.iter_event_calls(
                audit.parse_hoi("effect_tooltip = { country_event = kaz_test.4 }").root)), [])

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
