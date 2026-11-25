import importlib.util
import re
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

    def test_anonymous_blocks_are_valid_list_items_and_nested_entries_are_walked(self):
        parsed = audit.parse_hoi("""
milestones = {
    { effect = { set_variable = fighters_milestone_var } }
    { effect = { set_variable = bombers_milestone_var } }
}
""")
        self.assertEqual(parsed.issues, [])
        self.assertEqual(parsed.brace_balance, 0)
        milestones = audit.get_block(parsed.root, "milestones")
        variable_entries = [
            entry for entry in audit.walk_entries(milestones)
            if entry.key.value == "set_variable"
        ]
        self.assertEqual(
            [audit.scalar(entry) for entry in variable_entries],
            ["fighters_milestone_var", "bombers_milestone_var"],
        )
        self.assertEqual(
            sum(1 for entry in audit.walk_entries(milestones) if entry.key.value == "set_variable"),
            2,
        )

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
 KAZ_hidden:0 "Hidden"
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

    def make_clean_cli_fixture(self, root: Path):
        self.make_repo(root)
        tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
        text = tree.read_text(encoding="utf-8")
        text = text.replace("focus = KAZ_missing", "focus = KAZ_hidden")
        text = text.replace(" add_ideas = KAZ_missing_idea", "")
        tree.write_text(text, encoding="utf-8")
        loc = root / "mdredux" / "localisation" / "english" / "zz_extra_l_english.yml"
        text = loc.read_text(encoding="utf-8")
        text = text.replace(' KAZ_visible:0 "Duplicate Visible"' + chr(10), "")
        text = text.replace("[KAZ_missing_script]", "[KAZ_defined_script]")
        loc.write_text(text, encoding="utf-8")
        main_loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
        main_text = main_loc.read_text(encoding="utf-8")
        main_text += chr(10) + ' kaz_test.1.t:0 "A test event."' + chr(10) + ' kaz_test.1.d:0 "The test event description is sufficiently long."' + chr(10)
        main_loc.write_text(main_text, encoding="utf-8")
        events = root / "mdredux" / "events" / "Kazakhstan.txt"
        events.write_text(
            chr(10).join([
                "add_namespace = kaz_test",
                "country_event = {",
                "  id = kaz_test.1",
                "  title = kaz_test.1.t",
                "  desc = kaz_test.1.d",
                '  option = { name = KAZ_visible log = "selected" }',
                "}",
                "",
            ]),
            encoding="utf-8",
        )

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

    def test_discover_includes_eng_tree_and_britain_event_alias(self):
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
            events = root / "mdredux" / "events" / "Britain.txt"
            events.write_text("""
add_namespace = britain_test
country_event = {
  id = britain_test.1
  title = britain_test.1.t
  desc = britain_test.1.d
  option = {
    name = ENG_test_option
    log = "selected"
    add_ideas = ENG_missing_idea
  }
}
""", encoding="utf-8")

            countries, loc_index = audit.discover(root)
            self.assertIn("ENG", countries)
            self.assertEqual(countries["ENG"]["tree"], tree)
            self.assertEqual(countries["ENG"]["events"], events)

            all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            event_report = audit.build_event_audit(root, countries, loc_index, event_parsed, content)
            candidate = next(
                item for item in event_report["missing_event_idea_candidates"]
                if item["idea"] == "ENG_missing_idea"
            )
            self.assertEqual(candidate["classification"], "local_candidate")

    def test_discover_finds_focus_trees_in_nested_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            nested = root / "mdredux" / "common" / "national_focus" / "regional"
            nested.mkdir()
            tree = nested / "Serbia_Focus_Tree.txt"
            tree.write_text("""
focus_tree = {
  country = { original_tag = SER }
  focus = { id = SER_test }
}
""", encoding="utf-8")
            countries, _ = audit.discover(root)
            self.assertIn("SER", countries)
            self.assertEqual(countries["SER"]["tree"], tree)

    def test_localisation_duplicates_are_found_across_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = self.audit_fixture(root)
            self.assertIn("KAZ_visible", result["dup_loc_keys"])
            self.assertNotIn("KAZ_visible", result["dup_loc_keys_identical"])

    def test_identical_localisation_duplicates_are_warn_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = self.audit_fixture(root)
            self.assertIn("KAZ_hidden", result["dup_loc_keys_identical"])
            self.assertNotIn("KAZ_hidden", result["dup_loc_keys"])
            self.assertNotIn("dup_loc_keys_identical", audit.ERRORS)

    def test_scripted_localisation_duplicates_are_split_by_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            scripts = root / "mdredux" / "common" / "scripted_localisation"
            (scripts / "98_KAZ_duplicate_a.txt").write_text("""
defined_text = { name = KAZ_identical_loc text = { trigger = { always = yes } localization_key = KAZ_loc1 } }
defined_text = { name = KAZ_conflicting_loc text = { trigger = { always = yes } localization_key = KAZ_loc1 } }
""", encoding="utf-8")
            (scripts / "99_KAZ_duplicate_b.txt").write_text("""
defined_text = { name = KAZ_identical_loc text = { trigger = { always = yes } localization_key = KAZ_loc1 } }
defined_text = { name = KAZ_conflicting_loc text = { trigger = { always = no } localization_key = KAZ_loc1 } }
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            result = audit.audit_country("KAZ", countries["KAZ"], loc_index, set(), set(countries),
                                         set(), set(), parsed, content)
            self.assertIn("KAZ_identical_loc", result["scripted_loc_duplicate_identical"])
            self.assertIn("KAZ_conflicting_loc", result["scripted_loc_duplicate"])
            self.assertNotIn("scripted_loc_duplicate_identical", audit.ERRORS)

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
            self.make_clean_cli_fixture(root)
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_missing_event_fields_and_option_log_return_nonzero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_clean_cli_fixture(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_test
country_event = {
  id = kaz_test.missing_fields
  option = { }
}
""", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("missing_title_fields: 1", result.stdout)
            self.assertIn("missing_desc_fields: 1", result.stdout)
            self.assertIn("missing_option_names: 1", result.stdout)
            self.assertIn("options_without_log: 1", result.stdout)

    def test_cli_require_external_registry_rejects_missing_registry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_clean_cli_fixture(root)
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ",
                 "--require-external-registry"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("обязательный реестр внешних зависимостей не найден", result.stderr)

    def test_cli_require_external_registry_accepts_valid_registry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_clean_cli_fixture(root)
            registry = root / "docs" / "research" / "external-dependencies.json"
            registry.parent.mkdir(parents=True)
            registry.write_text('{"schema_version": 1, "dependencies": []}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ",
                 "--require-external-registry"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_parse_error_aggregation_covers_every_subsystem(self):
        for field in audit.PARSE_ERROR_FIELDS:
            with self.subTest(field=field):
                self.assertTrue(audit.reports_have_parse_errors({field: ["broken input"]}))
        self.assertFalse(audit.reports_have_parse_errors({"parse_errors": []}))

    def test_event_reachability_includes_history_and_extensionless_scripts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_test
country_event = { id = kaz_test.10 title = kaz_test.10.t desc = kaz_test.10.d is_triggered_only = yes }
country_event = { id = kaz_test.11 title = kaz_test.11.t desc = kaz_test.11.d is_triggered_only = yes }
country_event = { id = kaz_test.12 title = kaz_test.12.t desc = kaz_test.12.d is_triggered_only = yes }
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_test.10.t:0 "Scheduled from history"
 kaz_test.10.d:0 "History event."
 kaz_test.11.t:0 "Scheduled from script"
 kaz_test.11.d:0 "Script event."
 kaz_test.12.t:0 "Scheduled from on action"
 kaz_test.12.d:0 "On-action event."
""", encoding="utf-8")

            history = root / "mdredux" / "common" / "history" / "countries"
            history.mkdir(parents=True)
            (history / "KAZ - Kazakhstan.txt").write_text("""
2000.1.1 = {
    country_event = { id = kaz_test.10 days = 1 }
}
""", encoding="utf-8")

            scripted = root / "mdredux" / "common" / "scripted_effects"
            scripted.mkdir(parents=True)
            (scripted / "00_extensionless_effect").write_text(
                "KAZ_schedule_event = { country_event = kaz_test.11 }", encoding="utf-8")
            on_actions = root / "mdredux" / "common" / "on_actions"
            on_actions.mkdir(parents=True)
            (on_actions / "00_extensionless_on_action").write_text(
                "on_monthly = { effect = { country_event = kaz_test.12 } }", encoding="utf-8")

            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            report = audit.build_event_audit(root, countries, loc_index, parsed)
            orphan_ids = {item["id"] for item in report["unreachable_triggered_events"]}
            self.assertNotIn("kaz_test.10", orphan_ids)
            self.assertNotIn("kaz_test.11", orphan_ids)
            self.assertNotIn("kaz_test.12", orphan_ids)
            self.assertTrue(any(
                item["target"] == "kaz_test.11"
                and Path(item["source"]).name == "00_extensionless_effect"
                for item in report["scripted_effect_references"]
            ))

    def test_cli_returns_nonzero_for_new_subsystem_parse_errors(self):
        cases = [
            ("mdredux/common/military_industrial_organization/organizations/KAZ_bad.txt",
             "KAZ_bad_mio = {", "industry mio_parse_errors: 1"),
            ("mdredux/common/units/equipment/KAZ_bad.txt",
             "equipments = {", "industry equipment_parse_errors: 1"),
            ("mdredux/common/units/equipment/modules/KAZ_bad.txt",
             "equipment_modules = {", "industry module_parse_errors: 1"),
            ("mdredux/common/technologies/KAZ_bad.txt",
             "technologies = {", "industry technology_parse_errors: 1"),
            ("mdredux/common/scripted_effects/00_extensionless_bad",
             "KAZ_bad_effect = {", "state_flow script_parse_errors: 1"),
            ("mdredux/common/scripted_triggers/00_extensionless_bad",
             "KAZ_bad_trigger = {", "state_flow script_parse_errors: 1"),
        ]
        for relative_path, contents, expected_output in cases:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    self.make_clean_cli_fixture(root)
                    bad_file = root / relative_path
                    bad_file.parent.mkdir(parents=True, exist_ok=True)
                    bad_file.write_text(contents, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                        universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, check=False,
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn(expected_output, result.stdout)

    def test_cli_rejects_invalid_external_dependency_registry_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_clean_cli_fixture(root)
            registry = root / "docs" / "research" / "external-dependencies.json"
            registry.parent.mkdir(parents=True)
            registry.write_text("{ invalid json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("ОШИБКА", result.stderr)

    def test_cli_returns_nonzero_for_invalid_external_dependency_registry_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_clean_cli_fixture(root)
            registry = root / "docs" / "research" / "external-dependencies.json"
            registry.parent.mkdir(parents=True)
            registry.write_text('{"schema_version": 999, "dependencies": []}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(root), "--tags", "KAZ"],
                universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

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


    def test_event_option_log_key_mismatch_is_warn_only(self):
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
  option = { name = kaz_test.1.a log = "[GetDateText]: [This.GetName]: kaz_test.1.a executed" }
  option = { name = kaz_test.1.b log = "[GetDateText]: [This.GetName]: kaz_test.1.a executed" }
  option = { name = kaz_test.1.c log = "Custom diagnostic message" }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_test.1.t:0 "A test event"
 kaz_test.1.d:0 "A sufficiently descriptive test event."
 kaz_test.1.a:0 "First option"
 kaz_test.1.b:0 "Second option"
 kaz_test.1.c:0 "Third option"
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            report = audit.build_event_audit(root, countries, loc_index, parsed)
            self.assertEqual(len(report["option_log_key_mismatches"]), 1)
            finding = report["option_log_key_mismatches"][0]
            self.assertEqual(finding["event_id"], "kaz_test.1")
            self.assertEqual(finding["option_key"], "kaz_test.1.b")
            self.assertEqual(finding["log_key"], "kaz_test.1.a")
            self.assertGreater(finding["option_line"], 0)
            self.assertGreater(finding["log_line"], 0)
            self.assertNotIn("option_log_key_mismatches", audit.ERRORS)

    def test_event_calls_support_scalar_and_block_syntax(self):
        parsed = audit.parse_hoi("""
country_event = kaz_test.1
news_event = { id = kaz_test.2 days = 1 }
""")
        calls = list(audit.iter_event_calls(parsed.root))
        self.assertEqual([(kind, event_id) for kind, event_id, _ in calls],
                         [("country_event", "kaz_test.1"), ("news_event", "kaz_test.2")])

    def test_event_audit_accepts_conditional_title_desc_and_hidden_events(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text(""" 
add_namespace = kaz_test
country_event = {
  id = kaz_test.conditional
  title = {
    trigger = { tag = KAZ }
    text = kaz_test.conditional.t1
  }
  title = {
    trigger = { NOT = { tag = KAZ } }
    text = kaz_test.conditional.t2
  }
  desc = {
    trigger = { tag = KAZ }
    text = kaz_test.conditional.d1
  }
  option = { name = kaz_test.conditional.a log = "selected" }
}
country_event = {
  id = kaz_test.hidden
  hidden = yes
  is_triggered_only = yes
  option = { name = kaz_test.hidden.a log = "hidden event" }
}
country_event = {
  id = kaz_test.missing
  option = { name = kaz_test.missing.a log = "still missing title and desc" }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_test.conditional.t1:0 "Conditional title one"
 kaz_test.conditional.t2:0 "Conditional title two"
 kaz_test.conditional.d1:0 "Conditional description."
 kaz_test.conditional.a:0 "Continue"
 kaz_test.hidden.a:0 "Hidden"
 kaz_test.missing.a:0 "Acknowledge"
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            _, _, _, parsed = audit.build_global_indexes(countries, root)
            report = audit.build_event_audit(root, countries, loc_index, parsed)

            self.assertFalse(any(item["id"] == "kaz_test.conditional"
                                 for item in report["missing_title_fields"]))
            self.assertFalse(any(item["id"] == "kaz_test.conditional"
                                 for item in report["missing_desc_fields"]))
            self.assertFalse(any(item["id"] == "kaz_test.hidden"
                                 for item in report["missing_title_fields"]))
            self.assertFalse(any(item["id"] == "kaz_test.hidden"
                                 for item in report["missing_desc_fields"]))
            self.assertTrue(any(item["id"] == "kaz_test.missing"
                                for item in report["missing_title_fields"]))
            self.assertTrue(any(item["id"] == "kaz_test.missing"
                                for item in report["missing_desc_fields"]))
            conditional = next(item for item in report["metadata"] if item["id"] == "kaz_test.conditional")
            self.assertEqual(conditional["title_keys"], ["kaz_test.conditional.t1", "kaz_test.conditional.t2"])
            self.assertEqual(conditional["desc_keys"], ["kaz_test.conditional.d1"])
            self.assertTrue(next(item for item in report["metadata"] if item["id"] == "kaz_test.hidden")["hidden"])

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


    def test_decision_gate_conflicts_are_warn_only_and_skip_or_alternatives(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            decisions = root / "mdredux" / "common" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "Kazakhstan.txt").write_text("""\\
KAZ_gate_category = {
  KAZ_flag_conflict = {
    visible = { AND = { has_country_flag = KAZ_stage_open NOT = { has_idea = KAZ_stage_closed } } }
    available = { AND = { NOT = { has_country_flag = KAZ_stage_open } has_idea = KAZ_stage_closed } }
  }
  KAZ_nor_conflict = {
    visible = { NOR = { has_country_flag = KAZ_nor_left has_country_flag = KAZ_nor_right } }
    available = { has_country_flag = KAZ_nor_right }
  }
  KAZ_or_safe = {
    visible = { OR = { has_country_flag = KAZ_or_left has_country_flag = KAZ_or_right } }
    available = { NOT = { has_country_flag = KAZ_or_left } }
  }
  KAZ_same_condition = {
    visible = { has_country_flag = KAZ_ready }
    available = { has_country_flag = KAZ_ready }
  }
}
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            all_focus, defined_events, namespaces, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_decision_audit(
                root, countries, loc_index, all_focus, defined_events,
                namespaces, event_parsed, content,
            )

            conflicts = report["decision_gate_conflicts"]
            self.assertEqual(len(conflicts), 3)
            by_decision = {}
            for item in conflicts:
                by_decision.setdefault(item["decision"], []).append(item)

            self.assertEqual(len(by_decision["KAZ_flag_conflict"]), 2)
            self.assertEqual(len(by_decision["KAZ_nor_conflict"]), 1)
            self.assertNotIn("KAZ_or_safe", by_decision)
            self.assertNotIn("KAZ_same_condition", by_decision)
            self.assertEqual(
                {(item["predicate"], item["visible_requirement"], item["available_requirement"])
                 for item in by_decision["KAZ_flag_conflict"]},
                {
                    ("has_country_flag = KAZ_stage_open", "must_be_true", "must_be_false"),
                    ("has_idea = KAZ_stage_closed", "must_be_false", "must_be_true"),
                },
            )
            self.assertEqual(
                by_decision["KAZ_nor_conflict"][0]["predicate"],
                "has_country_flag = KAZ_nor_right",
            )
            self.assertEqual(
                {item["classification"] for item in conflicts},
                {"warn_only_candidate"},
            )
            self.assertNotIn("decision_gate_conflicts", audit.ERRORS)
            self.assertNotIn("decision_gate_conflicts", audit.WARNS)

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
    KAZ_legacy_stage2 = {
      name = KAZ_legacy
      picture = generic_company
      modifier = { stability_factor = 0.03 }
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
  focus = {
    id = KAZ_legacy_stage2_direct_grant
    completion_reward = { add_ideas = KAZ_legacy_stage2 }
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
            self.assertEqual(report["counts"]["definitions"], 6)
            self.assertTrue(any(item["idea"] == "KAZ_legacy"
                                for item in report["legacy_ids_without_idea_suffix"]))
            self.assertTrue(any(item["idea"] == "KAZ_legacy_stage1" and item["base_idea"] == "KAZ_legacy"
                                for item in report["stage_name_links"]))
            self.assertTrue(any(
                item["remove_idea"] == "KAZ_legacy" and item["add_idea"] == "KAZ_legacy_stage1"
                for item in report["stage_swap_transitions"]
            ))
            self.assertTrue(any(
                item["idea"] == "KAZ_legacy_stage2"
                for item in report["stage_grant_without_swap_candidates"]
            ))
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


    def test_idea_lifecycle_indexes_extensionless_scripted_effect_grants(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            scripts = root / "mdredux" / "common" / "scripted_effects"
            scripts.mkdir(parents=True)
            script_path = scripts / "00_extensionless_idea_grants"
            script_path.write_text(
                "KAZ_grant_valid_idea = { add_ideas = KAZ_valid_idea }",
                encoding="utf-8",
            )
            countries, loc_index = audit.discover(root)
            _, _, _, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            report = audit.build_idea_lifecycle_audit(root, countries, loc_index, content, event_parsed)
            self.assertTrue(any(
                item["idea"] == "KAZ_valid_idea" and item["usage"] == "add"
                and item["path"] == str(script_path)
                for item in report["idea_references"]
            ))
            self.assertFalse(any(
                item["idea"] == "KAZ_valid_idea"
                for item in report["not_locally_granted_candidates"]
            ))


    def test_state_flow_indexes_flags_variables_arrays_scripts_and_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)

            common = root / "mdredux" / "common"
            effects = common / "scripted_effects"
            effects.mkdir(parents=True)
            (effects / "KAZ_scripted_effects.txt").write_text("""
KAZ_apply_state = {
  set_country_flag = KAZ_state_flag
  set_variable = { var = KAZ_counter value = 1 }
  add_to_array = { KAZ_registry = KAZ }
}
""", encoding="utf-8")
            # Script files without a .txt extension are also valid inputs for the index.
            (effects / "00_shared_effects").write_text("""
KAZ_extensionless_effect = { set_country_flag = KAZ_extensionless_flag }
""", encoding="utf-8")

            triggers = common / "scripted_triggers"
            triggers.mkdir(parents=True)
            (triggers / "KAZ_scripted_triggers.txt").write_text("""
KAZ_state_ready = {
  has_country_flag = KAZ_state_flag
  check_variable = { var = KAZ_counter value > 0 }
}
""", encoding="utf-8")

            on_actions = common / "on_actions"
            on_actions.mkdir(parents=True)
            (on_actions / "00_on_actions.txt").write_text("""
on_actions = {
  on_startup = {
    effect = { KAZ_apply_state = yes }
  }
}
""", encoding="utf-8")

            history = common / "history" / "countries"
            history.mkdir(parents=True)
            (history / "KAZ - Kazakhstan.txt").write_text("""
2000.1.1 = {
  add_ideas = { KAZ_startup_idea }
  set_country_flag = KAZ_history_flag
  set_variable = { KAZ_history_counter = 5 }
  add_to_array = { KAZ_history_array = KAZ }
  country_event = { id = kaz_test.1 days = 80 }
}
""", encoding="utf-8")

            ideas = common / "ideas" / "Kazakhstan_ideas.txt"
            ideas.write_text("""
ideas = {
  country = {
    KAZ_balanced_state_idea = {
      on_add = { add_to_array = { KAZ_registry_idea = KAZ } }
      on_remove = { remove_from_array = { KAZ_registry_idea = KAZ } }
    }
    KAZ_one_sided_state_idea = {
      on_add = { set_country_flag = KAZ_one_sided_flag }
    }
  }
}
""", encoding="utf-8")

            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            source = tree.read_text(encoding="utf-8")
            source = source.rsplit("}", 1)[0] + """
  focus = {
    id = KAZ_state_flow_test
    available = {
      has_country_flag = KAZ_state_flag
      check_variable = { var = KAZ_counter value > 0 }
      any_of_scopes = { array = KAZ_registry always = yes }
      KAZ_state_ready = yes
      USA_base_trigger = yes
    }
    completion_reward = {
      KAZ_apply_state = yes
      KAZ_extensionless_effect = yes
      KAZ_missing_scripted_call = yes
    }
  }
}
"""
            tree.write_text(source, encoding="utf-8")

            countries, _ = audit.discover(root)
            _, _, _, event_parsed = audit.build_global_indexes(countries, root)
            report = audit.build_state_flow_audit(root, countries, event_parsed)

            self.assertEqual(report["counts"]["history_files"], 1)
            self.assertEqual(report["history_tags"], ["KAZ"])
            self.assertTrue(report["on_action_inventory_available"])
            self.assertTrue(report["scripted_trigger_inventory_available"])
            self.assertTrue(any(item["id"] == "on_startup" for item in report["on_action_hooks"]))
            self.assertTrue(any(item["idea"] == "KAZ_startup_idea"
                                for item in report["history_summaries"][0]["startup_idea_grants"]))
            self.assertTrue(any(item["variable"] == "KAZ_history_counter"
                                for item in report["history_summaries"][0]["startup_variable_initialisations"]))

            flag = next(item for item in report["flag_symbols"] if item["id"] == "KAZ_state_flag")
            self.assertGreaterEqual(flag["write_count"], 1)
            self.assertGreaterEqual(flag["read_count"], 1)

            variable = next(item for item in report["variable_symbols"] if item["id"] == "KAZ_counter")
            self.assertGreaterEqual(variable["write_count"], 1)
            self.assertGreaterEqual(variable["read_count"], 1)

            array = next(item for item in report["array_symbols"] if item["id"] == "KAZ_registry")
            self.assertGreaterEqual(array["write_count"], 1)
            self.assertGreaterEqual(array["read_count"], 1)

            self.assertTrue(any(item["scripted_effect"] == "KAZ_apply_state"
                                for item in report["scripted_effect_calls"]))
            self.assertTrue(any(item["scripted_effect"] == "KAZ_extensionless_effect"
                                for item in report["scripted_effect_calls"]))
            self.assertTrue(any(item["scripted_trigger"] == "KAZ_state_ready"
                                for item in report["scripted_trigger_calls"]))
            self.assertTrue(any(item["candidate"] == "KAZ_missing_scripted_call"
                                and item["classification"] == "local_definition_not_found_candidate"
                                for item in report["unresolved_scripted_call_candidates"]))
            self.assertTrue(any(item["candidate"] == "USA_base_trigger"
                                and item["classification"] == "external_or_unknown_dependency"
                                for item in report["unresolved_scripted_call_candidates"]))
            self.assertFalse(any(item["idea"] == "KAZ_balanced_state_idea"
                                 for item in report["idea_on_add_without_matching_on_remove"]))
            self.assertTrue(any(item["idea"] == "KAZ_one_sided_state_idea"
                                and item["id"] == "KAZ_one_sided_flag"
                                for item in report["idea_on_add_without_matching_on_remove"]))

    def test_state_flow_links_decisions_and_events_by_exact_positive_flag_and_idea_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)

            common = root / "mdredux" / "common"
            decisions = common / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "Kazakhstan.txt").write_text("""
KAZ_test_category = {
  KAZ_decision_writer = {
    complete_effect = {
      set_global_flag = KAZ_decision_gate
      add_ideas = KAZ_decision_idea
    }
  }
  KAZ_decision_reader = {
    visible = { has_global_flag = KAZ_decision_gate }
    available = { has_idea = KAZ_decision_idea }
  }
}
""", encoding="utf-8")

            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            with events.open("a", encoding="utf-8") as handle:
                handle.write("""
country_event = {
  id = kaz_test.flag_writer
  option = {
    name = kaz_test.flag_writer.a
    set_country_flag = KAZ_event_gate
    add_timed_idea = { idea = KAZ_event_idea days = 30 }
  }
}
country_event = {
  id = kaz_test.flag_reader
  trigger = {
    has_country_flag = KAZ_event_gate
    has_idea = KAZ_event_idea
  }
}
country_event = {
  id = kaz_test.negative_reader
  trigger = { NOT = { has_country_flag = KAZ_event_gate } }
}
""")

            countries, _ = audit.discover(root)
            _, _, _, event_parsed = audit.build_global_indexes(countries)
            report = audit.build_state_flow_audit(root, countries, event_parsed)
            links = report["decision_event_state_links"]
            link_keys = {
                (item["family"], item["id"], item["writer"]["object_id"], item["reader"]["object_id"])
                for item in links
            }

            self.assertIn(("flag", "KAZ_decision_gate", "KAZ_decision_writer", "KAZ_decision_reader"),
                          link_keys)
            self.assertIn(("idea", "KAZ_decision_idea", "KAZ_decision_writer", "KAZ_decision_reader"),
                          link_keys)
            self.assertIn(("flag", "KAZ_event_gate", "kaz_test.flag_writer", "kaz_test.flag_reader"),
                          link_keys)
            self.assertIn(("idea", "KAZ_event_idea", "kaz_test.flag_writer", "kaz_test.flag_reader"),
                          link_keys)
            self.assertFalse(any(item["reader"]["object_id"] == "kaz_test.negative_reader"
                                 for item in links))
            self.assertTrue(all(item["scope_match"] is True for item in links if item["family"] == "flag"))
            self.assertEqual(report["counts"]["decision_event_state_links"], len(links))


    def test_industry_audit_lists_unresolved_has_tech_references_without_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tech_dir = root / "mdredux" / "common" / "technologies"
            tech_dir.mkdir(parents=True)
            (tech_dir / "fixture.txt").write_text("""
technologies = {
    KAZ_known_technology = { research_cost = 1 }
}
""", encoding="utf-8")
            decisions = root / "mdredux" / "common" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "Kazakhstan.txt").write_text("""
KAZ_test_category = {
    KAZ_test_decision = {
        visible = { has_tech = KAZ_external_technology }
    }
}
""", encoding="utf-8")
            countries, loc_index = audit.discover(root)
            all_focus, _, _, event_parsed = audit.build_global_indexes(countries, root)
            report = audit.build_industry_audit(root, countries, loc_index, all_focus, event_parsed)
            self.assertTrue(any(
                item["technology"] == "KAZ_external_technology"
                and item["classification"] == "not_defined_in_local_technology_slice"
                for item in report["unknown_technology_references"]
            ))
            self.assertFalse(any(
                item["technology"] == "KAZ_known_technology"
                for item in report["unknown_technology_references"]
            ))


    def test_external_dependency_registry_preserves_confirmed_assumption_and_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry_dir = root / "docs" / "research"
            registry_dir.mkdir(parents=True)
            registry = {
                "schema_version": 1,
                "last_reviewed": "2026-11-24",
                "baseline": {"repository": "MillenniumDawn/Millennium-Dawn", "commit": "abc123"},
                "dependencies": [
                    {
                        "type": "event", "id": "CSTO.1", "status": "confirmed",
                        "expected_source": "Millennium Dawn base events",
                        "checked_at": "2026-11-24", "verification": [],
                        "notes": "Verified in pinned upstream snapshot."
                    },
                    {
                        "type": "equipment", "id": "CV_MR_Fighter2", "status": "assumption",
                        "expected_source": "Millennium Dawn / HOI4 equipment",
                        "checked_at": "2026-11-24", "verification": [],
                        "notes": "Upstream usage seen; definition not independently verified."
                    }
                ]
            }
            (registry_dir / "external-dependencies.json").write_text(
                __import__("json").dumps(registry, ensure_ascii=False), encoding="utf-8"
            )
            event_report = {
                "external_references": [
                    {"target": "CSTO.1", "source": "mdredux/common/national_focus/Poland_Focus_Tree.txt",
                     "line": 10, "source_kind": "focus", "caller": "POL_test"},
                    {"target": "NOT_IN_REGISTRY.9", "source": "mdredux/events/Georgia.txt",
                     "line": 20, "source_kind": "event", "caller": "geo_test"}
                ],
                "external_localisation": [
                    {"key": "CSTO.1.t", "path": "mdredux/events/Georgia.txt",
                     "line": 21, "event_id": "geo_test", "field": "title"}
                ],
                "external_option_localisation": [],
                "missing_event_idea_candidates": []
            }
            decision_report = {
                "external_tooltip_localisation": [], "external_event_references": [],
                "external_focus_references": [], "external_decision_references": []
            }
            idea_report = {
                "external_idea_references": [
                    {"idea": "CSTO_member", "path": "mdredux/common/national_focus/Russia_Focus_Tree.txt",
                     "line": 30, "usage": "condition"}
                ],
                "unresolved_unprefixed_idea_references": []
            }
            industry_report = {
                "external_mio_references": [], "missing_local_mio_references": [],
                "external_mio_name_localisation_candidates": [],
                "unknown_equipment_type_references": [
                    {"type": "CV_MR_Fighter2", "path": "mdredux/events/Georgia.txt",
                     "line": 40, "action": "add_equipment_to_stockpile"}
                ],
                "unknown_module_references": [],
                "unknown_technology_references": [
                    {"technology": "KAZ_unknown_tech", "path": "mdredux/common/decisions/Kazakhstan.txt",
                     "line": 50, "command": "has_tech"}
                ]
            }
            state_flow_report = {
                "unresolved_scripted_call_candidates": [
                    {"candidate": "CSTO_join", "path": "mdredux/events/Georgia.txt", "line": 60,
                     "classification": "external_or_unknown_dependency"}
                ]
            }
            report = audit.build_external_dependency_audit(
                root, event_report, decision_report, idea_report, industry_report, state_flow_report
            )
            by_key = {(item["type"], item["id"]): item for item in report["findings"]}
            self.assertEqual(by_key[("event", "CSTO.1")]["status"], "confirmed")
            self.assertEqual(by_key[("event", "CSTO.1")]["registry_status"], "registered")
            self.assertEqual(by_key[("event", "NOT_IN_REGISTRY.9")]["status"], "unknown")
            self.assertEqual(by_key[("event", "NOT_IN_REGISTRY.9")]["registry_status"], "unregistered")
            self.assertEqual(by_key[("equipment", "CV_MR_Fighter2")]["status"], "assumption")
            self.assertEqual(by_key[("idea", "CSTO_member")]["status"], "unknown")
            self.assertEqual(by_key[("technology", "KAZ_unknown_tech")]["status"], "unknown")
            self.assertEqual(by_key[("scripted_effect_or_trigger", "CSTO_join")]["status"], "unknown")
            self.assertEqual(report["counts"]["unregistered"], 5)
            self.assertTrue(report["registry_available"])


    def test_confirmed_external_event_localisation_resolves_only_exact_event_keys(self):
        event_report = {
            "missing_localisation": [
                {"field": "desc", "key": "sov_nationalists.20.d", "event_id": "sov_nationalists.20",
                 "path": "mdredux/events/Russia.txt", "line": 10}
            ],
            "missing_option_localisation": [
                {"key": "israel_economy.38.b", "event_id": "israel_economy.38",
                 "path": "mdredux/events/Israel.txt", "line": 20},
                {"key": "israel_missing.1.a", "event_id": "israel_missing.1",
                 "path": "mdredux/events/Israel.txt", "line": 30}
            ]
        }
        dependency_report = {
            "findings": [
                {
                    "type": "localisation", "id": "sov_nationalists.20.d", "status": "confirmed",
                    "references": [{"repository": "TDF", "path": "mdredux/events/Russia.txt"}]
                },
                {
                    "type": "localisation", "id": "israel_economy.38.b", "status": "confirmed",
                    "references": [{"repository": "TDF", "path": "mdredux/events/Israel.txt"}]
                },
                {
                    "type": "localisation", "id": "israel_missing.1.a", "status": "unknown",
                    "references": [{"repository": "TDF", "path": "mdredux/events/Israel.txt"}]
                },
                {
                    "type": "localisation", "id": "focus_only_desc", "status": "confirmed",
                    "references": [{"repository": "TDF", "path": "mdredux/common/national_focus/Russia_Focus_Tree.txt"}]
                }
            ]
        }
        audit.classify_confirmed_external_event_localisation(event_report, dependency_report)
        self.assertEqual(event_report["missing_localisation"], [])
        self.assertEqual(
            [item["key"] for item in event_report["missing_option_localisation"]],
            ["israel_missing.1.a"]
        )
        self.assertEqual(
            [item["key"] for item in event_report["confirmed_external_localisation"]],
            ["sov_nationalists.20.d", "israel_economy.38.b"]
        )
        self.assertNotIn("confirmed_external_localisation", audit.ERRORS)

    def test_confirmed_external_focus_localisation_resolves_only_exact_focus_keys(self):
        results = {
            "ENG": {
                "title_missing": ["ENG_title_from_base", "ENG_title_unknown"],
                "desc_missing": ["ENG_desc_from_base", "ENG_desc_assumption"],
            },
            "GEO": {
                "title_missing": [],
                "desc_missing": ["GEO_desc_from_event_only"],
            },
        }
        dependency_report = {
            "findings": [
                {
                    "type": "localisation", "id": "ENG_title_from_base", "status": "confirmed",
                    "references": [{"repository": "TDF", "path": "mdredux/common/national_focus/United Kingdom_Focus_Tree.txt"}]
                },
                {
                    "type": "localisation", "id": "ENG_desc_from_base_desc", "status": "confirmed",
                    "references": [{"repository": "TDF", "path": "mdredux/common/national_focus/United Kingdom_Focus_Tree.txt"}]
                },
                {
                    "type": "localisation", "id": "ENG_title_unknown", "status": "unknown",
                    "references": [{"repository": "TDF", "path": "mdredux/common/national_focus/United Kingdom_Focus_Tree.txt"}]
                },
                {
                    "type": "localisation", "id": "ENG_desc_assumption_desc", "status": "assumption",
                    "references": [{"repository": "TDF", "path": "mdredux/common/national_focus/United Kingdom_Focus_Tree.txt"}]
                },
                {
                    "type": "localisation", "id": "GEO_desc_from_event_only_desc", "status": "confirmed",
                    "references": [{"repository": "TDF", "path": "mdredux/events/Georgia.txt"}]
                }
            ]
        }
        audit.classify_confirmed_external_focus_localisation(results, dependency_report)
        self.assertEqual(results["ENG"]["title_missing"], ["ENG_title_unknown"])
        self.assertEqual(results["ENG"]["desc_missing"], ["ENG_desc_assumption"])
        self.assertEqual(results["GEO"]["desc_missing"], ["GEO_desc_from_event_only"])
        self.assertEqual(
            [item["key"] for item in results["ENG"]["confirmed_external_localisation"]],
            ["ENG_title_from_base", "ENG_desc_from_base_desc"]
        )
        self.assertNotIn("confirmed_external_localisation", audit.ERRORS)

    def test_confirmed_external_events_resolve_only_exact_local_namespace_gaps(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry_dir = root / "docs" / "research"
            registry_dir.mkdir(parents=True)
            registry = {
                "schema_version": 1,
                "last_reviewed": "2026-11-25",
                "baseline": {
                    "repository": "MillenniumDawn/Millennium-Dawn",
                    "commit": "04b2ba126fc1057bf2ab4bac0407b3235983994c"
                },
                "dependencies": [
                    {
                        "type": "event", "id": "arm_foreign_legion.3", "status": "confirmed",
                        "expected_source": "Millennium Dawn pinned base event definition",
                        "checked_at": "2026-11-25",
                        "verification": [{"kind": "event definition", "path": "events/05_armenia.txt", "line": 12532}],
                        "notes": "Exact event definition verified in the pinned base snapshot."
                    },
                    {
                        "type": "event", "id": "russia.3", "status": "unknown",
                        "expected_source": "Millennium Dawn Russia events",
                        "checked_at": "2026-11-25", "verification": [],
                        "notes": "Not verified in the pinned baseline."
                    },
                    {
                        "type": "event", "id": "syria_bashar.8", "status": "assumption",
                        "expected_source": "Millennium Dawn Syria events",
                        "checked_at": "2026-11-25", "verification": [],
                        "notes": "Usage only; definition not verified."
                    }
                ]
            }
            (registry_dir / "external-dependencies.json").write_text(
                __import__("json").dumps(registry, ensure_ascii=False), encoding="utf-8"
            )
            event_report = {
                "external_references": [],
                "unresolved_references": [
                    {"kind": "country_event", "target": "arm_foreign_legion.3",
                     "source": "mdredux/events/Armenia.txt", "line": 10, "source_kind": "event"},
                    {"kind": "country_event", "target": "russia.3",
                     "source": "mdredux/events/Russia.txt", "line": 20, "source_kind": "event"},
                    {"kind": "news_event", "target": "syria_bashar.8",
                     "source": "mdredux/events/Syria.txt", "line": 30, "source_kind": "event"},
                    {"kind": "country_event", "target": "not_registered.1",
                     "source": "mdredux/events/Georgia.txt", "line": 40, "source_kind": "event"}
                ],
                "external_localisation": [], "external_option_localisation": [],
                "missing_event_idea_candidates": []
            }
            decision_report = {
                "external_tooltip_localisation": [], "external_event_references": [],
                "external_focus_references": [], "external_decision_references": []
            }
            idea_report = {"external_idea_references": [], "unresolved_unprefixed_idea_references": []}
            industry_report = {
                "external_mio_references": [], "missing_local_mio_references": [],
                "external_mio_name_localisation_candidates": [],
                "unknown_equipment_type_references": [], "unknown_module_references": [],
                "unknown_technology_references": []
            }
            state_flow_report = {"unresolved_scripted_call_candidates": []}

            dependency_report = audit.build_external_dependency_audit(
                root, event_report, decision_report, idea_report, industry_report, state_flow_report
            )
            by_key = {(item["type"], item["id"]): item for item in dependency_report["findings"]}
            self.assertEqual(by_key[("event", "arm_foreign_legion.3")]["status"], "confirmed")
            self.assertEqual(by_key[("event", "russia.3")]["status"], "unknown")
            self.assertEqual(by_key[("event", "syria_bashar.8")]["status"], "assumption")
            self.assertEqual(by_key[("event", "not_registered.1")]["registry_status"], "unregistered")

            audit.classify_confirmed_external_event_references(event_report, dependency_report)
            self.assertEqual(
                [item["target"] for item in event_report["confirmed_external_references"]],
                ["arm_foreign_legion.3"]
            )
            self.assertEqual(
                [item["target"] for item in event_report["unresolved_references"]],
                ["russia.3", "syria_bashar.8", "not_registered.1"]
            )
            self.assertNotIn("confirmed_external_references", audit.ERRORS)


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



    def test_branch_connectivity_links_focus_event_idea_tooltip_and_next_focus(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            tree.write_text("""
focus_tree = {
  country = { original_tag = KAZ }
  focus = {
    id = KAZ_flow_root
    completion_reward = {
      log = "[GetDateText]: [Root.GetName]: Focus KAZ_flow_root"
      country_event = { id = kaz_flow.1 days = 1 }
      show_ideas_tooltip = KAZ_flow_spirit
    }
  }
  focus = {
    id = KAZ_flow_next
    prerequisite = { focus = KAZ_flow_root }
    available = { has_idea = KAZ_flow_spirit_2 }
    completion_reward = { log = "[GetDateText]: [Root.GetName]: Focus KAZ_flow_next" }
  }
  focus = {
    id = KAZ_flow_negative_gate
    prerequisite = { focus = KAZ_flow_root }
    available = { NOT = { has_idea = KAZ_flow_spirit_2 } }
    bypass = { has_idea = KAZ_never_used_for_access }
    completion_reward = { log = "[GetDateText]: [Root.GetName]: Focus KAZ_flow_negative_gate" }
  }
}
""", encoding="utf-8")

            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_flow
country_event = {
  id = kaz_flow.1
  title = kaz_flow.1.t
  desc = kaz_flow.1.d
  is_triggered_only = yes
  option = {
    name = kaz_flow.1.a
    log = "[GetDateText]: [This.GetName]: kaz_flow.1.a"
    country_event = kaz_flow.2
  }
}
country_event = {
  id = kaz_flow.2
  title = kaz_flow.2.t
  desc = kaz_flow.2.d
  is_triggered_only = yes
  option = {
    name = kaz_flow.2.a
    log = "[GetDateText]: [This.GetName]: kaz_flow.2.a"
    add_ideas = KAZ_flow_spirit_2
  }
}
country_event = {
  id = kaz_flow.3
  title = kaz_flow.3.t
  desc = kaz_flow.3.d
  is_triggered_only = yes
  option = { name = kaz_flow.3.a }
}
country_event = {
  id = kaz_flow.4
  title = kaz_flow.4.t
  desc = kaz_flow.4.d
  is_triggered_only = yes
  option = { name = kaz_flow.4.a }
}
""", encoding="utf-8")

            ideas = root / "mdredux" / "common" / "ideas" / "Kazakhstan_ideas.txt"
            ideas.write_text("""
ideas = {
  country = {
    KAZ_flow_spirit = {
      name = KAZ_flow_spirit
      custom_modifier_tooltip = KAZ_flow_spirit_tt
    }
    KAZ_flow_spirit_2 = {
      name = KAZ_flow_spirit
      on_remove = {
        country_event = { id = kaz_flow.3 days = 1 }
      }
    }
    KAZ_flow_ungranted_spirit = {
      name = KAZ_flow_ungranted_spirit
      on_add = {
        country_event = { id = kaz_flow.4 days = 1 }
      }
    }
  }
}
""", encoding="utf-8")

            scripted = root / "mdredux" / "common" / "scripted_localisation"
            (scripted / "99_KAZ_scripted_localisation.txt").write_text("""
defined_text = {
  name = KAZ_flow_spirit_stage
  text = {
    trigger = { has_idea = KAZ_flow_spirit_2 }
    localization_key = KAZ_flow_spirit_stage_desc
  }
}
""", encoding="utf-8")

            mio_dir = root / "mdredux" / "common" / "military_industrial_organization" / "organizations"
            mio_dir.mkdir(parents=True)
            (mio_dir / "KAZ_mio.txt").write_text("""
KAZ_flow_mio = {
  allowed = { original_tag = KAZ }
  visible = { has_completed_focus = KAZ_flow_root }
  name = KAZ_flow_mio_name
  include = generic_tank_equipment_organization
}
""", encoding="utf-8")

            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_flow.1.t:0 "Offer"
 kaz_flow.1.d:0 "The offer is presented."
 kaz_flow.1.a:0 "Continue"
 kaz_flow.2.t:0 "Delivery"
 kaz_flow.2.d:0 "The delivery is arranged."
 kaz_flow.2.a:0 "Accept"
 kaz_flow.3.t:0 "Idea removal"
 kaz_flow.3.d:0 "The granted idea was removed."
 kaz_flow.3.a:0 "Continue"
 kaz_flow.4.t:0 "Unreached idea"
 kaz_flow.4.d:0 "This idea has no local grant."
 kaz_flow.4.a:0 "Continue"
 KAZ_flow_root:0 "Root"
 KAZ_flow_root_desc:0 "A sufficiently long description used by a branch connectivity fixture."
 KAZ_flow_next:0 "Next"
 KAZ_flow_next_desc:0 "A sufficiently long description used by a branch connectivity fixture."
 KAZ_flow_spirit:0 "First stage"
 KAZ_flow_ungranted_spirit:0 "Unreached stage"
 KAZ_flow_spirit_tt:0 "Current stage: [KAZ_flow_spirit_stage]"
 KAZ_flow_spirit_stage_desc:0 "The upgraded stage is active."
 KAZ_flow_mio_name:0 "Kazakhstan test organization"
""", encoding="utf-8")

            countries, loc_index = audit.discover(root)
            _, _, _, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            idea_report = audit.build_idea_lifecycle_audit(root, countries, loc_index, content, event_parsed)
            event_report = audit.build_event_audit(
                root, countries, loc_index, event_parsed, content, idea_report
            )
            all_focus = {
                audit.get_scalar(body, "id")
                for body in audit.find_named_blocks(countries["KAZ"]["tree_parsed"].root, "focus")
                if audit.get_scalar(body, "id")
            }
            industry_report = audit.build_industry_audit(root, countries, loc_index, all_focus, event_parsed)
            state_report = audit.build_state_flow_audit(root, countries, event_parsed)
            report = audit.build_branch_connectivity_audit(
                countries, event_report, idea_report, industry_report, state_report,
                event_parsed, content, loc_index, tags=["KAZ"],
            )
            flow = report["by_country"]["KAZ"]

            self.assertTrue(any(
                edge["from"] == "KAZ_flow_root" and edge["to"] == "kaz_flow.1"
                for edge in flow["focus_event_edges"]
            ))
            self.assertTrue(any(
                edge["from"] == "kaz_flow.1" and edge["to"] == "kaz_flow.2"
                for edge in flow["event_event_edges"]
            ))
            self.assertTrue(any(
                edge["from"] == "kaz_flow.2" and edge["to"] == "KAZ_flow_spirit_2"
                for edge in flow["event_idea_grant_edges"]
            ))
            self.assertTrue(any(
                edge["from"] == "KAZ_flow_spirit_2" and edge["to"] == "kaz_flow.3"
                and edge["lifecycle"] == "on_remove"
                for edge in flow["idea_event_edges"]
            ))
            self.assertTrue(any(
                edge["from"] == "KAZ_flow_ungranted_spirit" and edge["to"] == "kaz_flow.4"
                for edge in flow["idea_event_edges"]
            ))
            self.assertIn("kaz_flow.3", event_report["idea_event_roots"])
            self.assertFalse(any(
                item["id"] == "kaz_flow.3"
                for item in event_report["unreachable_triggered_events"]
            ))
            self.assertTrue(any(
                item["id"] == "kaz_flow.4"
                for item in event_report["unreachable_triggered_events"]
            ))
            self.assertTrue(any(
                item["id"] == "kaz_flow.4"
                for item in flow["review_candidates"]["unreachable_triggered_events"]
            ))
            tooltip_relations = {edge["relation"] for edge in flow["idea_tooltip_edges"]}
            self.assertIn("custom_modifier_tooltip", tooltip_relations)
            self.assertIn("localisation_calls_scripted_localisation", tooltip_relations)
            self.assertIn("scripted_localisation_checks_idea", tooltip_relations)
            self.assertTrue(any(
                edge["from"] == "KAZ_flow_mio" and edge["to"] == "KAZ_flow_root"
                for edge in flow["mio_visibility_edges"]
            ))
            gate = next(edge for edge in flow["focus_idea_gate_edges"]
                        if edge["from"] == "KAZ_flow_next" and edge["to"] == "KAZ_flow_spirit_2")
            self.assertEqual(gate["path_status"], "local_upstream_grant_found")
            self.assertFalse(flow["review_candidates"]["focus_idea_gate_paths"])
            self.assertFalse(any(
                item["focus"] == "KAZ_flow_negative_gate"
                for item in flow["review_candidates"]["focus_idea_gate_paths"]
            ))
            self.assertTrue(any(
                edge["from"] == "KAZ_flow_negative_gate" and edge["gate"] == "bypass"
                for edge in flow["focus_idea_gate_edges"]
            ))
            self.assertFalse(flow["review_candidates"]["tooltip_script_resolution"])

    def test_branch_connectivity_separates_local_gaps_from_external_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            tree = root / "mdredux" / "common" / "national_focus" / "Kazakhstan_Focus_Tree.txt"
            tree.write_text("""
focus_tree = {
  country = { original_tag = KAZ }
  focus = {
    id = KAZ_flow_root
    available = { has_idea = KAZ_orphan_spirit }
    completion_reward = {
      log = "[GetDateText]: [Root.GetName]: Focus KAZ_flow_root"
      country_event = kaz_flow.404
      country_event = base_md_event.1
    }
  }
}
""", encoding="utf-8")
            events = root / "mdredux" / "events" / "Kazakhstan.txt"
            events.write_text("""
add_namespace = kaz_flow
country_event = {
  id = kaz_flow.1
  title = kaz_flow.1.t
  desc = kaz_flow.1.d
}
""", encoding="utf-8")
            ideas = root / "mdredux" / "common" / "ideas" / "Kazakhstan_ideas.txt"
            ideas.write_text("""
ideas = {
  country = {
    KAZ_orphan_spirit = {
      name = KAZ_orphan_spirit
      custom_modifier_tooltip = KAZ_orphan_tooltip
    }
  }
}
""", encoding="utf-8")
            loc = root / "mdredux" / "localisation" / "english" / "kazakhstan_a_l_english.yml"
            loc.write_text("""l_english:
 kaz_flow.1.t:0 "Event"
 kaz_flow.1.d:0 "A description."
 KAZ_flow_root:0 "Root"
 KAZ_flow_root_desc:0 "A sufficiently long description used by a branch connectivity fixture."
 KAZ_orphan_spirit:0 "Orphan"
 KAZ_orphan_tooltip:0 "An unfinished tooltip: [KAZ_missing_script]"
""", encoding="utf-8")

            countries, loc_index = audit.discover(root)
            _, _, _, event_parsed = audit.build_global_indexes(countries, root)
            content = audit.build_content_indexes(root, countries, loc_index)
            idea_report = audit.build_idea_lifecycle_audit(root, countries, loc_index, content, event_parsed)
            event_report = audit.build_event_audit(
                root, countries, loc_index, event_parsed, content, idea_report
            )
            all_focus = {
                audit.get_scalar(body, "id")
                for body in audit.find_named_blocks(countries["KAZ"]["tree_parsed"].root, "focus")
                if audit.get_scalar(body, "id")
            }
            industry_report = audit.build_industry_audit(root, countries, loc_index, all_focus, event_parsed)
            state_report = audit.build_state_flow_audit(root, countries, event_parsed)
            report = audit.build_branch_connectivity_audit(
                countries, event_report, idea_report, industry_report, state_report,
                event_parsed, content, loc_index, tags=["KAZ"],
            )
            candidates = report["by_country"]["KAZ"]["review_candidates"]

            self.assertTrue(any(
                item["to"] == "kaz_flow.404" and item["status"] == "missing_in_declared_local_namespace"
                for item in candidates["unresolved_local_event_calls"]
            ))
            self.assertTrue(any(
                item["to"] == "base_md_event.1" and item["status"] == "external_or_unknown_namespace"
                for item in candidates["external_event_calls"]
            ))
            self.assertTrue(any(
                item["focus"] == "KAZ_flow_root" and item["idea"] == "KAZ_orphan_spirit"
                for item in candidates["focus_idea_gate_paths"]
            ))
            self.assertTrue(any(
                item["scripted_localisation"] == "KAZ_missing_script"
                for item in candidates["tooltip_script_resolution"]
            ))


class DocumentationPolicyTests(unittest.TestCase):
    def test_editorial_heuristics_remain_warnings_or_info(self):
        editorial_warnings = (
            "title_gt30", "desc_lt150", "desc_gt340", "banned_phrase",
            "event_generic_label", "event_label_gt35",
        )
        for key in editorial_warnings:
            with self.subTest(key=key):
                self.assertIn(key, audit.WARNS)
                self.assertNotIn(key, audit.ERRORS)
        self.assertIn("event_without_picture", audit.INFOS)
        self.assertNotIn("event_without_picture", audit.ERRORS)

    def test_reference_index_local_links_resolve(self):
        repo_root = Path(__file__).parents[3]
        index_path = repo_root / "skills" / "tdf-country-content" / "references" / "README.md"
        self.assertTrue(index_path.is_file(), "Missing canonical reference index")
        content = index_path.read_text(encoding="utf-8")
        targets = re.findall(r"\]\(([^)]+)\)", content)
        broken = []
        from urllib.parse import unquote
        for target in targets:
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (index_path.parent / unquote(target)).resolve()
            if not resolved.exists():
                broken.append(target)
        self.assertEqual(broken, [], "Broken local links in reference index")

if __name__ == "__main__":
    unittest.main()


