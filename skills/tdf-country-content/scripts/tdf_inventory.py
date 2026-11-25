#!/usr/bin/env python3
"""Reproducible structural inventory for the TDF/MDC source files in this checkout.

Run from the repository root:
    python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
    python3 -I skills/tdf-country-content/scripts/tdf_inventory.py . --json inventory.json

Counts are syntactic block/file counts from this checkout. They do not prove
that the complete target installation loads these files or that content works in-game.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

_AUDIT_PATH = Path(__file__).with_name("tdf_audit.py")
_SPEC = importlib.util.spec_from_file_location("tdf_audit", _AUDIT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Cannot load tdf_audit.py")
audit = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = audit
_SPEC.loader.exec_module(audit)


def files_with_suffix(directory: Path, suffix: str = ".txt") -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*")
                  if path.is_file() and path.suffix.lower() == suffix)


def parse(path: Path):
    return audit.parse_hoi(audit.read(path))


def block_entries(entries: Iterable[Any]) -> int:
    return sum(1 for entry in entries
               if isinstance(entry, audit.Entry) and isinstance(entry.value, audit.Block))


def count_idea_blocks(parsed, category_name: str) -> int:
    total = 0
    for ideas_block in audit.find_named_blocks(parsed.root, "ideas"):
        for category in audit.direct_entries(ideas_block, category_name):
            if isinstance(category.value, audit.Block):
                total += block_entries(category.value.entries)
    return total


def collect_inventory(repository: Path) -> Dict[str, Any]:
    mod = repository / "mdredux"
    common = mod / "common"

    focus_paths = sorted((common / "national_focus").rglob("*_Focus_Tree.txt"))
    idea_paths = files_with_suffix(common / "ideas")
    event_paths = files_with_suffix(mod / "events")
    decision_paths = files_with_suffix(common / "decisions")
    scripted_loc_paths = files_with_suffix(common / "scripted_localisation")
    history_paths = files_with_suffix(common / "history" / "countries")
    mio_paths = files_with_suffix(common / "military_industrial_organization" /
                                  "organizations")
    technology_paths = files_with_suffix(common / "technologies")
    equipment_paths = files_with_suffix(common / "units" / "equipment")

    focus_rows = []
    for path in focus_paths:
        parsed = parse(path)
        focus_rows.append({
            "path": path.relative_to(repository).as_posix(),
            "tag": audit.detect_tag(parsed),
            "focus_blocks": len(audit.find_named_blocks(parsed.root, "focus")),
            "parse_issues": len(parsed.issues),
        })

    idea_country = 0
    idea_hidden = 0
    idea_parse_issues = 0
    for path in idea_paths:
        parsed = parse(path)
        idea_country += count_idea_blocks(parsed, "country")
        idea_hidden += count_idea_blocks(parsed, "hidden_ideas")
        idea_parse_issues += len(parsed.issues)

    country_events = 0
    news_events = 0
    namespace_declarations = 0
    event_parse_issues = 0
    for path in event_paths:
        parsed = parse(path)
        country_events += block_entries(audit.direct_entries(parsed.root, "country_event"))
        news_events += block_entries(audit.direct_entries(parsed.root, "news_event"))
        namespace_declarations += len(audit.direct_entries(parsed.root, "add_namespace"))
        event_parse_issues += len(parsed.issues)

    decision_categories = 0
    decisions = 0
    decision_parse_issues = 0
    for path in decision_paths:
        parsed = parse(path)
        categories = [entry for entry in parsed.root.entries
                      if isinstance(entry, audit.Entry) and isinstance(entry.value, audit.Block)]
        decision_categories += len(categories)
        for category in categories:
            decisions += block_entries(category.value.entries)
        decision_parse_issues += len(parsed.issues)

    scripted_definitions = 0
    scripted_parse_issues = 0
    for path in scripted_loc_paths:
        parsed = parse(path)
        scripted_definitions += block_entries(audit.direct_entries(parsed.root, "defined_text"))
        scripted_parse_issues += len(parsed.issues)

    mio_definitions = 0
    mio_parse_issues = 0
    for path in mio_paths:
        parsed = parse(path)
        mio_definitions += block_entries(parsed.root.entries)
        mio_parse_issues += len(parsed.issues)

    return {
        "scope": "TDF/MDC source files present in this checkout; not a complete target-installation or runtime inventory",
        "method": {
            "parser": "skills/tdf-country-content/scripts/tdf_audit.py::parse_hoi",
            "focus_trees": "all *_Focus_Tree.txt files recursively under mdredux/common/national_focus",
            "ideas": "direct country and hidden_ideas child blocks inside every ideas block",
            "events": "top-level country_event, news_event and add_namespace declarations in mdredux/events/*.txt",
            "decisions": "top-level decision-category blocks and their direct child decision blocks",
            "scripted_localisation": "top-level defined_text blocks",
            "mio": "top-level named blocks in common/military_industrial_organization/organizations/*.txt; includes generic templates",
            "technology_equipment_history": "file counts by repository path and .txt suffix",
        },
        "files": {
            "focus_trees": len(focus_paths),
            "idea_files": len(idea_paths),
            "event_files": len(event_paths),
            "decision_files": len(decision_paths),
            "scripted_localisation_files": len(scripted_loc_paths),
            "country_history_files": len(history_paths),
            "mio_organization_files": len(mio_paths),
            "technology_files": len(technology_paths),
            "equipment_files": len(equipment_paths),
        },
        "blocks": {
            "focuses": sum(row["focus_blocks"] for row in focus_rows),
            "ideas_country": idea_country,
            "ideas_hidden": idea_hidden,
            "ideas_country_plus_hidden": idea_country + idea_hidden,
            "country_events": country_events,
            "news_events": news_events,
            "events_total": country_events + news_events,
            "event_namespace_declarations": namespace_declarations,
            "decision_categories": decision_categories,
            "decisions": decisions,
            "scripted_localisation_defined_text": scripted_definitions,
            "mio_top_level_definitions_including_generic_templates": mio_definitions,
        },
        "parse_issues": {
            "focus_tree_files": sum(row["parse_issues"] for row in focus_rows),
            "idea_files": idea_parse_issues,
            "event_files": event_parse_issues,
            "decision_files": decision_parse_issues,
            "scripted_localisation_files": scripted_parse_issues,
            "mio_files": mio_parse_issues,
        },
        "focus_trees": focus_rows,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Структурная инвентаризация TDF/MDC")
    parser.add_argument("repo", nargs="?", default=".", help="корень репозитория")
    parser.add_argument("--json", metavar="PATH", help="сохранить JSON-отчёт в UTF-8")
    args = parser.parse_args(argv)

    try:
        result = collect_inventory(Path(args.repo).resolve())
    except (OSError, audit.AuditInputError, ValueError) as exc:
        print("ОШИБКА: {}".format(exc), file=sys.stderr)
        return 2

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        target = Path(args.json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
