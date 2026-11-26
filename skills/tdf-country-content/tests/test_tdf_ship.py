import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "tdf_ship.py"
SPEC = importlib.util.spec_from_file_location("tdf_ship", SCRIPT)
ship = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ship)

SHA = "a" * 40
PUSH_URL = "https://x-access-token:SECRET@github.com/o/r.git"


class FakeGit:
    def __init__(self, branch="feat/x", dirty="", ahead="1", subjects="feat: x", remote_sha=None):
        self.branch, self.dirty, self.ahead, self.subjects = branch, dirty, ahead, subjects
        self.remote_sha = remote_sha or SHA
        self.calls = []

    def __call__(self, args):
        args = list(args)
        self.calls.append(args)
        if args[:2] == ["rev-parse", "--abbrev-ref"]:
            return self.branch + "\n"
        if args[0] == "status":
            return self.dirty
        if args[0] == "rev-list":
            return self.ahead + "\n"
        if args[:2] == ["rev-parse", "HEAD"]:
            return SHA + "\n"
        if args[0] == "log" and args[1] == "--format=%s":
            return self.subjects
        if args[0] == "log":
            return "\0".join(s + "\n\nтело" for s in self.subjects.split("\n")) + "\0"
        if args[0] == "ls-remote":
            return "{}\trefs/heads/x\n".format(self.remote_sha)
        return ""

    def pushed(self):
        return any(c[0] == "push" for c in self.calls)


class FakeApi:
    """runs: список ответов на опрос прогонов; последний повторяется."""

    def __init__(self, runs, existing_pr=None, merge=(200, None), jobs=None):
        self.runs, self.existing_pr, self.jobs = list(runs), existing_pr, jobs or []
        self.merge = merge if merge[1] is not None else (200, {"merged": True, "sha": "abc1234" + "0" * 33})
        self.calls = []

    def __call__(self, method, path, payload):
        self.calls.append((method, path, payload))
        if method == "GET" and "/pulls?" in path:
            return 200, [self.existing_pr] if self.existing_pr else []
        if method == "POST" and path.endswith("/pulls"):
            return 201, {"number": 7, "html_url": "https://github.com/o/r/pull/7"}
        if method == "GET" and "/actions/runs?" in path:
            batch = self.runs.pop(0) if len(self.runs) > 1 else self.runs[0]
            return 200, {"workflow_runs": batch}
        if method == "GET" and path.endswith("/jobs?per_page=50"):
            return 200, {"jobs": self.jobs}
        if method == "PUT":
            return self.merge
        if method == "DELETE":
            return 204, {}
        return 404, {}

    def methods(self):
        return [c[0] for c in self.calls]


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def run(api, git, *args):
    clock = FakeClock()
    opts = ship.build_parser().parse_args(list(args))
    shipper = ship.Shipper(api, git, sleep=clock.sleep, clock=clock.clock)
    return shipper.ship(opts, "o", "r", PUSH_URL)


PENDING = [{"id": 1, "status": "in_progress", "conclusion": None}]
GREEN = [{"id": 1, "status": "completed", "conclusion": "success"}]
RED = [{"id": 1, "status": "completed", "conclusion": "failure"}]


class PureFunctionTests(unittest.TestCase):
    def test_parse_repo_variants(self):
        for url in ("https://github.com/o/r", "https://github.com/o/r.git", "git@github.com:o/r.git",
                    "https://x-access-token:T0K@github.com/o/r.git", "https://github.com/o/r/"):
            self.assertEqual(ship.parse_repo(url), ("o", "r"), url)

    def test_parse_repo_rejects_other_hosts(self):
        with self.assertRaises(ship.ShipError):
            ship.parse_repo("https://example.com/o/r.git")

    def test_sanitize_hides_token(self):
        self.assertEqual(ship.sanitize("push https://x:SECRET@github.com", "SECRET"), "push https://x:***@github.com")
        self.assertEqual(ship.sanitize("no token", ""), "no token")

    def test_classify_runs(self):
        self.assertEqual(ship.classify_runs([]), "none")
        self.assertEqual(ship.classify_runs(PENDING), "pending")
        self.assertEqual(ship.classify_runs(GREEN), "success")
        self.assertEqual(ship.classify_runs(GREEN + RED), "failure")
        self.assertEqual(ship.classify_runs([{"status": "completed", "conclusion": "cancelled"}]), "failure")
        self.assertEqual(ship.classify_runs([{"status": "completed", "conclusion": "skipped"}]), "success")

    def test_default_title_only_for_a_single_commit(self):
        self.assertEqual(ship.default_title_and_body(["feat: x"], ["feat: x\n\nтело"])[0], "feat: x")
        self.assertEqual(ship.default_title_and_body(["a", "b"], ["a", "b"])[0], "")


