import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tdf_audit as base  # noqa: E402  (модуль, а не класс: тесты не собираются повторно)

BASELINE_SCRIPT = Path(__file__).parents[1] / "scripts" / "tdf_baseline.py"
SPEC = importlib.util.spec_from_file_location("tdf_baseline", BASELINE_SCRIPT)
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


class FingerprintTests(unittest.TestCase):
    def test_embedded_line_number_in_string_is_removed(self):
        self.assertEqual(
            baseline.fingerprint("a/b.txt:297: блок '{' не закрыт"),
            baseline.fingerprint("a/b.txt:301: блок '{' не закрыт"),
        )

    def test_plain_ids_are_untouched(self):
        self.assertEqual(baseline.fingerprint("britain_boris.13.a"), "britain_boris.13.a")

    def test_pairs_are_joined_in_order(self):
        self.assertEqual(baseline.fingerprint(["ARM_a", "ARM_b"]), "ARM_a | ARM_b")
        self.assertNotEqual(baseline.fingerprint(["ARM_a", "ARM_b"]), baseline.fingerprint(["ARM_b", "ARM_a"]))

    def test_dict_ignores_line_numbers_and_key_order(self):
        one = {"key": "k", "path": "p.txt", "line": 10, "event_id": "e"}
        two = {"event_id": "e", "line": 999, "path": "p.txt", "key": "k"}
        self.assertEqual(baseline.fingerprint(one), baseline.fingerprint(two))
        self.assertNotEqual(baseline.fingerprint(one), baseline.fingerprint({**one, "key": "other"}))


class ExtractTests(unittest.TestCase):
    def test_only_error_checks_per_tag_are_collected(self):
        report = {"ARM": {"desc_missing": ["ARM_x"], "desc_lt150": ["ARM_y"], "n_focus": 5}}
        self.assertEqual(baseline.extract_findings(report), {"ARM/desc_missing": ["ARM_x"]})

    def test_global_sections_are_collected(self):
        report = {
            "_events": {"options_without_log": [{"key": "a.1.a", "line": 5}]},
            "_decisions": {
                "missing_decision_localisation": [{"decision": "d", "line": 1}],
                "duplicate_category_ids": [{"scope": "same_file", "id": "c1"}, {"scope": "cross_file", "id": "c2"}],
            },
            "_ideas": {"source_parse_errors": ["f.txt:3: блок '{' не закрыт"]},
        }
        found = baseline.extract_findings(report)
        self.assertIn("_events/options_without_log", found)
        self.assertIn("_decisions/missing_decision_localisation", found)
        self.assertEqual(len(found["_decisions/duplicate_category_ids"]), 1)
        self.assertEqual(found["_ideas/source_parse_errors"], ["f.txt: блок '{' не закрыт"])

    def test_registry_issues_count_only_when_registry_is_available(self):
        issues = ["bad entry"]
        self.assertEqual(baseline.extract_findings(
            {"_external_dependencies": {"registry_available": False, "registry_validation_issues": issues}}), {})
        self.assertEqual(baseline.extract_findings(
            {"_external_dependencies": {"registry_available": True, "registry_validation_issues": issues}}),
            {"_external_dependencies/registry_validation_issues": issues})

    def test_check_lists_stay_in_sync_with_the_auditor(self):
        self.assertEqual(tuple(base.audit.ERRORS), baseline.TAG_ERROR_CHECKS)
        self.assertEqual(tuple(base.audit.PARSE_ERROR_FIELDS), baseline.PARSE_ERROR_FIELDS)


