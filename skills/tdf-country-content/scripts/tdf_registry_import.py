#!/usr/bin/env python3
"""Подтверждение внешних зависимостей по файлам целевой сборки, которые предоставил пользователь.

Политика проекта (docs/research/external-dependencies.md): TDF самостоятельный мод, и статус
`confirmed` можно ставить только по точному определению в файлах TDF или в файле целевой сборки,
явно предоставленном пользователем (`verification_origin: user_provided`, точный путь файла).
Инструмент автоматизирует именно этот случай: берёт каталог целевой сборки, находит в нём
определения кандидатов (находок аудитора со статусом не confirmed) и записывает подтверждения
в реестр вместе с доказательством: путь файла, строка, SHA-256 файла и метка сборки.

Что он НЕ делает: не угадывает по имени и не подтверждает «по похожести»; не добавляет в реестр
ненайденные ID; не трогает уже подтверждённые записи; по умолчанию ничего не пишет (нужен --write).

Каталог целевой сборки может быть корнем мода (`common/`, `events/`, `localisation/`) или
родителем такого корня: файлы классифицируются по частям пути. Искомые определения:
    event                     country_event/news_event/... { id = X } в events/
    idea                      ideas = { группа = { X = { } } } в common/ideas/
    scripted_effect(_or_trigger)   блоки верхнего уровня в common/scripted_effects и scripted_triggers
    equipment                 equipments = { X = { } } в common/units/equipment/
    technology                technologies = { X = { } } в common/technologies/
    mio                       блоки верхнего уровня в common/military_industrial_organization/organizations/
    localisation              ключи в английской локализации (localisation/english, *_l_english.yml)

Коды выхода: 0 — успех (в том числе когда ничего не найдено); 2 — ошибка входных данных.

Примеры (из корня репозитория):
    python3 -I skills/tdf-country-content/scripts/tdf_registry_import.py \\
        --target-dir D:/builds/md --build-label "MD 2026-11 (коммит abc1234)"
    ... --write --not-found-report reports/not-found.json
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from tdf_audit_lib.core import (  # noqa: E402
    LOC_LINE_RE, AuditInputError, Block, parse_hoi, read, scalar,
)
from tdf_audit_lib.external_dependencies import has_approved_confirmation  # noqa: E402

DEFAULT_REGISTRY = "docs/research/external-dependencies.json"
AUDIT_SCRIPT = Path(__file__).resolve().parent / "tdf_audit.py"
EVIDENCE_KIND = "user-provided target build definition"
MAX_EVIDENCE = 5
MAX_WHERE_USED = 25

# тип находки аудитора -> виды определений в целевой сборке
TYPE_TO_KINDS = {
    "event": ("event",),
    "idea": ("idea",),
    "localisation": ("localisation",),
    "scripted_effect": ("scripted_effect",),
    "scripted_effect_or_trigger": ("scripted_effect", "scripted_trigger"),
    "equipment": ("equipment",),
    "technology": ("technology",),
    "mio": ("mio",),
}


class ImportInputError(Exception):
    """Ошибка входных данных: печатается в stderr, код выхода 2."""


class Evidence:
    __slots__ = ("path", "line")

    def __init__(self, path: str, line: int):
        self.path, self.line = path, line


def classify_path(relative: str) -> Optional[str]:
    """Вид определений, которые лежат в файле, по его пути; None если файл не интересен."""
    rel = "/" + relative.replace("\\", "/").lower()
    name = rel.rsplit("/", 1)[-1]
    if name.endswith(".yml"):
        if "/localisation/" in rel and ("/english/" in rel or name.endswith("_l_english.yml")):
            return "localisation"
        return None
    if not name.endswith(".txt"):
        return None
    for marker, kind in (
        ("/events/", "event"),
        ("/common/ideas/", "idea"),
        ("/common/scripted_effects/", "scripted_effect"),
        ("/common/scripted_triggers/", "scripted_trigger"),
        ("/common/units/equipment/", "equipment"),
        ("/common/technologies/", "technology"),
        ("/common/military_industrial_organization/organizations/", "mio"),
    ):
        if marker in rel:
            return kind
    return None


def _top_blocks(root: Block) -> Iterable[Tuple[str, int, Block]]:
    for entry in root.entries:
        if isinstance(entry.value, Block):
            yield entry.key.value, entry.line, entry.value


def extract_definitions(kind: str, text: str) -> List[Tuple[str, int]]:
    """(id, строка) определений заданного вида в тексте одного файла."""
    found: List[Tuple[str, int]] = []
    if kind == "localisation":
        for number, line in enumerate(text.splitlines(), 1):
            match = LOC_LINE_RE.match(line)
            if match:
                found.append((match.group(1), number))
        return found
    root = parse_hoi(text).root
    if kind == "event":
        for key, _line, block in _top_blocks(root):
            if key.endswith("_event"):
                for entry in block.entries:
                    if entry.key.value == "id" and scalar(entry):
                        found.append((scalar(entry), entry.line))
    elif kind == "idea":
        for key, _line, ideas in _top_blocks(root):
            if key == "ideas":
                for _group, _gline, group in _top_blocks(ideas):
                    found.extend((name, line) for name, line, _ in _top_blocks(group))
    elif kind in ("equipment", "technology"):
        container = "equipments" if kind == "equipment" else "technologies"
        for key, _line, block in _top_blocks(root):
            if key == container:
                found.extend((name, line) for name, line, _ in _top_blocks(block))
    else:  # scripted_effect, scripted_trigger, mio: блоки верхнего уровня
        found.extend((name, line) for name, line, _ in _top_blocks(root))
    return found


def scan_target(target: Path) -> Tuple[Dict[Tuple[str, str], List[Evidence]], Dict[str, int], int]:
    """Индекс {(вид, id): [доказательства]}, число файлов по видам и число файлов с ошибками разбора."""
    index: Dict[Tuple[str, str], List[Evidence]] = defaultdict(list)
    files_by_kind: Dict[str, int] = defaultdict(int)
    unreadable = 0
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        relative = path.relative_to(target).as_posix()
        kind = classify_path(relative)
        if kind is None:
            continue
        try:
            text = read(path)
            definitions = extract_definitions(kind, text)
        except (AuditInputError, OSError):
            unreadable += 1
            continue
        files_by_kind[kind] += 1
        for name, line in definitions:
            index[(kind, name)].append(Evidence(relative, line))
    return index, dict(files_by_kind), unreadable


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(str(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_evidence(finding_type: str, dep_id: str, index) -> List[Evidence]:
    evidence: List[Evidence] = []
    for kind in TYPE_TO_KINDS.get(finding_type, ()):
        evidence.extend(index.get((kind, dep_id), []))
    return evidence


def namespace_of(finding_type: str, dep_id: str) -> str:
    if finding_type == "event" and "." in dep_id:
        return dep_id.split(".", 1)[0]
    return dep_id.split("_", 1)[0]


def build_confirmation(finding: dict, existing: Optional[dict], evidence: Sequence[Evidence],
                       target: Path, label: str, checked_at: str,
                       hashes: Dict[str, str]) -> dict:
    """Запись реестра со статусом confirmed (новая или повышенная из unknown/assumption)."""
    verification = []
    for item in list(evidence)[:MAX_EVIDENCE]:
        if item.path not in hashes:
            hashes[item.path] = sha256_of(target / item.path)
        verification.append({"kind": EVIDENCE_KIND, "path": item.path, "line": item.line,
                             "sha256": hashes[item.path], "build": label})
    count = len(evidence)
    notes = ("Точное определение найдено в файле целевой сборки, предоставленном пользователем "
             "(сборка: {}). Подтверждение относится только к указанным определениям и путям.".format(label))
    if count > 1:
        notes += " Определений с этим ID в сборке: {} (в доказательствах до {}).".format(count, MAX_EVIDENCE)
    entry = dict(existing) if existing else {
        "type": finding["type"],
        "id": finding["id"],
        "where_used": [
            {"repository": "TDF", "path": ref.get("path"), "line": ref.get("line"),
             "usage": ref.get("source_kind") or ref.get("usage") or "reference"}
            for ref in (finding.get("references") or [])[:MAX_WHERE_USED] if ref.get("path")
        ],
        "namespace": namespace_of(finding["type"], finding["id"]),
    }
    entry.update({
        "status": "confirmed",
        "expected_source": "Точное определение найдено в файле целевой сборки, предоставленном пользователем (сборка: {}).".format(label),
        "checked_at": checked_at,
        "verification": verification,
        "notes": notes,
        "verification_origin": "user_provided",
    })
    if not has_approved_confirmation(entry):
        raise ImportInputError("внутренняя ошибка: запись {} {} не прошла проверку подтверждения".format(
            entry.get("type"), entry.get("id")))
    return entry


def plan_import(findings: Sequence[dict], registry: dict, index, target: Path, label: str,
                checked_at: str, hashes: Optional[Dict[str, str]] = None):
    """Вернуть (новые записи, повышенные записи, ненайденные находки, пропущенные неизвестного типа)."""
    hashes = hashes if hashes is not None else {}
    existing = {(d.get("type"), d.get("id")): d for d in registry.get("dependencies", []) if isinstance(d, dict)}
    new_entries, upgraded, not_found, skipped = [], [], [], []
    seen = set()
    for finding in findings:
        key = (finding.get("type"), finding.get("id"))
        if key in seen or finding.get("status") == "confirmed":
            continue
        seen.add(key)
        if finding.get("type") not in TYPE_TO_KINDS:
            skipped.append(finding)
            continue
        if existing.get(key, {}).get("status") == "confirmed":
            continue
        evidence = find_evidence(finding["type"], finding["id"], index)
        if not evidence:
            not_found.append(finding)
            continue
        entry = build_confirmation(finding, existing.get(key), evidence, target, label, checked_at, hashes)
        (upgraded if key in existing else new_entries).append(entry)
    return new_entries, upgraded, not_found, skipped


def merge_registry(registry: dict, new_entries: Sequence[dict], upgraded: Sequence[dict], checked_at: str) -> dict:
    """Новый реестр: повышенные записи заменяют старые на месте, новые добавляются по (type, id)."""
    result = dict(registry)
    replacements = {(d["type"], d["id"]): d for d in upgraded}
    dependencies = [replacements.get((d.get("type"), d.get("id")), d) for d in registry.get("dependencies", [])]
    dependencies.extend(sorted(new_entries, key=lambda d: (d["type"], d["id"])))
    result["dependencies"] = dependencies
    if new_entries or upgraded:
        result["last_reviewed"] = checked_at
    return result


def dump_registry(registry: dict) -> str:
    return json.dumps(registry, ensure_ascii=False, indent=2) + "\n"


def load_findings(args) -> List[dict]:
    if args.report:
        try:
            report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ImportInputError("не удалось прочитать отчёт {}: {}".format(args.report, exc)) from exc
    else:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "audit.json"
            proc = subprocess.run(
                [sys.executable, "-I", str(AUDIT_SCRIPT), args.repo, "--require-external-registry", "--json", str(out)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, universal_newlines=True,
                encoding="utf-8", check=False)
            if proc.returncode not in (0, 1) or not out.exists():
                raise ImportInputError("аудитор завершился с кодом {}: {}".format(
                    proc.returncode, proc.stderr.strip() or "нет сообщения"))
            report = json.loads(out.read_text(encoding="utf-8"))
    external = report.get("_external_dependencies") or {}
    if not external.get("registry_available"):
        raise ImportInputError("в отчёте нет данных реестра внешних зависимостей (registry_available = false)")
    return [f for f in external.get("findings", []) if isinstance(f, dict)]


def summarize(findings, new_entries, upgraded, not_found, skipped, files_by_kind, unreadable, label) -> str:
    def by_type(items):
        counts: Dict[str, int] = defaultdict(int)
        for item in items:
            counts[item["type"]] += 1
        return ", ".join("{} {}".format(t, n) for t, n in sorted(counts.items())) or "—"

    open_total = sum(1 for f in findings if f.get("status") != "confirmed")
    scanned = ", ".join("{} {}".format(k, v) for k, v in sorted(files_by_kind.items())) or "ничего"
    lines = [
        "Целевая сборка «{}»: просканированы файлы ({}).".format(label, scanned),
        "Кандидатов без подтверждения: {}. Найдено определений: {} (новых записей {}, повышено до confirmed {}). Не найдено: {}.".format(
            open_total, len(new_entries) + len(upgraded), len(new_entries), len(upgraded), len(not_found)),
        "Найдено по типам: {}.".format(by_type(list(new_entries) + list(upgraded))),
        "Не найдено по типам: {}.".format(by_type(not_found)),
    ]
    if skipped:
        lines.append("Пропущено (неизвестный тип находки): {}.".format(len(skipped)))
    if unreadable:
        lines.append("Файлов, которые не удалось прочитать: {}.".format(unreadable))
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Подтверждение внешних зависимостей по целевой сборке")
    parser.add_argument("--target-dir", required=True, help="каталог целевой сборки, предоставленный пользователем")
    parser.add_argument("--build-label", required=True,
                        help="метка сборки для доказательства, например «MD 2026-11 (коммит abc1234)»")
    parser.add_argument("--repo", default=".", help="корень репозитория TDF (по умолчанию текущая папка)")
    parser.add_argument("--registry", help="путь к реестру (по умолчанию {} в корне репозитория)".format(DEFAULT_REGISTRY))
    parser.add_argument("--report", help="готовый JSON аудитора (иначе аудит запускается здесь)")
    parser.add_argument("--write", action="store_true", help="записать подтверждения в реестр (по умолчанию пробный прогон)")
    parser.add_argument("--not-found-report", help="сохранить ненайденные находки в JSON (что ещё запросить у пользователя)")
    parser.add_argument("--date", default=datetime.date.today().isoformat(), help="дата проверки (по умолчанию сегодня)")
    args = parser.parse_args(argv)
    try:
        target = Path(args.target_dir)
        if not target.is_dir():
            raise ImportInputError("каталог целевой сборки не найден: {}".format(target))
        label = args.build_label.strip()
        if not label:
            raise ImportInputError("--build-label не может быть пустым: без метки сборки доказательство анонимно")
        registry_path = Path(args.registry) if args.registry else Path(args.repo) / DEFAULT_REGISTRY
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ImportInputError("не удалось прочитать реестр {}: {}".format(registry_path, exc)) from exc
        findings = load_findings(args)
        index, files_by_kind, unreadable = scan_target(target)
        new_entries, upgraded, not_found, skipped = plan_import(findings, registry, index, target, label, args.date)
        print(summarize(findings, new_entries, upgraded, not_found, skipped, files_by_kind, unreadable, label))
        if args.not_found_report:
            payload = [{"type": f["type"], "id": f["id"], "references": (f.get("references") or [])[:3]}
                       for f in sorted(not_found, key=lambda f: (f["type"], f["id"]))]
            Path(args.not_found_report).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")
            print("Ненайденные находки сохранены: {}".format(args.not_found_report))
        if not (new_entries or upgraded):
            print("Изменений реестра нет.")
        elif args.write:
            registry_path.write_text(dump_registry(merge_registry(registry, new_entries, upgraded, args.date)),
                                     encoding="utf-8", newline="\n")
            print("Реестр обновлён: {}. Дальше: tdf_baseline.py check (подтверждения могут сократить находки).".format(
                registry_path))
        else:
            print("ПРОБНЫЙ ПРОГОН: реестр не изменён. Добавьте --write, чтобы записать подтверждения.")
        return 0
    except ImportInputError as exc:
        print("ОШИБКА: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
