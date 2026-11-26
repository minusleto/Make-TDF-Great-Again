#!/usr/bin/env python3
"""Отправить текущую ветку через PR одной командой: пуш, PR, ожидание CI, слияние.

Печатает ОДНУ строку итога (дёшево для агента и для лога) и выставляет код выхода:
    0 — PR слит (или проверен и оставлен из-за --no-merge)
    1 — CI упал: PR остаётся открытым, ветка не удаляется
    2 — ошибка условий или API (грязное дерево, нет токена, пуш отклонён, слияние отклонено)
    3 — таймаут ожидания CI: PR остаётся открытым

Токен берётся ТОЛЬКО из переменной окружения GH_TOKEN (или GITHUB_TOKEN): в аргументы не
передаётся и в вывод не попадает. Права: Contents и Pull requests (read/write); для изменений в
.github/workflows/ нужно ещё право Workflows.

Если workflow не запускается из-за фильтра `paths` (правка вне путей триггера), прогонов CI не
появится: после --grace секунд PR сливается с пометкой «CI не запускался».

Примеры (из корня репозитория, на ветке с закоммиченными изменениями):
    python3 -I skills/tdf-country-content/scripts/tdf_ship.py --title "docs: поправить README"
    python3 -I skills/tdf-country-content/scripts/tdf_ship.py --dry-run
    python3 -I skills/tdf-country-content/scripts/tdf_ship.py --no-merge --body-file pr.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Callable, List, Optional, Sequence, Tuple

API = "https://api.github.com"
EXIT_OK, EXIT_CI_FAILED, EXIT_ERROR, EXIT_TIMEOUT = 0, 1, 2, 3
GOOD_CONCLUSIONS = frozenset({"success", "skipped", "neutral"})
BODY_LIMIT = 3000

ApiFn = Callable[[str, str, Optional[dict]], Tuple[int, object]]
GitFn = Callable[[Sequence[str]], str]


class ShipError(Exception):
    """Ошибка условий или API: печатается в stderr, код выхода 2."""


def parse_repo(remote_url: str) -> Tuple[str, str]:
    """owner/repo из https-, ssh- или credential-URL GitHub."""
    match = re.search(r"github\.com[:/]+([^/\s@]+)/([^/\s]+?)(?:\.git)?/?$", remote_url.strip())
    if not match:
        raise ShipError("не удалось определить репозиторий GitHub из remote: {}".format(
            sanitize(remote_url, os.environ.get("GH_TOKEN", ""))))
    return match.group(1), match.group(2)


def sanitize(text: str, token: str) -> str:
    return text.replace(token, "***") if token else text


def classify_runs(runs: Sequence[dict]) -> str:
    """'none' | 'pending' | 'success' | 'failure' по списку прогонов workflow для одного SHA."""
    if not runs:
        return "none"
    if any(run.get("status") != "completed" for run in runs):
        return "pending"
    if all(run.get("conclusion") in GOOD_CONCLUSIONS for run in runs):
        return "success"
    return "failure"


def failed_steps(api: ApiFn, owner: str, repo: str, runs: Sequence[dict], limit: int = 3) -> List[str]:
    """«Задание > шаг» для упавших мест (по прогонам с неуспешным итогом)."""
    found: List[str] = []
    for run in runs:
        if run.get("conclusion") in GOOD_CONCLUSIONS:
            continue
        status, data = api("GET", "/repos/{}/{}/actions/runs/{}/jobs?per_page=50".format(owner, repo, run["id"]), None)
        jobs = data.get("jobs", []) if status == 200 and isinstance(data, dict) else []
        for job in jobs:
            if job.get("conclusion") in GOOD_CONCLUSIONS or job.get("conclusion") is None:
                continue
            bad = [s["name"] for s in job.get("steps", []) if s.get("conclusion") not in GOOD_CONCLUSIONS | {None}]
            found.append("{} > {}".format(job["name"], bad[0]) if bad else job["name"])
    return found[:limit] or ["см. прогон CI"]


def default_title_and_body(subjects: Sequence[str], messages: Sequence[str]) -> Tuple[str, str]:
    title = subjects[0] if len(subjects) == 1 else ""
    body = "\n\n".join(m.strip() for m in messages)[:BODY_LIMIT]
    return title, body


class Shipper:
    """Оркестратор. Внешний мир (git, API, время) передаётся зависимостями: так он тестируется."""

    def __init__(self, api: ApiFn, git: GitFn, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic):
        self.api, self.git, self.sleep, self.clock = api, git, sleep, clock

    def _request(self, method: str, path: str, payload: Optional[dict] = None) -> Tuple[int, object]:
        return self.api(method, path, payload)

    def ship(self, opts: argparse.Namespace, owner: str, repo: str, push_url: str) -> Tuple[int, str]:
        branch = opts.branch or self.git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        if branch in ("HEAD", opts.base):
            raise ShipError("перейдите на рабочую ветку (сейчас «{}»)".format(branch))
        if self.git(["status", "--porcelain"]).strip():
            raise ShipError("есть незакоммиченные изменения: закоммитьте или уберите их")
        if opts.fetch:
            self.git(["fetch", "--quiet", "origin", opts.base])
        ahead = int(self.git(["rev-list", "--count", "origin/{}..HEAD".format(opts.base)]).strip() or "0")
        if ahead == 0:
            raise ShipError("в ветке нет коммитов относительно origin/{}".format(opts.base))
        head_sha = self.git(["rev-parse", "HEAD"]).strip()
        subjects = self.git(["log", "--format=%s", "origin/{}..HEAD".format(opts.base)]).strip().split("\n")
        raw_messages = self.git(["log", "--format=%B%x00", "origin/{}..HEAD".format(opts.base)])
        messages = [m for m in raw_messages.split("\0") if m.strip()]
        title_default, body_default = default_title_and_body(subjects, messages)
        title = opts.title or title_default
        if not title:
            raise ShipError("в ветке {} коммитов: задайте --title".format(ahead))
        body = opts.body if opts.body is not None else body_default
        if opts.dry_run:
            return EXIT_OK, "DRY-RUN {}/{}: ветка {} -> {}, коммитов {}, заголовок «{}»".format(
                owner, repo, branch, opts.base, ahead, title)

        self.git(["push", "--quiet", push_url, "HEAD:refs/heads/{}".format(branch)])
        remote = self.git(["ls-remote", push_url, "refs/heads/{}".format(branch)]).split("\t")[0].strip()
        if remote != head_sha:
            raise ShipError("пуш не подтверждён: на GitHub {} вместо {}".format(remote[:7] or "ничего", head_sha[:7]))

        status, existing = self._request("GET", "/repos/{}/{}/pulls?head={}:{}&state=open".format(owner, repo, owner, branch))
        if status == 200 and isinstance(existing, list) and existing:
            pr = existing[0]
        else:
            status, pr = self._request("POST", "/repos/{}/{}/pulls".format(owner, repo),
                                       {"title": title, "head": branch, "base": opts.base, "body": body})
            if status != 201 or not isinstance(pr, dict):
                raise ShipError("не удалось создать PR ({}): {}".format(status, json.dumps(pr, ensure_ascii=False)[:200]))
        number, url = pr["number"], pr["html_url"]

        verdict, runs = self._wait_for_ci(owner, repo, head_sha, opts)
        if verdict == "failure":
            return EXIT_CI_FAILED, "CI УПАЛ PR #{}: {} | {}".format(
                number, "; ".join(failed_steps(self.api, owner, repo, runs)), url)
        if verdict == "timeout":
            return EXIT_TIMEOUT, "ТАЙМАУТ ожидания CI PR #{} | {}".format(number, url)
        ci_note = "CI не запускался (paths-фильтр)" if verdict == "none" else "CI зелёный"
        if opts.no_merge:
            return EXIT_OK, "OK PR #{} готов к слиянию | {} | {}".format(number, ci_note, url)

        status, merged = self._request("PUT", "/repos/{}/{}/pulls/{}/merge".format(owner, repo, number),
                                       {"merge_method": opts.merge_method})
        if status != 200 or not isinstance(merged, dict) or not merged.get("merged"):
            detail = merged.get("message", "") if isinstance(merged, dict) else ""
            raise ShipError("PR #{} не слит ({}): {}. Возможно, нужен rebase на origin/{}".format(
                number, status, detail, opts.base))
        deleted = "ветка оставлена"
        if not opts.keep_branch:
            status, _ = self._request("DELETE", "/repos/{}/{}/git/refs/heads/{}".format(owner, repo, branch))
            deleted = "ветка удалена" if status in (200, 204) else "ветку удалить не удалось"
        return EXIT_OK, "OK PR #{} слит {} | {} | {}".format(number, str(merged.get("sha", ""))[:7], ci_note, deleted)

    def _wait_for_ci(self, owner: str, repo: str, sha: str, opts: argparse.Namespace) -> Tuple[str, List[dict]]:
        started = self.clock()
        while True:
            status, data = self._request("GET", "/repos/{}/{}/actions/runs?head_sha={}".format(owner, repo, sha))
            runs = data.get("workflow_runs", []) if status == 200 and isinstance(data, dict) else []
            state = classify_runs(runs)
            elapsed = self.clock() - started
            if state in ("success", "failure"):
                return state, runs
            if state == "none" and elapsed >= opts.grace:
                return "none", runs
            if elapsed >= opts.timeout:
                return "timeout", runs
            self.sleep(opts.interval)


def make_git(token: str, cwd: Optional[str] = None) -> GitFn:
    def run(args: Sequence[str]) -> str:
        proc = subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, encoding="utf-8", check=False)
        if proc.returncode != 0:
            raise ShipError("git {} завершился с кодом {}: {}".format(
                args[0], proc.returncode, sanitize(proc.stderr.strip(), token)[:300]))
        return proc.stdout
    return run


def make_api(token: str) -> ApiFn:
    def call(method: str, path: str, payload: Optional[dict]) -> Tuple[int, object]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(API + path, data=data, method=method, headers={
            "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
            "Content-Type": "application/json", "User-Agent": "tdf-ship"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                text = response.read().decode("utf-8")
                return response.status, (json.loads(text) if text else {})
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", "replace")
            try:
                return exc.code, json.loads(text)
            except json.JSONDecodeError:
                return exc.code, {"message": text[:200]}
        except (urllib.error.URLError, OSError) as exc:
            raise ShipError("сеть недоступна: {}".format(sanitize(str(exc), token))) from exc
    return call


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Отправить ветку через PR: пуш, CI, слияние, одна строка итога")
    parser.add_argument("--title", help="заголовок PR (по умолчанию тема единственного коммита)")
    parser.add_argument("--body", help="описание PR (по умолчанию тексты коммитов)")
    parser.add_argument("--body-file", help="файл с описанием PR")
    parser.add_argument("--base", default="main", help="целевая ветка (по умолчанию main)")
    parser.add_argument("--branch", help="имя ветки на GitHub (по умолчанию текущая)")
    parser.add_argument("--no-merge", action="store_true", help="дождаться CI, но не сливать")
    parser.add_argument("--keep-branch", action="store_true", help="не удалять ветку после слияния")
    parser.add_argument("--merge-method", choices=("merge", "squash", "rebase"), default="merge")
    parser.add_argument("--timeout", type=int, default=900, help="сколько секунд ждать CI (по умолчанию 900)")
    parser.add_argument("--grace", type=int, default=60, help="сколько секунд ждать появления прогонов CI")
    parser.add_argument("--interval", type=int, default=15, help="период опроса CI, секунд")
    parser.add_argument("--no-fetch", dest="fetch", action="store_false", help="не обновлять origin/<base>")
    parser.add_argument("--dry-run", action="store_true", help="проверить условия и показать план, ничего не отправляя")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    opts = build_parser().parse_args(argv)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    try:
        if not token and not opts.dry_run:
            raise ShipError("нужна переменная окружения GH_TOKEN (токен с правами Contents и Pull requests)")
        if opts.body_file:
            with open(opts.body_file, encoding="utf-8") as handle:
                opts.body = handle.read()
        git = make_git(token)
        owner, repo = parse_repo(git(["remote", "get-url", "origin"]))
        push_url = "https://x-access-token:{}@github.com/{}/{}.git".format(token, owner, repo)
        code, line = Shipper(make_api(token), git).ship(opts, owner, repo, push_url)
        print(sanitize(line, token))
        return code
    except (ShipError, OSError) as exc:
        print("ОШИБКА: {}".format(sanitize(str(exc), token)), file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
