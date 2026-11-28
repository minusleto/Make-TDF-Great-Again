import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tdf_audit as base  # noqa: E402  (модуль, а не класс: тесты не собираются повторно)

SCRIPT = Path(__file__).parents[1] / "scripts" / "tdf_registry_import.py"
SPEC = importlib.util.spec_from_file_location("tdf_registry_import", SCRIPT)
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)

LABEL = "TEST-BUILD 1.0 (commit abc1234)"
DATE = "2026-11-28"

FILES = {
    "events/Test.txt": "add_namespace = tst\ncountry_event = {\n\tid = tst.1\n\ttitle = tst.1.t\n}\n"
                       "news_event = { id = tst.2 }\nnot_a_definition = { id = tst.99 }\n",
    "common/ideas/groups.txt": "ideas = {\n\tcountry = {\n\t\tTST_idea_a = { picture = x }\n\t}\n"
                               "\thidden_ideas = {\n\t\tTST_hidden = { }\n\t}\n"
                               "\tcompanies_slot = {\n\t\tTST_company_idea = { }\n\t}\n}\n",
    "common/scripted_effects/e.txt": "@const = 5\nmy_effect = { add_stability = 0.1 }\n",
    "common/scripted_triggers/t.txt": "my_trigger = { always = yes }\n",
    "common/units/equipment/eq.txt": "equipments = {\n\tmy_equipment_1 = { year = 1936 }\n}\n",
    "common/technologies/tech.txt": "technologies = {\n\tmy_tech = { }\n}\n",
    "common/military_industrial_organization/organizations/mio.txt": "TST_mio = {\n\tallowed = { always = yes }\n}\n",
    "localisation/english/x_l_english.yml": "\ufeffl_english:\n tst.1.t:0 \"Title\"\n tst_key:0 \"Value\"\n",
    "localisation/german/x_l_german.yml": "\ufeffl_german:\n de_only:0 \"Nur deutsch\"\n",
    "gfx/ignored.txt": "country_event = { id = tst.ignored }\n",
}


def write_target(root: Path, prefix: str = "") -> Path:
    for relative, content in FILES.items():
        path = root / prefix / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return root


def finding(dep_type, dep_id, status="unknown", refs=None):
    return {"type": dep_type, "id": dep_id, "status": status, "registry_status": "unregistered",
            "references": refs if refs is not None else [{"path": "mdredux/events/A.txt", "line": 7, "source_kind": "focus"}]}


def registry(dependencies=None):
    return {"schema_version": 1, "last_reviewed": "2026-11-26", "status_definitions": {},
            "dependencies": dependencies or [], "project_scope": {"repository": "o/r"}}


class ClassifyTests(unittest.TestCase):
    def test_kinds_by_path(self):
        cases = {
            "events/a.txt": "event", "mod/events/a.txt": "event", "common/ideas/a.txt": "idea",
            "common/scripted_effects/a.txt": "scripted_effect", "common/scripted_triggers/a.txt": "scripted_trigger",
            "common/units/equipment/a.txt": "equipment", "common/technologies/a.txt": "technology",
            "common/military_industrial_organization/organizations/a.txt": "mio",
            "localisation/english/a_l_english.yml": "localisation", "localisation/a_l_english.yml": "localisation",
            "Common\\Ideas\\a.txt": "idea",
        }
        for path, kind in cases.items():
            self.assertEqual(tool.classify_path(path), kind, path)

    def test_uninteresting_files(self):
        for path in ("gfx/a.txt", "localisation/german/a_l_german.yml", "events/readme.md", "common/ideas/a.yml"):
            self.assertIsNone(tool.classify_path(path), path)


