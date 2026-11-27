"""Аудит жизненного цикла национальных духов и идей.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import defaultdict
from pathlib import Path
from .core import (
    Block,
    Entry,
    Token,
    _state_flow_script_files,
    find_named_blocks,
    get_scalar,
    iter_files,
    parse_hoi,
    read,
    scalar,
    walk_entries,
)
from .indexes import (
    get_loc_value,
)


def build_idea_lifecycle_audit(repo, countries, loc_index, content_indexes, event_parsed=None):
    """Audit idea definitions, their grant/removal chain and custom tooltip references."""
    mod = Path(repo) / "mdredux"
    country_tags = set(countries)
    definitions = list(content_indexes.get("idea_definitions", []))
    definitions_by_id = defaultdict(list)
    for item in definitions:
        definitions_by_id[item["id"]].append(item)
    defined_ids = set(definitions_by_id)

    duplicate_idea_ids = [
        {"id": idea_id, "definitions": [
            {"path": item["path"], "line": item["line"], "visibility": item["visibility"]}
            for item in values
        ]}
        for idea_id, values in sorted(definitions_by_id.items()) if len(values) > 1
    ]

    def resolved_name_key(item):
        key = item.get("name") or item["id"]
        seen = {item["id"]}
        while key in definitions_by_id and key not in seen:
            seen.add(key)
            base = definitions_by_id[key][0]
            key = base.get("name") or base["id"]
        return key

    missing_name_localisation = []
    stage_name_links = []
    legacy_ids_without_suffix = []
    for item in definitions:
        if item["owner_tag"] not in country_tags:
            continue
        name_key = resolved_name_key(item)
        if name_key not in loc_index:
            missing_name_localisation.append({
                "idea": item["id"], "name_key": name_key,
                "path": item["path"], "line": item["line"],
            })
        if item.get("name") in defined_ids and item["name"] != item["id"]:
            stage_name_links.append({
                "idea": item["id"], "base_idea": item["name"],
                "path": item["path"], "line": item["line"],
            })
        if not item["id"].endswith("_idea"):
            legacy_ids_without_suffix.append({
                "idea": item["id"], "path": item["path"], "line": item["line"],
            })

    # Inspect common scripts, events and country history; idea definitions themselves
    # are excluded so their metadata is not mistaken for grant/read/remove effects.
    sources = []
    common_dir = mod / "common"
    ideas_dir = common_dir / "ideas"
    for path in iter_files(common_dir, ".txt"):
        if ideas_dir in path.parents:
            continue
        sources.append((path, parse_hoi(read(path))))
    for path, parsed in (event_parsed or {}).items():
        sources.append((Path(path), parsed))
    history_dirs = (mod / "history" / "countries", common_dir / "history" / "countries")
    history_files = sorted({
        path for directory in history_dirs for path in iter_files(directory, ".txt")
    })
    # Match state-flow discovery for extensionless scripted files. The broad
    # .txt scan above already covers normal script files; only add unseen paths.
    existing_source_paths = {path for path, _ in sources}
    for directory in (
        common_dir / "scripted_effects",
        common_dir / "scripted_triggers",
        common_dir / "on_actions",
    ):
        for path in _state_flow_script_files(directory):
            if path not in existing_source_paths:
                sources.append((path, parse_hoi(read(path))))
                existing_source_paths.add(path)

    for path in history_files:
        if path not in existing_source_paths:
            sources.append((path, parse_hoi(read(path))))
            existing_source_paths.add(path)

    references = []
    granted_ids = set()
    source_parse_errors = []
    swap_blocks = []

    def values_from(entry):
        if isinstance(entry.value, Token):
            return [entry.value.value]
        if not isinstance(entry.value, Block):
            return []
        values = []
        for child in entry.value.items:
            if isinstance(child, Token):
                values.append(child.value)
            elif isinstance(child, Entry) and child.key.value in ("idea", "add_idea", "remove_idea"):
                value = scalar(child)
                if value:
                    values.append(value)
        return values

    def add_ref(idea_id, usage, path, line):
        if not idea_id or idea_id.lower() in ("no", "none", "empty"):
            return
        references.append({"idea": idea_id, "usage": usage, "path": str(path), "line": line})
        if usage in ("add", "timed_add"):
            granted_ids.add(idea_id)

    for path, parsed in sources:
        for issue in parsed.issues:
            source_parse_errors.append("{}:{}: {}".format(path, issue.line, issue.message))
        for swap in find_named_blocks(parsed.root, "swap_ideas"):
            old_idea = get_scalar(swap, "remove_idea")
            new_idea = get_scalar(swap, "add_idea")
            if old_idea and new_idea:
                swap_blocks.append({
                    "remove_idea": old_idea, "add_idea": new_idea,
                    "path": str(path), "line": swap.line,
                })
        for entry in walk_entries(parsed.root):
            key = entry.key.value
            if key in ("add_ideas", "add_idea"):
                for idea_id in values_from(entry):
                    add_ref(idea_id, "add", path, entry.line)
            elif key in ("remove_ideas", "remove_idea"):
                for idea_id in values_from(entry):
                    add_ref(idea_id, "remove", path, entry.line)
            elif key in ("has_idea", "has_ideas"):
                for idea_id in values_from(entry):
                    add_ref(idea_id, "condition", path, entry.line)
            elif key == "add_timed_idea" and isinstance(entry.value, Block):
                add_ref(get_scalar(entry.value, "idea"), "timed_add", path, entry.line)

    # Connect staged idea families to explicit swap_ideas transitions. This is
    # an inventory only: a missing same-block swap is a review candidate because
    # removal may happen in a separate effect or external script.
    stage_ids = {item["idea"] for item in stage_name_links}
    family_by_id = {
        idea_id: resolved_name_key(values[0])
        for idea_id, values in definitions_by_id.items()
    }
    stage_swap_transitions = []
    for swap in swap_blocks:
        old_idea, new_idea = swap["remove_idea"], swap["add_idea"]
        if old_idea == new_idea or old_idea not in family_by_id or new_idea not in family_by_id:
            continue
        old_family, new_family = family_by_id[old_idea], family_by_id[new_idea]
        if old_family == new_family and (old_idea in stage_ids or new_idea in stage_ids):
            owner_tag = next(
                (item["owner_tag"] for item in definitions_by_id[new_idea] if item.get("owner_tag")),
                next((item["owner_tag"] for item in definitions_by_id[old_idea] if item.get("owner_tag")), None),
            )
            stage_swap_transitions.append({
                "owner_tag": owner_tag, "family": old_family,
                "remove_idea": old_idea, "add_idea": new_idea,
                "path": swap["path"], "line": swap["line"],
                "classification": "same_family_swap_candidate",
            })

    ideas_added_by_any_swap = {item["add_idea"] for item in swap_blocks}
    stage_grant_without_swap_candidates = []
    for item in references:
        idea_id = item["idea"]
        if item["usage"] != "add" or idea_id not in stage_ids or idea_id in ideas_added_by_any_swap:
            continue
        owner_tag = next(
            (definition["owner_tag"] for definition in definitions_by_id.get(idea_id, [])
             if definition.get("owner_tag")),
            None,
        )
        stage_grant_without_swap_candidates.append({
            **item, "owner_tag": owner_tag,
            "classification": "direct_stage_grant_review_candidate",
            "reason": (
                "Ступень выдана add_idea/add_ideas вне найденного swap_ideas; "
                "проверь, где снимается предыдущая ступень (включая scripted/external effects)."
            ),
        })

    missing_local_references = []
    external_references = []
    unresolved_unprefixed_references = []
    for item in references:
        if item["idea"] in defined_ids:
            continue
        match = re.match(r"^([A-Z]{3})_", item["idea"])
        if match and match.group(1) in country_tags:
            missing_local_references.append(dict(item))
        elif match:
            external_references.append(dict(item))
        else:
            unresolved_unprefixed_references.append(dict(item))

    scripted_names = {
        item["name"]
        for definitions_for_tag in content_indexes.get("scripted_defs", {}).values()
        for item in definitions_for_tag
    }
    tooltip_missing_loc = []
    tooltip_scripted_candidates = []
    tooltip_static_key_candidates = []
    for item in definitions:
        if item["owner_tag"] not in country_tags:
            continue
        for tooltip_key in item["custom_modifier_tooltips"]:
            if tooltip_key not in loc_index:
                tooltip_missing_loc.append({
                    "idea": item["id"], "tooltip_key": tooltip_key,
                    "path": item["path"], "line": item["line"],
                })
                continue
            value = get_loc_value(loc_index, tooltip_key) or ""
            bracket_refs = re.findall(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", value)
            if bracket_refs:
                tooltip_scripted_candidates.append({
                    "idea": item["id"], "tooltip_key": tooltip_key,
                    "bracket_references": bracket_refs,
                    "defined_text_names_found": [
                        name for name in bracket_refs if name in scripted_names
                    ],
                    "path": item["path"], "line": item["line"],
                })
            for nested_key in re.findall(r"\$([A-Za-z0-9_.-]+)\$", value):
                if nested_key.startswith(item["owner_tag"] + "_") and nested_key not in loc_index:
                    tooltip_static_key_candidates.append({
                        "idea": item["id"], "tooltip_key": tooltip_key,
                        "nested_localisation_key": nested_key,
                        "path": item["path"], "line": item["line"],
                    })

    scripted_idea_refs = {
        idea_id
        for definitions_for_tag in content_indexes.get("scripted_defs", {}).values()
        for definition in definitions_for_tag
        for idea_id in definition.get("idea_refs", [])
    }
    hidden_ids = {item["id"] for item in definitions if item["visibility"] == "hidden"}
    hidden_with_scripted_refs = hidden_ids & scripted_idea_refs

    locally_ungranted = [
        {
            "idea": item["id"], "path": item["path"], "line": item["line"],
            "visibility": item["visibility"], "owner_tag": item["owner_tag"],
        }
        for item in definitions
        if item["owner_tag"] in country_tags and item["id"] not in granted_ids
    ]
    locally_ungranted.sort(key=lambda item: (item["owner_tag"], item["idea"]))

    return {
        "counts": {
            "idea_files": len(iter_files(ideas_dir, ".txt")),
            "definitions": len(definitions),
            "visible_ideas": sum(1 for item in definitions if item["visibility"] == "visible"),
            "hidden_ideas": len(hidden_ids),
            "idea_references": len(references),
            "add_references": sum(1 for item in references if item["usage"] == "add"),
            "timed_add_references": sum(1 for item in references if item["usage"] == "timed_add"),
            "remove_references": sum(1 for item in references if item["usage"] == "remove"),
            "condition_references": sum(1 for item in references if item["usage"] == "condition"),
            "ideas_with_on_add": sum(1 for item in definitions if item["has_on_add"]),
            "ideas_with_on_remove": sum(1 for item in definitions if item["has_on_remove"]),
            "ideas_with_cancel": sum(1 for item in definitions if item["has_cancel"]),
            "ideas_with_allowed_civil_war": sum(1 for item in definitions if item["has_allowed_civil_war"]),
            "custom_modifier_tooltips": sum(len(item["custom_modifier_tooltips"]) for item in definitions),
            "history_files": len(history_files),
        },
        "parse_errors": list(content_indexes.get("idea_parse_errors", [])),
        "source_parse_errors": source_parse_errors,
        "duplicate_idea_ids": duplicate_idea_ids,
        "missing_name_localisation": missing_name_localisation,
        "stage_name_links": stage_name_links,
        "stage_swap_transitions": stage_swap_transitions,
        "stage_grant_without_swap_candidates": stage_grant_without_swap_candidates,
        "legacy_ids_without_idea_suffix": legacy_ids_without_suffix,
        "missing_local_idea_references": missing_local_references,
        "external_idea_references": external_references,
        "unresolved_unprefixed_idea_references": unresolved_unprefixed_references,
        "not_locally_granted_candidates": locally_ungranted[:100],
        "not_locally_granted_candidates_truncated": max(0, len(locally_ungranted) - 100),
        "custom_modifier_tooltip_missing_localisation": tooltip_missing_loc,
        "custom_modifier_tooltip_scripted_loc_candidates": tooltip_scripted_candidates,
        "custom_modifier_tooltip_static_key_candidates": tooltip_static_key_candidates,
        "hidden_ideas_with_scripted_loc_refs": len(hidden_with_scripted_refs),
        "hidden_ideas_without_scripted_loc_refs": len(hidden_ids - hidden_with_scripted_refs),
        "history_inventory_available": bool(history_files),
        "idea_definitions": definitions,
        "idea_references": references,
    }