class CompareTests(unittest.TestCase):
    BASE = {"ARM/desc_missing": ["ARM_a", "ARM_b"], "KAZ/no_log": ["KAZ_c"]}

    def test_identical_state_has_no_new_or_fixed(self):
        new, fixed = baseline.compare(self.BASE, self.BASE)
        self.assertEqual((new, fixed), (set(), set()))

    def test_new_finding_is_reported_even_if_count_is_unchanged(self):
        current = {"ARM/desc_missing": ["ARM_a", "ARM_z"], "KAZ/no_log": ["KAZ_c"]}
        new, fixed = baseline.compare(self.BASE, current)
        self.assertEqual(new, {("ARM/desc_missing", "ARM_z")})
        self.assertEqual(fixed, {("ARM/desc_missing", "ARM_b")})

    def test_strict_tag_treats_known_findings_as_violations(self):
        new, _ = baseline.compare(self.BASE, self.BASE, strict_tags=["kaz"])
        self.assertEqual(new, {("KAZ/no_log", "KAZ_c")})

    def test_render_summarizes_and_truncates(self):
        current = {"ARM/desc_missing": ["ARM_%d" % i for i in range(8)]}
        new, fixed = baseline.compare({}, current)
        text = baseline.render({}, current, new, fixed, max_samples=3)
        self.assertIn("РЕГРЕССИЯ", text)
        self.assertIn("(+8)", text)
        self.assertIn("(+5 ещё)", text)

    def test_render_ok_and_fixed_hint(self):
        new, fixed = baseline.compare(self.BASE, {"KAZ/no_log": ["KAZ_c"]})
        text = baseline.render(self.BASE, {"KAZ/no_log": ["KAZ_c"]}, new, fixed)
        self.assertIn("OK: новых находок нет", text)
        self.assertIn("Исправлено 2", text)


class CliTests(unittest.TestCase):
    helper = base.RepositoryAuditTests("make_repo")

    def run_cmd(self, *args):
        return subprocess.run(
            [sys.executable, "-I", str(BASELINE_SCRIPT), *args],
            universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )

    def audit_json(self, root: Path, out: Path) -> int:
        proc = subprocess.run(
            [sys.executable, "-I", str(base.SCRIPT), str(root), "--json", str(out)],
            universal_newlines=True, encoding="utf-8", stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, check=False,
        )
        return proc.returncode

    def test_findings_exist_exactly_when_the_auditor_exits_with_errors(self):
        for builder, expected_exit in (("make_repo", 1), ("make_clean_cli_fixture", 0)):
            with self.subTest(fixture=builder), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "repo"
                getattr(self.helper, builder)(root)
                out = Path(temp) / "audit.json"
                self.assertEqual(self.audit_json(root, out), expected_exit)
                found = baseline.extract_findings(json.loads(out.read_text(encoding="utf-8")))
                self.assertEqual(bool(found), expected_exit == 1)

    def test_update_then_check_roundtrip_and_regression_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            self.helper.make_repo(root)
            out = Path(temp) / "audit.json"
            self.audit_json(root, out)
            bl = Path(temp) / "baseline.json"
            self.assertEqual(self.run_cmd("update", "--report", str(out), "--baseline", str(bl)).returncode, 0)
            ok = self.run_cmd("check", "--report", str(out), "--baseline", str(bl))
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("Новых: 0", ok.stdout)

            report = json.loads(out.read_text(encoding="utf-8"))
            report["KAZ"]["desc_missing"] = list(report["KAZ"].get("desc_missing", [])) + ["KAZ_brand_new"]
            out.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            bad = self.run_cmd("check", "--report", str(out), "--baseline", str(bl))
            self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
            self.assertIn("KAZ_brand_new", bad.stdout)

    def test_check_runs_the_auditor_itself_when_no_report_is_given(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            self.helper.make_clean_cli_fixture(root)
            bl = Path(temp) / "baseline.json"
            common = ["--repo", str(root), "--baseline", str(bl), "--no-require-registry"]
            self.assertEqual(self.run_cmd("update", *common).returncode, 0)
            result = self.run_cmd("check", *common)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertLess(len(result.stdout.splitlines()), 6)

    def test_missing_baseline_is_an_input_error(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "audit.json"
            out.write_text("{}", encoding="utf-8")
            result = self.run_cmd("check", "--report", str(out), "--baseline", str(Path(temp) / "nope.json"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("update", result.stderr)

    def test_baseline_file_has_no_absolute_paths_or_positions(self):
        with tempfile.TemporaryDirectory() as temp:
            bl = Path(temp) / "b.json"
            baseline.write_baseline(bl, {"_events/options_without_log": [baseline.fingerprint(
                {"key": "a.1.a", "path": "mdredux/events/A.txt", "line": 12})]})
            text = bl.read_text(encoding="utf-8")
            self.assertNotIn('"line"', text)
            self.assertEqual(json.loads(text)["counts"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