class ScanTests(unittest.TestCase):
    def scan(self, prefix=""):
        with tempfile.TemporaryDirectory() as temp:
            write_target(Path(temp), prefix)
            index, files, unreadable = tool.scan_target(Path(temp) / prefix if prefix else Path(temp))
            return {k: [(e.path, e.line) for e in v] for k, v in index.items()}, files, unreadable

    def test_finds_every_kind_with_path_and_line(self):
        found, files, unreadable = self.scan()
        self.assertEqual(unreadable, 0)
        self.assertEqual(found[("event", "tst.1")], [("events/Test.txt", 3)])
        self.assertEqual(found[("event", "tst.2")], [("events/Test.txt", 6)])
        self.assertEqual(found[("idea", "TST_idea_a")], [("common/ideas/groups.txt", 3)])
        self.assertIn(("idea", "TST_hidden"), found)
        self.assertEqual(found[("idea", "TST_company_idea")], [("common/ideas/groups.txt", 9)])
        self.assertEqual(found[("scripted_effect", "my_effect")], [("common/scripted_effects/e.txt", 2)])
        self.assertEqual(found[("scripted_trigger", "my_trigger")][0][0], "common/scripted_triggers/t.txt")
        self.assertEqual(found[("equipment", "my_equipment_1")][0][1], 2)
        self.assertEqual(found[("technology", "my_tech")][0][1], 2)
        self.assertEqual(found[("mio", "TST_mio")], [("common/military_industrial_organization/organizations/mio.txt", 1)])
        self.assertEqual(found[("localisation", "tst_key")], [("localisation/english/x_l_english.yml", 3)])
        self.assertEqual(files["event"], 1)

    def test_ignores_what_is_not_a_definition(self):
        found, _, _ = self.scan()
        for key in (("event", "tst.99"), ("event", "tst.ignored"), ("scripted_effect", "@const"),
                    ("localisation", "de_only"), ("localisation", "l_english")):
            self.assertNotIn(key, found)

    def test_target_may_be_the_parent_of_the_mod_root(self):
        found, _, _ = self.scan(prefix="mdredux")
        self.assertIn(("event", "tst.1"), found)
        self.assertEqual(found[("event", "tst.1")][0][0], "events/Test.txt")


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = write_target(Path(self.temp.name))
        self.index, _, _ = tool.scan_target(self.target)

    def plan(self, findings, reg=None):
        return tool.plan_import(findings, reg or registry(), self.index, self.target, LABEL, DATE)

    def test_found_and_not_found_are_separated(self):
        new, upgraded, not_found, skipped = self.plan([
            finding("event", "tst.1"), finding("event", "tst.absent"), finding("weird", "x")])
        self.assertEqual([e["id"] for e in new], ["tst.1"])
        self.assertEqual([f["id"] for f in not_found], ["tst.absent"])
        self.assertEqual([f["type"] for f in skipped], ["weird"])
        self.assertEqual(upgraded, [])

    def test_scripted_effect_or_trigger_matches_either_directory(self):
        new, _, not_found, _ = self.plan([finding("scripted_effect_or_trigger", "my_effect"),
                                          finding("scripted_effect_or_trigger", "my_trigger"),
                                          finding("scripted_effect", "my_trigger")])
        self.assertEqual(sorted(e["id"] for e in new), ["my_effect", "my_trigger"])
        self.assertEqual([f["id"] for f in not_found], ["my_trigger"])

    def test_new_entry_is_a_valid_user_provided_confirmation_with_evidence(self):
        new, _, _, _ = self.plan([finding("event", "tst.1")])
        entry = new[0]
        self.assertEqual((entry["status"], entry["verification_origin"]), ("confirmed", "user_provided"))
        self.assertTrue(tool.has_approved_confirmation(entry))
        evidence = entry["verification"][0]
        self.assertEqual((evidence["path"], evidence["line"], evidence["build"]), ("events/Test.txt", 3, LABEL))
        expected_hash = hashlib.sha256((self.target / "events/Test.txt").read_bytes()).hexdigest()
        self.assertEqual(evidence["sha256"], expected_hash)
        self.assertEqual(entry["where_used"][0], {"repository": "TDF", "path": "mdredux/events/A.txt", "line": 7, "usage": "focus"})
        self.assertEqual((entry["namespace"], entry["checked_at"]), ("tst", DATE))
        self.assertIn(LABEL, entry["notes"])

    def test_confirmed_findings_and_registry_confirmed_entries_are_left_alone(self):
        confirmed = {"type": "event", "id": "tst.2", "status": "confirmed", "verification_origin": "tdf_local",
                     "verification": [{"path": "mdredux/events/X.txt", "line": 1}]}
        new, upgraded, not_found, _ = self.plan([finding("event", "tst.1", status="confirmed"),
                                                 finding("event", "tst.2")], registry([confirmed]))
        self.assertEqual((new, upgraded, not_found), ([], [], []))

    def test_unknown_registry_entry_is_upgraded_in_place_keeping_its_context(self):
        old = {"type": "event", "id": "tst.1", "status": "unknown", "expected_source": "old", "checked_at": "2026-01-01",
               "where_used": [{"repository": "TDF", "path": "p", "line": 1, "usage": "u"}], "verification": [],
               "notes": "old", "namespace": "tst"}
        new, upgraded, _, _ = self.plan([finding("event", "tst.1")], registry([old]))
        self.assertEqual(new, [])
        self.assertEqual(upgraded[0]["where_used"], old["where_used"])
        self.assertEqual(upgraded[0]["status"], "confirmed")
        self.assertTrue(tool.has_approved_confirmation(upgraded[0]))
        self.assertEqual(old["status"], "unknown", "the input registry must not be mutated")

    def test_duplicate_definitions_are_all_recorded_up_to_the_limit(self):
        (self.target / "events" / "Dup.txt").write_text("country_event = { id = tst.1 }\n", encoding="utf-8")
        self.index, _, _ = tool.scan_target(self.target)
        new, _, _, _ = self.plan([finding("event", "tst.1")])
        self.assertEqual(len(new[0]["verification"]), 2)
        self.assertIn("Определений с этим ID в сборке: 2", new[0]["notes"])