class ShipFlowTests(unittest.TestCase):
    def test_green_ci_merges_and_deletes_branch(self):
        api, git = FakeApi([PENDING, PENDING, GREEN]), FakeGit()
        code, line = run(api, git)
        self.assertEqual(code, 0)
        self.assertEqual(line, "OK PR #7 слит abc1234 | CI зелёный | ветка удалена")
        self.assertIn("PUT", api.methods())
        self.assertIn("DELETE", api.methods())
        self.assertTrue(git.pushed())

    def test_merge_method_and_keep_branch(self):
        api = FakeApi([GREEN])
        code, line = run(api, FakeGit(), "--merge-method", "squash", "--keep-branch")
        self.assertEqual(code, 0)
        self.assertIn("ветка оставлена", line)
        self.assertNotIn("DELETE", api.methods())
        self.assertEqual([c for c in api.calls if c[0] == "PUT"][0][2], {"merge_method": "squash"})

    def test_failed_ci_does_not_merge_and_names_the_failing_step(self):
        jobs = [{"name": "Auditor and inventory unit tests", "conclusion": "success", "steps": []},
                {"name": "Full repository audit", "conclusion": "failure", "steps": [
                    {"name": "Run full audit", "conclusion": "success"},
                    {"name": "Check for new findings against baseline", "conclusion": "failure"}]}]
        api = FakeApi([RED], jobs=jobs)
        code, line = run(api, FakeGit())
        self.assertEqual(code, 1)
        self.assertIn("Full repository audit > Check for new findings against baseline", line)
        self.assertNotIn("PUT", api.methods())
        self.assertNotIn("DELETE", api.methods())

    def test_no_ci_runs_after_grace_merges_with_note(self):
        api = FakeApi([[]])
        code, line = run(api, FakeGit(), "--grace", "30", "--interval", "10")
        self.assertEqual(code, 0)
        self.assertIn("CI не запускался (paths-фильтр)", line)
        self.assertIn("PUT", api.methods())

    def test_timeout_leaves_pr_open(self):
        api = FakeApi([PENDING])
        code, line = run(api, FakeGit(), "--timeout", "60", "--interval", "20")
        self.assertEqual(code, 3)
        self.assertIn("ТАЙМАУТ", line)
        self.assertNotIn("PUT", api.methods())

    def test_existing_open_pr_is_reused(self):
        api = FakeApi([GREEN], existing_pr={"number": 7, "html_url": "https://github.com/o/r/pull/7"})
        code, _ = run(api, FakeGit())
        self.assertEqual(code, 0)
        self.assertNotIn("POST", api.methods())

    def test_no_merge_stops_after_green_ci(self):
        api = FakeApi([GREEN])
        code, line = run(api, FakeGit(), "--no-merge")
        self.assertEqual(code, 0)
        self.assertIn("готов к слиянию", line)
        self.assertNotIn("PUT", api.methods())

    def test_rejected_merge_is_an_error_with_rebase_hint(self):
        api = FakeApi([GREEN], merge=(405, {"message": "Base branch was modified"}))
        with self.assertRaises(ship.ShipError) as ctx:
            run(api, FakeGit())
        self.assertIn("rebase", str(ctx.exception))

    def test_dry_run_sends_nothing(self):
        api, git = FakeApi([GREEN]), FakeGit()
        code, line = run(api, git, "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(line.startswith("DRY-RUN o/r"))
        self.assertEqual(api.calls, [])
        self.assertFalse(git.pushed())


class PreconditionTests(unittest.TestCase):
    def assert_refused(self, git, *args, fragment=""):
        api = FakeApi([GREEN])
        with self.assertRaises(ship.ShipError) as ctx:
            run(api, git, *args)
        self.assertIn(fragment, str(ctx.exception))
        self.assertEqual(api.calls, [])
        self.assertFalse(git.pushed())

    def test_dirty_tree(self):
        self.assert_refused(FakeGit(dirty=" M file.txt\n"), fragment="незакоммиченные")

    def test_on_base_branch(self):
        self.assert_refused(FakeGit(branch="main"), fragment="рабочую ветку")

    def test_detached_head(self):
        self.assert_refused(FakeGit(branch="HEAD"), fragment="рабочую ветку")

    def test_nothing_ahead(self):
        self.assert_refused(FakeGit(ahead="0"), fragment="нет коммитов")

    def test_several_commits_need_a_title(self):
        self.assert_refused(FakeGit(ahead="2", subjects="a\nb"), fragment="--title")

    def test_unverified_push(self):
        api, git = FakeApi([GREEN]), FakeGit(remote_sha="b" * 40)
        with self.assertRaises(ship.ShipError) as ctx:
            run(api, git)
        self.assertIn("пуш не подтверждён", str(ctx.exception))
        self.assertEqual(api.calls, [])


class CliTests(unittest.TestCase):
    def test_missing_token_is_a_clear_error_and_exit_2(self):
        env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, "-I", str(SCRIPT), "--title", "t"], cwd=temp, env=env,
                                    universal_newlines=True, encoding="utf-8", stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("GH_TOKEN", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
