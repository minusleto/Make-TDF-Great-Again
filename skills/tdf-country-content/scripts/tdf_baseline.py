#!/usr/bin/env python3
"""Baseline («храповик») для статического аудита TDF.

Проект развивает инструменты и скиллы поиска ошибок и не чинит чужой контент, поэтому
известные ERROR-находки фиксируются в baseline-файле, а проверка падает только на НОВЫХ.

    check   сравнить текущий аудит с baseline; печатает краткий итог (несколько строк)
    update  перезаписать baseline текущим состоянием (осознанное действие)

Что считается находкой: те же ERROR-проверки, что определяют код выхода `tdf_audit.py`
(проверки по тегам, глобальные события и решения, parse-ошибки, ошибки реестра).
WARN и INFO в baseline не входят.

Отпечаток находки содержательный и не содержит номеров строк: сдвиг строк не создаёт
«новых» находок, а исправление одной ошибки и появление другой не маскируют друг друга.

Коды выхода (`check`): 0 — новых находок нет; 1 — есть новые; 2 — ошибка входных данных.

Примеры (из корня репозитория):
    python3 -I skills/tdf-country-content/scripts/tdf_baseline.py check
    python3 -I skills/tdf-country-content/scripts/tdf_baseline.py check --report reports/full-audit.json
    python3 -I skills/tdf-country-content/scripts/tdf_baseline.py check --strict-tags KAZ
    python3 -I skills/tdf-country-content/scripts/tdf_baseline.py update
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

SCHEMA_VERSION = 1
DEFAULT_BASELINE = "docs/research/audit-baseline.json"
AUDIT_SCRIPT = Path(__file__).resolve().parent / "tdf_audit.py"

# Должны совпадать с tdf_audit.ERRORS / PARSE_ERROR_FIELDS: это проверяется unit-тестом.
TAG_ERROR_CHECKS = (
    "parse_errors", "dup_focus_ids", "log_mismatch", "no_log", "prereq_missing",
    "mutex_missing", "relpos_missing", "title_missing", "desc_missing", "dup_loc_keys",
    "scripted_loc_duplicate", "swap_same_idea", "event_not_found",
    "event_option_label_missing", "event_option_no_log",
    "event_title_key_missing", "event_desc_key_missing",
)
PARSE_ERROR_FIELDS = (
    "parse_errors", "source_parse_errors", "mio_parse_errors",
    "equipment_parse_errors", "module_parse_errors", "technology_parse_errors",
    "script_parse_errors",
)
PARSE_REPORT_SCOPES = ("_ideas", "_events", "_decisions", "_industry", "_state_flow")
EVENT_ERROR_CHECKS = (
    "missing_event_ids", "duplicate_event_ids", "unresolved_references",
    "missing_localisation", "missing_option_localisation", "missing_title_fields",
    "missing_desc_fields", "missing_option_names", "options_without_log",
)
DECISION_ERROR_CHECKS = (
    "duplicate_decision_ids", "missing_category_localisation",
    "missing_decision_localisation", "invalid_numeric_fields",
    "missing_decision_references", "missing_focus_references", "missing_event_references",
)
# Позиционные поля не входят в отпечаток.
POSITION_KEYS = frozenset({"line", "lines", "column", "col"})
# «path.txt:297: сообщение» -> «path.txt: сообщение»: номер строки внутри текста тоже позиционный.
EMBEDDED_LINE = re.compile(r":\d+(?=:)")


class BaselineInputError(Exception):
    """Ошибка входных данных: нет отчёта, baseline или аудитор не отработал."""


def _canonical(value):
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in value.items() if k not in POSITION_KEYS}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def fingerprint(entry) -> str:
    """Стабильный отпечаток одной находки без номеров строк."""
    if isinstance(entry, str):
        return EMBEDDED_LINE.sub("", entry)
    canon = _canonical(entry)
    if isinstance(canon, list) and all(isinstance(item, str) for item in canon):
        return " | ".join(canon)
    return json.dumps(canon, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def extract_findings(report: dict) -> Dict[str, List[str]]:
    """Сопоставить отчёту аудитора {"<scope>/<check>": [отпечатки]} только по ERROR-проверкам."""
    findings: Dict[str, List[str]] = {}

    def add(scope: str, check: str, entries: Optional[Iterable]) -> None:
        prints = sorted({fingerprint(entry) for entry in (entries or [])})
        if prints:
            findings["{}/{}".format(scope, check)] = prints

    for tag, result in report.items():
        if tag.startswith("_") or not isinstance(result, dict):
            continue
        for check in TAG_ERROR_CHECKS:
            add(tag, check, result.get(check))

    events = report.get("_events") or {}
    for check in EVENT_ERROR_CHECKS:
        add("_events", check, events.get(check))

    decisions = report.get("_decisions") or {}
    for check in DECISION_ERROR_CHECKS:
        add("_decisions", check, decisions.get(check))
    add("_decisions", "duplicate_category_ids", [
        item for item in decisions.get("duplicate_category_ids") or []
        if isinstance(item, dict) and item.get("scope") == "same_file"
    ])

    for scope in PARSE_REPORT_SCOPES:
        section = report.get(scope) or {}
        for field in PARSE_ERROR_FIELDS:
            add(scope, field, section.get(field))

    external = report.get("_external_dependencies") or {}
    if external.get("registry_available"):
        add("_external_dependencies", "registry_validation_issues",
            external.get("registry_validation_issues"))
    return findings


def flatten(findings: Dict[str, List[str]]) -> Set[Tuple[str, str]]:
    return {(key, item) for key, items in findings.items() for item in items}


def scope_of(key: str) -> str:
    return key.split("/", 1)[0]


def compare(baseline: Dict[str, List[str]], current: Dict[str, List[str]],
            strict_tags: Sequence[str] = ()):
    """Вернуть (новые, исправленные). Для strict-тегов новой считается любая текущая находка."""
    base, cur = flatten(baseline), flatten(current)
    new = cur - base
    strict = {tag.upper() for tag in strict_tags}
    if strict:
        new |= {pair for pair in cur if scope_of(pair[0]).upper() in strict}
    return new, base - cur


def render(baseline: Dict[str, List[str]], current: Dict[str, List[str]], new, fixed,
           strict_tags: Sequence[str] = (), max_samples: int = 5) -> str:
    lines = ["Baseline: {} известных находок. Сейчас: {}. Новых: {}. Исправлено: {}.".format(
        len(flatten(baseline)), len(flatten(current)), len(new), len(fixed))]
    if strict_tags:
        lines.append("Строгие теги (любая находка = нарушение): {}.".format(
            ", ".join(sorted(t.upper() for t in strict_tags))))
    if new:
        lines.append("РЕГРЕССИЯ: новые находки.")
        grouped: Dict[str, List[str]] = {}
        for key, item in sorted(new):
            grouped.setdefault(key, []).append(item)
        for key, items in grouped.items():
            shown = "; ".join(items[:max_samples])
            extra = "" if len(items) <= max_samples else " (+{} ещё)".format(len(items) - max_samples)
            lines.append("  {} (+{}): {}{}".format(key, len(items), shown, extra))
        lines.append("Исправьте их или, если находка осознанно принята, обновите baseline командой `update`.")
    else:
        lines.append("OK: новых находок нет.")
    if fixed:
        lines.append("Исправлено {} находок из baseline: после слияния обновите baseline (`update`), "
                     "чтобы закрепить улучшение.".format(len(fixed)))
    return "\n".join(lines)


def read_baseline(path: Path) -> Dict[str, List[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BaselineInputError("baseline не найден: {}. Создайте его командой `update`.".format(path)) from None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BaselineInputError("не удалось прочитать baseline {}: {}".format(path, exc)) from exc
    if data.get("schema") != SCHEMA_VERSION or not isinstance(data.get("findings"), dict):
        raise BaselineInputError("неподдерживаемый формат baseline (ожидается schema={})".format(SCHEMA_VERSION))
    return {key: list(items) for key, items in data["findings"].items()}


def write_baseline(path: Path, findings: Dict[str, List[str]]) -> None:
    by_scope: Dict[str, int] = {}
    for key, items in findings.items():
        by_scope[scope_of(key)] = by_scope.get(scope_of(key), 0) + len(items)
    data = {
        "schema": SCHEMA_VERSION,
        "description": ("Известные ERROR-находки tdf_audit.py на момент создания. Служебный файл: "
                        "не читать целиком, пользоваться tdf_baseline.py check."),
        "counts": {"total": sum(by_scope.values()), "by_scope": dict(sorted(by_scope.items()))},
        "findings": dict(sorted(findings.items())),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")


def load_report(args) -> dict:
    if args.report:
        try:
            return json.loads(Path(args.report).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise BaselineInputError("не удалось прочитать отчёт {}: {}".format(args.report, exc)) from exc
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp) / "audit.json"
        cmd = [sys.executable, "-I", str(AUDIT_SCRIPT), args.repo, "--json", str(out)]
        if not args.no_require_registry:
            cmd.append("--require-external-registry")
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                              universal_newlines=True, encoding="utf-8", check=False)
        if proc.returncode not in (0, 1) or not out.exists():
            raise BaselineInputError("аудитор завершился с кодом {}: {}".format(
                proc.returncode, proc.stderr.strip() or "нет сообщения"))
        return json.loads(out.read_text(encoding="utf-8"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Baseline для статического аудита TDF")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("check", "сравнить аудит с baseline"), ("update", "обновить baseline")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--repo", default=".", help="корень репозитория (по умолчанию текущая папка)")
        p.add_argument("--report", help="готовый JSON аудитора (иначе аудит запускается здесь)")
        p.add_argument("--baseline", default=None,
                       help="путь к baseline (по умолчанию {} в корне репозитория)".format(DEFAULT_BASELINE))
        p.add_argument("--no-require-registry", action="store_true",
                       help="не требовать реестр внешних зависимостей при запуске аудитора")
        if name == "check":
            p.add_argument("--strict-tags", default="",
                           help="теги через запятую, где любая находка считается нарушением")
            p.add_argument("--max-samples", type=int, default=5, help="сколько примеров показывать на проверку")
            p.add_argument("--fail-on-fixed", action="store_true",
                           help="считать нарушением и исправленные находки (заставляет обновить baseline)")
    args = parser.parse_args(argv)
    baseline_path = Path(args.baseline) if args.baseline else Path(args.repo) / DEFAULT_BASELINE
    try:
        current = extract_findings(load_report(args))
        if args.command == "update":
            write_baseline(baseline_path, current)
            print("Baseline обновлён: {} находок -> {}".format(len(flatten(current)), baseline_path))
            return 0
        baseline = read_baseline(baseline_path)
        strict = [t.strip() for t in args.strict_tags.split(",") if t.strip()]
        new, fixed = compare(baseline, current, strict)
        print(render(baseline, current, new, fixed, strict, args.max_samples))
        return 1 if new or (args.fail_on_fixed and fixed) else 0
    except BaselineInputError as exc:
        print("ОШИБКА: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