class MergeTests(unittest.TestCase):
    def test_merge_is_deterministic_idempotent_and_does_not_touch_the_input(self):
        confirmed_a = {"type": "mio", "id": "B", "status": "confirmed"}
        confirmed_b = {"type": "event", "id": "A", "status": "confirmed"}
        reg = registry([{"type": "idea", "id": "keep", "status": "unknown"}])
        original = copy.deepcopy(reg)
        merged = tool.merge_registry(reg, [confirmed_a, confirmed_b], [], DATE)
        self.assertEqual(reg, original)
        self.assertEqual([d["id"] for d in merged["dependencies"]], ["keep", "A", "B"])
        self.assertEqual(merged["last_reviewed"], DATE)
        self.assertEqual(tool.merge_registry(merged, [], [], "2027-01-01"), merged)

    def test_registry_format_matches_the_files_in_the_repository(self):
        path = Path(__file__).parents[3] / "docs" / "research" / "external-dependencies.json"
        raw = path.read_text(encoding="utf-8")
        self.assertEqual(tool.dump_registry(json.loads(raw)), raw, "writer must reproduce the committed registry byte-for-byte")


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], universal_newlines=True, encoding="utf-8",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.target = write_target(root / "target")
        self.registry = root / "registry.json"
        self.registry.write_text(tool.dump_registry(registry()), encoding="utf-8")
        self.report = root / "report.json"
        self.report.write_text(json.dumps({"_external_dependencies": {"registry_available": True, "findings": [
            finding("event", "tst.1"), finding("idea", "TST_company_idea"), finding("event", "tst.absent")]}}),
            encoding="utf-8")
        self.common = ["--target-dir", str(self.target), "--build-label", LABEL, "--report", str(self.report),
                       "--registry", str(self.registry), "--date", DATE]

    def test_dry_run_reports_but_writes_nothing(self):
        before = self.registry.read_bytes()
        result = self.run_cli(*self.common)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.registry.read_bytes(), before)
        self.assertIn("ПРОБНЫЙ ПРОГОН", result.stdout)
        self.assertIn("новых записей 2", result.stdout)
        self.assertIn("Не найдено: 1", result.stdout)

    def test_write_updates_the_registry_and_a_second_run_is_a_noop(self):
        notfound = Path(self.temp.name) / "nf.json"
        result = self.run_cli(*self.common, "--write", "--not-found-report", str(notfound))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(sorted(d["id"] for d in data["dependencies"]), ["TST_company_idea", "tst.1"])
        self.assertTrue(all(tool.has_approved_confirmation(d) for d in data["dependencies"]))
        self.assertEqual(data["last_reviewed"], DATE)
        self.assertEqual([f["id"] for f in json.loads(notfound.read_text(encoding="utf-8"))], ["tst.absent"])
        after_first = self.registry.read_bytes()
        again = self.run_cli(*self.common, "--write")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("Изменений реестра нет", again.stdout)
        self.assertEqual(self.registry.read_bytes(), after_first)

    def test_input_errors_exit_with_2(self):
        for args, fragment in (
            (["--target-dir", str(self.target)], "build-label"),
            ([*self.common[:2], "--build-label", "   ", *self.common[4:]], "не может быть пустым"),
            (["--target-dir", str(self.target / "nope"), "--build-label", LABEL], "не найден"),
        ):
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn(fragment, result.stderr)

    def test_report_without_registry_data_is_an_error(self):
        self.report.write_text(json.dumps({"_external_dependencies": {"registry_available": False}}), encoding="utf-8")
        result = self.run_cli(*self.common)
        self.assertEqual(result.returncode, 2)
        self.assertIn("registry_available", result.stderr)

    def test_generated_registry_passes_the_auditors_own_validation(self):
        self.run_cli(*self.common, "--write")
        entries = json.loads(self.registry.read_text(encoding="utf-8"))["dependencies"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            helper = base.RepositoryAuditTests("make_clean_cli_fixture")
            helper.make_clean_cli_fixture(root)
            target = root / "docs" / "research" / "external-dependencies.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(tool.dump_registry(registry(entries)), encoding="utf-8")
            out = Path(temp) / "audit.json"
            subprocess.run([sys.executable, "-I", str(base.SCRIPT), str(root), "--json", str(out)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
            external = json.loads(out.read_text(encoding="utf-8"))["_external_dependencies"]
        self.assertTrue(external["registry_available"])
        self.assertEqual(external["registry_validation_issues"], [])
        self.assertEqual(external["counts"]["registry_entries"], 2)


if __name__ == "__main__":
    unittest.main()
