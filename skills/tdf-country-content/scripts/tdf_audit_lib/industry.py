"""Аудит MIO, техники, модулей и технологий.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import defaultdict
from pathlib import Path
from .core import (
    Block,
    Entry,
    Token,
    direct_entries,
    find_named_blocks,
    get_block,
    get_scalar,
    iter_files,
    nested_entries,
    parse_hoi,
    read,
    scalar,
    walk_entries,
)
from .decisions import (
    numeric_value,
    technology_unlock_values,
)


def build_industry_audit(repo, countries, loc_index, all_focus=None, event_parsed=None):
    """Index local MIO/equipment/technology definitions and audit script references.

    Missing references are classified as local candidates or unresolved dependencies.
    Do not infer their source from another mod; require a TDF or user-provided target file.
    """
    mod = Path(repo) / "mdredux"
    country_tags = set(countries)
    mio_dir = mod / "common" / "military_industrial_organization" / "organizations"
    equipment_dir = mod / "common" / "units" / "equipment"
    technology_dir = mod / "common" / "technologies"

    mio_files = iter_files(mio_dir, ".txt")
    mio_definitions, mio_parse_errors = [], []
    local_mio_visibility_focus_candidates = []
    for path in mio_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            mio_parse_errors.append("{}:{}".format(path, issue))
        for entry in parsed.root.entries:
            if not isinstance(entry, Entry) or not isinstance(entry.value, Block):
                continue
            block = entry.value
            if not any(direct_entries(block, field) for field in
                       ("name", "allowed", "include", "initial_trait", "trait", "equipment_type")):
                continue
            match = re.match(r"^([A-Z]{3})_", entry.key.value)
            owner_tag = match.group(1) if match else None
            visible = get_block(block, "visible")
            visible_focus_refs = [
                scalar(item) for item in nested_entries(visible, "has_completed_focus")
            ] if visible else []
            visible_focus_refs = [item for item in visible_focus_refs if item]
            mio_definitions.append({
                "id": entry.key.value,
                "name": get_scalar(block, "name"),
                "include": get_scalar(block, "include"),
                "owner_tag": owner_tag,
                "path": str(path),
                "line": entry.line,
                "has_allowed": bool(direct_entries(block, "allowed")),
                "has_visible": bool(direct_entries(block, "visible")),
                "visible_focus_refs": visible_focus_refs,
                "has_initial_trait": bool(direct_entries(block, "initial_trait")),
                "trait_count": len(direct_entries(block, "trait")),
                "has_equipment_type": bool(direct_entries(block, "equipment_type")),
            })
            if visible and owner_tag in country_tags:
                for focus_entry in nested_entries(visible, "has_completed_focus"):
                    target = scalar(focus_entry)
                    if target and target not in (all_focus or set()):
                        local_mio_visibility_focus_candidates.append({
                            "mio": entry.key.value, "focus": target,
                            "path": str(path), "line": focus_entry.line,
                        })

    mio_groups = defaultdict(list)
    for item in mio_definitions:
        mio_groups[item["id"]].append(item)
    defined_mio_ids = set(mio_groups)
    duplicate_mio_ids = [
        {"id": key, "definitions": [
            {"path": item["path"], "line": item["line"]} for item in values
        ]}
        for key, values in sorted(mio_groups.items()) if len(values) > 1
    ]

    local_missing_mio_names, external_missing_mio_names = [], []
    duplicate_mio_name_keys = defaultdict(list)
    mio_name_matches_other_mio = []
    for item in mio_definitions:
        name_key = item["name"]
        if not name_key:
            continue
        duplicate_mio_name_keys[name_key].append({
            "id": item["id"], "path": item["path"], "line": item["line"],
        })
        if name_key not in loc_index:
            candidate = {
                "mio": item["id"], "name_key": name_key,
                "path": item["path"], "line": item["line"],
            }
            (local_missing_mio_names if item["owner_tag"] in country_tags
             else external_missing_mio_names).append(candidate)
        if name_key in defined_mio_ids and name_key != item["id"]:
            mio_name_matches_other_mio.append({
                "mio": item["id"], "name_key": name_key,
                "other_mio_definition": name_key,
                "path": item["path"], "line": item["line"],
            })
    duplicate_mio_name_keys = [
        {"name_key": key, "definitions": values}
        for key, values in sorted(duplicate_mio_name_keys.items()) if len(values) > 1
    ]

    equipment_files = iter_files(equipment_dir, ".txt")
    equipment_definitions, equipment_parse_errors = [], []
    for path in equipment_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            equipment_parse_errors.append("{}:{}".format(path, issue))
        for container in find_named_blocks(parsed.root, "equipments"):
            for entry in container.entries:
                if isinstance(entry, Entry) and isinstance(entry.value, Block):
                    equipment_definitions.append({
                        "id": entry.key.value, "path": str(path), "line": entry.line,
                    })
    equipment_groups = defaultdict(list)
    for item in equipment_definitions:
        equipment_groups[item["id"]].append(item)
    defined_equipment_ids = set(equipment_groups)
    duplicate_equipment_ids = [
        {"id": key, "definitions": [
            {"path": item["path"], "line": item["line"]} for item in values
        ]}
        for key, values in sorted(equipment_groups.items()) if len(values) > 1
    ]

    module_dir = equipment_dir / "modules"
    module_files = iter_files(module_dir, ".txt")
    module_ids = set()
    module_parse_errors = []
    for path in module_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            module_parse_errors.append("{}:{}".format(path, issue))
        for container in find_named_blocks(parsed.root, "equipment_modules"):
            for entry in container.entries:
                if isinstance(entry, Entry) and isinstance(entry.value, Block):
                    module_ids.add(entry.key.value)

    technology_files = iter_files(technology_dir, ".txt")
    technology_ids = set()
    technology_parse_errors = []
    equipment_unlock_references = []
    equipment_unlocks = defaultdict(list)
    module_unlocks = defaultdict(list)
    for path in technology_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            technology_parse_errors.append("{}:{}".format(path, issue))
        for container in find_named_blocks(parsed.root, "technologies"):
            for entry in container.entries:
                if not isinstance(entry, Entry) or not isinstance(entry.value, Block):
                    continue
                technology_id = entry.key.value
                technology_ids.add(technology_id)
                for field, target_kind, target_index in (
                    ("enable_equipments", "equipment", equipment_unlocks),
                    ("enable_equipment_modules", "module", module_unlocks),
                ):
                    for unlock_entry in direct_entries(entry.value, field):
                        for target_id in technology_unlock_values(unlock_entry):
                            target_index[target_id].append(technology_id)
                            equipment_unlock_references.append({
                                "technology": technology_id,
                                "unlock_kind": target_kind,
                                "target": target_id,
                                "path": str(path),
                                "line": unlock_entry.line,
                            })

    # Parse all common scripts (focuses, decisions, ideas, scripted effects, etc.) plus events.
    # Do not scan MIO/equipment definition files as usage sources.
    sources = []
    for path in iter_files(mod / "common", ".txt"):
        if mio_dir in path.parents or equipment_dir in path.parents:
            continue
        sources.append((path, parse_hoi(read(path))))
    for path, parsed in (event_parsed or {}).items():
        sources.append((Path(path), parsed))

    # A missing local technology ID has no assumed source. Keep it as a review candidate
    # until the relevant TDF or user-provided target file is available.
    unknown_technology_references = []
    seen_technology_refs = set()
    for path, parsed in sources:
        for entry in walk_entries(parsed.root):
            if entry.key.value != "has_tech":
                continue
            technology = scalar(entry)
            if technology is None and isinstance(entry.value, Block):
                technology = (
                    get_scalar(entry.value, "technology")
                    or get_scalar(entry.value, "tech")
                    or get_scalar(entry.value, "id")
                )
                if technology is None:
                    tokens = [item.value for item in entry.value.items if isinstance(item, Token)]
                    technology = tokens[0] if tokens else None
            if not technology or technology in technology_ids:
                continue
            marker = (technology, str(path), entry.line)
            if marker in seen_technology_refs:
                continue
            seen_technology_refs.add(marker)
            unknown_technology_references.append({
                "technology": technology, "command": "has_tech",
                "path": str(path), "line": entry.line,
                "classification": "not_defined_in_local_technology_slice",
            })

    mio_references, variant_definitions, stockpile_grants = [], [], []
    unknown_equipment_type_references, unknown_module_references = [], []
    invalid_stockpile_amounts = []
    seen_mio_refs = set()

    def add_mio_reference(mio_id, path, line, usage):
        ref_key = (mio_id, str(path), line, usage)
        if ref_key not in seen_mio_refs:
            seen_mio_refs.add(ref_key)
            mio_references.append({
                "mio": mio_id, "path": str(path), "line": line, "usage": usage,
            })

    for path, parsed in sources:
        for entry in walk_entries(parsed.root):
            key = entry.key.value
            key_match = re.fullmatch(r"mio:([A-Za-z0-9_]+)", key)
            if key_match:
                add_mio_reference(key_match.group(1), path, entry.line, key)
            value = scalar(entry)
            if value:
                for match in re.finditer(r"\bmio:([A-Za-z0-9_]+)\b", value):
                    add_mio_reference(match.group(1), path, entry.line, key)

        for variant in find_named_blocks(parsed.root, "create_equipment_variant"):
            type_id = get_scalar(variant, "type")
            modules = get_block(variant, "modules")
            module_refs = []
            if modules:
                for module_entry in modules.entries:
                    if not isinstance(module_entry, Entry):
                        continue
                    module_id = scalar(module_entry)
                    if not module_id or module_id.lower() in ("empty", "none"):
                        continue
                    module_refs.append(module_id)
                    if module_id not in module_ids:
                        unknown_module_references.append({
                            "module": module_id, "variant": get_scalar(variant, "name"),
                            "path": str(path), "line": module_entry.line,
                        })
            if type_id and type_id not in defined_equipment_ids:
                unknown_equipment_type_references.append({
                    "type": type_id, "action": "create_equipment_variant",
                    "variant": get_scalar(variant, "name"), "path": str(path), "line": variant.line,
                })
            variant_definitions.append({
                "name": get_scalar(variant, "name"),
                "type": type_id,
                "design_team": get_scalar(variant, "design_team"),
                "allow_without_tech": get_scalar(variant, "allow_without_tech"),
                "module_count": len(module_refs),
                "type_unlock_technologies": sorted(set(equipment_unlocks.get(type_id, []))) if type_id else [],
                "module_unlock_technologies": [
                    {"module": module_id, "technologies": sorted(set(module_unlocks.get(module_id, [])))}
                    for module_id in module_refs
                ],
                "path": str(path), "line": variant.line,
            })

        for grant in find_named_blocks(parsed.root, "add_equipment_to_stockpile"):
            type_id = get_scalar(grant, "type")
            amount = get_scalar(grant, "amount")
            if type_id and type_id not in defined_equipment_ids:
                unknown_equipment_type_references.append({
                    "type": type_id, "action": "add_equipment_to_stockpile",
                    "variant": get_scalar(grant, "variant_name"), "path": str(path), "line": grant.line,
                })
            if amount is not None:
                number = numeric_value(amount)
                if number is None or number <= 0:
                    invalid_stockpile_amounts.append({
                        "amount": amount, "type": type_id, "path": str(path), "line": grant.line,
                    })
            stockpile_grants.append({
                "type": type_id,
                "amount": amount,
                "variant_name": get_scalar(grant, "variant_name"),
                "producer": get_scalar(grant, "producer"),
                "path": str(path), "line": grant.line,
            })

    missing_local_mio_references, external_mio_references = [], []
    for item in mio_references:
        if item["mio"] in defined_mio_ids:
            continue
        match = re.match(r"^([A-Z]{3})_", item["mio"])
        candidate = dict(item)
        if match and match.group(1) in country_tags:
            missing_local_mio_references.append(candidate)
        else:
            external_mio_references.append(candidate)

    local_equipment_localisation_candidates = []
    for item in equipment_definitions:
        match = re.match(r"^([A-Z]{3})_", item["id"])
        if match and match.group(1) in country_tags and item["id"] not in loc_index:
            local_equipment_localisation_candidates.append(item)

    return {
        "counts": {
            "mio_files": len(mio_files), "mio_definitions": len(mio_definitions),
            "mio_references": len(mio_references), "equipment_files": len(equipment_files),
            "equipment_ids": len(equipment_definitions), "module_files": len(module_files),
            "module_ids": len(module_ids), "technology_files": len(technology_files),
            "technology_ids": len(technology_ids),
            "equipment_unlock_references": len(equipment_unlock_references),
            "equipment_variants": len(variant_definitions),
            "stockpile_grants": len(stockpile_grants),
        },
        "mio_parse_errors": mio_parse_errors,
        "equipment_parse_errors": equipment_parse_errors,
        "module_parse_errors": module_parse_errors,
        "technology_parse_errors": technology_parse_errors,
        "duplicate_mio_ids": duplicate_mio_ids,
        "missing_local_mio_references": missing_local_mio_references,
        "external_mio_references": external_mio_references,
        "missing_local_mio_name_localisation": local_missing_mio_names,
        "external_mio_name_localisation_candidates": external_missing_mio_names,
        "duplicate_mio_name_keys": duplicate_mio_name_keys,
        "mio_name_matches_other_mio": mio_name_matches_other_mio,
        "local_mio_visibility_focus_candidates": local_mio_visibility_focus_candidates,
        "duplicate_equipment_ids": duplicate_equipment_ids,
        "unknown_equipment_type_references": unknown_equipment_type_references,
        "unknown_module_references": unknown_module_references,
        "unknown_technology_references": unknown_technology_references,
        "equipment_unlock_references": equipment_unlock_references,
        "invalid_stockpile_amounts": invalid_stockpile_amounts,
        "local_equipment_localisation_candidates": local_equipment_localisation_candidates,
        "mio_definitions": mio_definitions,
        "equipment_variants": variant_definitions,
        "stockpile_grants": stockpile_grants,
    }
