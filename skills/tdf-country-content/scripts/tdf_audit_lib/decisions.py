"""Аудит решений: категории, стоимость, условия, ссылки.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator, List, Optional, Sequence
from .core import (
    Block,
    Entry,
    Token,
    _structural_signature,
    direct_entries,
    find_named_blocks,
    get_block,
    get_scalar,
    iter_event_calls,
    iter_files,
    nested_entries,
    parse_hoi,
    read,
    scalar,
    walk_entries,
)
from .indexes import (
    idea_candidates,
)


DECISION_CATEGORY_FIELDS = frozenset({
    "allowed", "visible", "potential", "priority", "icon", "picture", "name", "desc",
    "visible_when_empty", "collapse", "scripted_gui", "on_map_mode", "background", "decision_icon",
})


DECISION_REF_KEYS = frozenset({"has_decision", "has_completed_decision", "has_taken_decision", "has_activated_decision"})


FLAG_READ_KEYS = frozenset({"has_country_flag", "has_global_flag"})


FLAG_WRITE_KEYS = frozenset({"set_country_flag", "clr_country_flag", "set_global_flag", "clr_global_flag"})


def decision_owner_tag(path: Path, countries) -> Optional[str]:
    stem = path.stem.lower()
    for tag, country in countries.items():
        tree_name = country["tree"].name
        suffix = "_Focus_Tree.txt"
        tree_stem = tree_name[:-len(suffix)] if tree_name.endswith(suffix) else Path(tree_name).stem
        if tree_stem.lower() == stem:
            return tag
    return None


def decision_reference_value(entry: Entry) -> Optional[str]:
    if isinstance(entry.value, Token):
        return entry.value.value
    for key in ("decision", "id", "name", "flag"):
        value = get_scalar(entry.value, key)
        if value:
            return value
    return None


def iter_named_script_refs(block: Block, commands) -> Iterator[str]:
    for entry in walk_entries(block):
        if entry.key.value in commands:
            value = decision_reference_value(entry)
            if value:
                yield value


def decision_tooltip_keys(block: Block) -> List[str]:
    found = []
    for entry in walk_entries(block):
        key = entry.key.value
        if key == "custom_cost_text":
            value = scalar(entry)
            if value:
                found.append(value)
        elif key == "custom_effect_tooltip":
            value = scalar(entry)
            if value:
                found.append(value)
            elif isinstance(entry.value, Block):
                for nested in walk_entries(entry.value):
                    if nested.key.value in ("localization_key", "tooltip") and scalar(nested):
                        found.append(scalar(nested))
        elif key == "custom_trigger_tooltip" and isinstance(entry.value, Block):
            for nested in walk_entries(entry.value):
                if nested.key.value in ("tooltip", "localization_key") and scalar(nested):
                    found.append(scalar(nested))
    return found


def decision_gate_atoms(block: Block):
    """Collect only mandatory, simple predicates from a decision visibility gate.

    AND is flattened; OR branches and compound negation are deliberately skipped.
    The result is evidence for a WARN-only review, not a full logic solver.
    """
    atoms = []
    logical_keys = {"AND", "OR", "NOT", "NOR"}

    def add_atom(entry: Entry, polarity: bool):
        if isinstance(entry.value, Token):
            label = "{} = {}".format(entry.key.value, entry.value.value)
        else:
            label = "{} = {{ … }}".format(entry.key.value)
        atoms.append({
            "signature": (entry.key.value, _structural_signature(entry.value)),
            "predicate": label,
            "polarity": bool(polarity),
            "line": entry.line,
        })

    def visit(container: Block, polarity: bool):
        for entry in container.entries:
            key = entry.key.value
            value = entry.value
            if key == "AND" and isinstance(value, Block):
                visit(value, polarity)
            elif key == "OR" and isinstance(value, Block):
                # No child of OR is individually mandatory.
                continue
            elif key == "NOT" and isinstance(value, Block):
                children = value.entries
                if len(children) == 1 and children[0].key.value not in logical_keys:
                    add_atom(children[0], not polarity)
                # Compound NOT is intentionally left for manual review.
            elif key == "NOR" and isinstance(value, Block):
                # Every simple child of NOR must be false. Compound children are skipped.
                for child in value.entries:
                    if child.key.value not in logical_keys:
                        add_atom(child, not polarity)
            else:
                add_atom(entry, polarity)

    visit(block, True)
    return atoms


def numeric_value(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def custom_cost_text_is_requirement(custom_text: Optional[str], loc_index) -> bool:
    """Recognize obvious threshold/eligibility labels that do not claim a debit."""
    if not custom_text:
        return False
    key = custom_text.lower()
    requirement_key_patterns = (
        "more_than", "greater_than", "at_least", "minimum",
    )
    if any(pattern in key for pattern in requirement_key_patterns):
        return True
    values = [item.value for item in loc_index.get(custom_text, [])]
    text = " ".join(values).lower()
    requirement_phrases = (
        "at least", "more than", "greater than", "minimum of",
        "requires at least", "must have at least", "need at least",
    )
    return any(phrase in text for phrase in requirement_phrases)


def has_obvious_manual_cost_debit(effect_blocks: Sequence[Optional[Block]]) -> bool:
    entries = []
    for block in effect_blocks:
        if block is not None:
            entries.extend(list(walk_entries(block)))
    for entry in entries:
        if entry.key.value in ("subtract_from_variable", "subtract_from_array"):
            return True
        if entry.key.value in ("add_political_power", "add_command_power", "add_army_experience",
                               "add_navy_experience", "add_air_experience"):
            value = numeric_value(scalar(entry))
            if value is not None and value < 0:
                return True
        if entry.key.value in ("add_to_variable", "add_to_array", "add_equipment_to_stockpile", "add_resource"):
            if isinstance(entry.value, Block):
                amount_entries = direct_entries(entry.value, "amount") + direct_entries(entry.value, "value")
                if any((numeric_value(scalar(item)) or 0) < 0 for item in amount_entries):
                    return True
    has_treasury_modifier = any(entry.key.value == "modify_treasury_effect" for entry in entries)
    if has_treasury_modifier:
        for entry in entries:
            if entry.key.value == "set_temp_variable" and isinstance(entry.value, Block):
                for variable in entry.value.entries:
                    if variable.key.value == "treasury_change":
                        value = numeric_value(scalar(variable))
                        if value is not None and value < 0:
                            return True
    return False


def technology_unlock_values(entry: Entry) -> List[str]:
    """Read direct token-list values from enable_equipments/module unlock fields."""
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    return [
        item.value for item in entry.value.items
        if isinstance(item, Token) and item.value.lower() not in ("no", "none", "empty")
    ]


def collect_state_inventory(mod: Path):
    state_dirs = (mod / "history" / "states", mod / "common" / "history" / "states")
    files = []
    for directory in state_dirs:
        files.extend(iter_files(directory, ".txt"))
    state_ids = set()
    for path in sorted(set(files)):
        parsed = parse_hoi(read(path))
        blocks = find_named_blocks(parsed.root, "state") or [parsed.root]
        for block in blocks:
            for entry in direct_entries(block, "id"):
                value = scalar(entry)
                if value and value.isdigit():
                    state_ids.add(int(value))
    return bool(files), state_ids


def build_decision_audit(repo, countries, loc_index, all_focus, defined_events,
                         defined_namespaces, event_parsed, content_indexes):
    mod = Path(repo) / "mdredux"
    decision_files = iter_files(mod / "common" / "decisions", ".txt")
    categories, decisions, parsed_by_path, parse_errors = [], [], {}, []

    for path in decision_files:
        parsed = parse_hoi(read(path))
        parsed_by_path[path] = parsed
        for issue in parsed.issues:
            parse_errors.append("{}:{}".format(path, issue))
        owner_tag = decision_owner_tag(path, countries)
        for category_entry in parsed.root.entries:
            if not isinstance(category_entry, Entry) or not isinstance(category_entry.value, Block):
                continue
            category_id = category_entry.key.value
            category_block = category_entry.value
            categories.append({
                "id": category_id, "path": str(path), "line": category_entry.line,
                "block": category_block, "owner_tag": owner_tag,
                "has_allowed": bool(direct_entries(category_block, "allowed")),
                "has_visible": bool(direct_entries(category_block, "visible")),
                "has_priority": bool(direct_entries(category_block, "priority")),
            })
            for decision_entry in category_block.entries:
                if not isinstance(decision_entry.value, Block) or decision_entry.key.value in DECISION_CATEGORY_FIELDS:
                    continue
                block = decision_entry.value
                decisions.append({
                    "id": decision_entry.key.value, "category": category_id,
                    "category_line": category_entry.line,
                    "path": str(path), "line": decision_entry.line, "block": block,
                    "owner_tag": owner_tag,
                    "category_has_allowed": bool(direct_entries(category_block, "allowed")),
                    "category_has_visible": bool(direct_entries(category_block, "visible")),
                    "cost": get_scalar(block, "cost"),
                    "days_remove": get_scalar(block, "days_remove"),
                    "days_re_enable": get_scalar(block, "days_re_enable"),
                    "fire_only_once": (get_scalar(block, "fire_only_once") or "").lower() in ("yes", "true", "1"),
                    "has_visible": bool(direct_entries(block, "visible")),
                    "has_available": bool(direct_entries(block, "available")),
                    "has_activation": bool(direct_entries(block, "activation")),
                    "days_mission_timeout": get_scalar(block, "days_mission_timeout"),
                    "has_allowed": bool(direct_entries(block, "allowed")),
                    "has_ai_will_do": bool(direct_entries(block, "ai_will_do")),
                    "has_complete_effect": bool(direct_entries(block, "complete_effect")),
                    "has_remove_effect": bool(direct_entries(block, "remove_effect")),
                    "has_modifier": bool(direct_entries(block, "modifier") or direct_entries(block, "targeted_modifier")),
                    "target_array": get_scalar(block, "target_array"),
                })

    category_groups = defaultdict(list)
    for item in categories:
        category_groups[item["id"]].append(item)
    duplicate_categories = [
        {
            "id": key,
            "scope": "same_file" if len({x["path"] for x in values}) == 1 else "multiple_files",
            "definitions": [{"path": x["path"], "line": x["line"]} for x in values],
        }
        for key, values in sorted(category_groups.items()) if len(values) > 1
    ]

    decision_groups = defaultdict(list)
    for item in decisions:
        decision_groups[item["id"]].append(item)
    duplicate_decisions = [
        {"id": key, "definitions": [
            {"category": x["category"], "path": x["path"], "line": x["line"]} for x in values
        ]}
        for key, values in sorted(decision_groups.items()) if len(values) > 1
    ]
    defined_decisions = set(decision_groups)

    missing_category_loc, missing_decision_loc, duplicate_loc_keys = [], [], []
    missing_tooltip_loc, external_tooltip_loc = [], []
    missing_decision_refs, external_decision_refs = [], []
    missing_focus_refs, external_focus_refs = [], []
    missing_event_refs, external_event_refs = [], []
    idea_reference_candidates, flag_reference_candidates, missing_scripted_loc = [], [], []
    invalid_numeric_fields, custom_cost_pair_issues, custom_cost_conflicts = [], [], []
    custom_cost_without_debit, custom_cost_gate_only_candidates = [], []
    repeatability_warnings, empty_effect_warnings = [], []
    nonnumeric_highlight_states, unknown_highlight_states, highlight_state_refs = [], [], []
    decision_conditions = []
    mission_gate_review_candidates = []
    decision_gate_conflicts = []

    idea_index = (content_indexes or {}).get("idea_ids", {})
    script_defs = (content_indexes or {}).get("scripted_defs", {})
    script_names = {tag: {item["name"] for item in values} for tag, values in script_defs.items()}
    script_ref_re = re.compile(r"\[([A-Z]{3}_[A-Za-z0-9_]+)\]")

    for category in categories:
        key = category["id"]
        if key not in loc_index:
            missing_category_loc.append({"category": key, "path": category["path"], "line": category["line"]})
        elif len(loc_index[key]) > 1:
            duplicate_loc_keys.append({
                "key": key, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[key]],
            })

    for decision in decisions:
        decision_id, owner_tag, block = decision["id"], decision["owner_tag"], decision["block"]
        if decision_id not in loc_index:
            missing_decision_loc.append({
                "decision": decision_id, "category": decision["category"],
                "path": decision["path"], "line": decision["line"],
            })
        elif len(loc_index[decision_id]) > 1:
            duplicate_loc_keys.append({
                "key": decision_id, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[decision_id]],
            })

        # Decision _desc keys are optional in this TDF slice; duplicate definitions are not.
        desc_key = decision_id + "_desc"
        if len(loc_index.get(desc_key, [])) > 1:
            duplicate_loc_keys.append({
                "key": desc_key, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[desc_key]],
            })

        tooltip_keys = decision_tooltip_keys(block)
        for key in tooltip_keys:
            if key not in loc_index:
                item = {"key": key, "decision": decision_id, "path": decision["path"], "line": decision["line"]}
                (missing_tooltip_loc if owner_tag and key.startswith(owner_tag + "_") else external_tooltip_loc).append(item)
            elif len(loc_index[key]) > 1:
                duplicate_loc_keys.append({
                    "key": key, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[key]],
                })

        keys_to_scan = [decision_id, desc_key, decision["category"], decision["category"] + "_desc"] + tooltip_keys
        for loc_key in keys_to_scan:
            for occurrence in loc_index.get(loc_key, []):
                for name in script_ref_re.findall(occurrence.value):
                    tag = name[:3]
                    if tag in countries and name not in script_names.get(tag, set()):
                        missing_scripted_loc.append({
                            "decision": decision_id, "localisation_key": loc_key,
                            "scripted_localisation": name, "path": occurrence.path, "line": occurrence.line,
                        })

        for entry in walk_entries(block):
            if entry.key.value in DECISION_REF_KEYS:
                target = decision_reference_value(entry)
                if target and target not in defined_decisions:
                    item = {"decision": decision_id, "target": target, "path": decision["path"],
                            "line": entry.line, "field": entry.key.value}
                    (missing_decision_refs if owner_tag and target.startswith(owner_tag + "_") else external_decision_refs).append(item)

            if entry.key.value == "has_completed_focus":
                target = scalar(entry)
                if target and target not in all_focus:
                    item = {"decision": decision_id, "target": target, "path": decision["path"], "line": entry.line}
                    (missing_focus_refs if owner_tag and target.startswith(owner_tag + "_") else external_focus_refs).append(item)

        for _, event_id, line in iter_event_calls(block):
            if event_id not in defined_events:
                namespace = event_id.split(".", 1)[0] if "." in event_id else ""
                item = {"decision": decision_id, "target": event_id, "path": decision["path"], "line": line}
                (missing_event_refs if namespace and namespace in defined_namespaces else external_event_refs).append(item)

        for idea_id in idea_candidates(block):
            match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", idea_id)
            if match:
                tag = match.group(1)
                if tag in countries and idea_id not in idea_index.get(tag, set()):
                    idea_reference_candidates.append({
                        "decision": decision_id, "idea": idea_id, "owner_tag": owner_tag,
                        "classification": "local_candidate" if tag == owner_tag else "cross_country_candidate",
                        "path": decision["path"], "line": decision["line"],
                    })

        for flag in sorted(set(iter_named_script_refs(block, FLAG_READ_KEYS))):
            if owner_tag and flag.startswith(owner_tag + "_"):
                flag_reference_candidates.append({
                    "decision": decision_id, "flag": flag, "classification": "local_candidate",
                    "path": decision["path"], "line": decision["line"],
                })

        for field in ("cost", "days_remove", "days_re_enable"):
            value = decision[field]
            if value is not None:
                number = numeric_value(value)
                invalid = number is None or (number < 0 and not (field == "days_remove" and number == -1))
                if invalid:
                    invalid_numeric_fields.append({
                        "decision": decision_id, "field": field, "value": value,
                        "path": decision["path"], "line": decision["line"],
                    })

        has_custom_trigger = bool(direct_entries(block, "custom_cost_trigger"))
        custom_text = get_scalar(block, "custom_cost_text")
        if has_custom_trigger != bool(custom_text):
            custom_cost_pair_issues.append({
                "decision": decision_id, "has_custom_cost_trigger": has_custom_trigger,
                "custom_cost_text": custom_text, "path": decision["path"], "line": decision["line"],
            })
        if has_custom_trigger and custom_text and decision["cost"] is not None:
            custom_cost_conflicts.append({"decision": decision_id, "path": decision["path"], "line": decision["line"]})
        # A trigger without custom_cost_text is not an explicit displayed price.
        # Keep the trigger/text pairing warning, but don't infer a missing debit
        # from an eligibility gate alone.
        if has_custom_trigger and custom_text:
            effects = []
            effects.extend([x.value for x in direct_entries(block, "complete_effect") if isinstance(x.value, Block)])
            effects.extend([x.value for x in direct_entries(block, "remove_effect") if isinstance(x.value, Block)])
            if not has_obvious_manual_cost_debit(effects):
                candidate = {
                    "decision": decision_id, "custom_cost_text": custom_text,
                    "path": decision["path"], "line": decision["line"],
                }
                if custom_cost_text_is_requirement(custom_text, loc_index):
                    custom_cost_gate_only_candidates.append({
                        **candidate,
                        "classification": "threshold_only_requirement",
                        "reason": (
                            "Локализация/ключ описывает минимальный порог ресурса, а не цену покупки; "
                            "отсутствие списания может быть намеренным."
                        ),
                    })
                else:
                    custom_cost_without_debit.append(candidate)

        cooldown = numeric_value(decision["days_re_enable"])
        if decision["fire_only_once"] and cooldown is not None and cooldown > 0:
            repeatability_warnings.append({
                "decision": decision_id, "reason": "fire_only_once вместе с days_re_enable",
                "days_re_enable": decision["days_re_enable"], "path": decision["path"], "line": decision["line"],
            })

        for field in ("complete_effect", "remove_effect"):
            for entry in direct_entries(block, field):
                if isinstance(entry.value, Block) and not entry.value.entries:
                    empty_effect_warnings.append({
                        "decision": decision_id, "effect": field, "path": decision["path"], "line": entry.line,
                    })

        for field in ("allowed", "visible", "available"):
            condition = get_block(block, field)
            if condition and get_scalar(condition, "always") == "no":
                condition_item = {
                    "decision": decision_id, "condition": field,
                    "reason": "always = no делает условие постоянно ложным; проверь, что это намеренно",
                    "path": decision["path"], "line": decision["line"],
                }
                if (field == "available" and decision["has_activation"]
                        and decision["days_mission_timeout"] is not None):
                    mission_gate_review_candidates.append({
                        **condition_item,
                        "classification": "non_clickable_mission_gate",
                        "reason": (
                            "У решения есть activation и days_mission_timeout: available = always no "
                            "может намеренно запрещать ручной выбор у автоматически запускаемой миссии. "
                            "Проверь activation, cancel_trigger, timeout_effect и источник активации."
                        ),
                    })
                else:
                    decision_conditions.append(condition_item)

        # Compare only mandatory atomic predicates in visible/available.
        # allowed is a separate load/startup filter and is not compared here.
        visible_atoms = []
        available_atoms = []
        for gate_entry in direct_entries(block, "visible"):
            if isinstance(gate_entry.value, Block):
                visible_atoms.extend(
                    (atom, gate_entry.line) for atom in decision_gate_atoms(gate_entry.value)
                )
        for gate_entry in direct_entries(block, "available"):
            if isinstance(gate_entry.value, Block):
                available_atoms.extend(
                    (atom, gate_entry.line) for atom in decision_gate_atoms(gate_entry.value)
                )
        seen_gate_conflicts = set()
        for visible_atom, visible_gate_line in visible_atoms:
            for available_atom, available_gate_line in available_atoms:
                if (visible_atom["signature"] != available_atom["signature"]
                        or visible_atom["polarity"] == available_atom["polarity"]):
                    continue
                conflict_key = (
                    visible_atom["signature"], visible_atom["line"], available_atom["line"],
                    visible_gate_line, available_gate_line,
                )
                if conflict_key in seen_gate_conflicts:
                    continue
                seen_gate_conflicts.add(conflict_key)
                decision_gate_conflicts.append({
                    "decision": decision_id,
                    "category": decision["category"],
                    "owner_tag": owner_tag,
                    "predicate": visible_atom["predicate"],
                    "visible_requirement": "must_be_true" if visible_atom["polarity"] else "must_be_false",
                    "available_requirement": "must_be_true" if available_atom["polarity"] else "must_be_false",
                    "visible_line": visible_atom["line"],
                    "available_line": available_atom["line"],
                    "visible_gate_line": visible_gate_line,
                    "available_gate_line": available_gate_line,
                    "path": decision["path"],
                    "line": decision["line"],
                    "classification": "warn_only_candidate",
                    "reason": (
                        "Один и тот же простой предикат обязателен в visible и available "
                        "с противоположной полярностью; проверь достижимость решения вручную."
                    ),
                })

        highlight = get_block(block, "highlight_states")
        if highlight:
            for entry in nested_entries(highlight, "state"):
                value = scalar(entry)
                item = {"decision": decision_id, "state": value, "path": decision["path"], "line": entry.line}
                if value is None or not value.isdigit():
                    nonnumeric_highlight_states.append(item)
                else:
                    highlight_state_refs.append({**item, "state": int(value)})

    flag_setters = set()
    sources = [x["tree_parsed"].root for x in countries.values()]
    sources.extend(x.root for x in event_parsed.values())
    sources.extend(x.root for x in parsed_by_path.values())
    for folder in ("scripted_effects", "on_actions"):
        for path in iter_files(mod / "common" / folder, ".txt"):
            sources.append(parse_hoi(read(path)).root)
    for path in iter_files(mod / "common" / "history" / "countries", ".txt"):
        sources.append(parse_hoi(read(path)).root)
    for source in sources:
        flag_setters.update(iter_named_script_refs(source, FLAG_WRITE_KEYS))
    for item in flag_reference_candidates:
        item["status"] = "setter_found_in_checkout" if item["flag"] in flag_setters else "setter_not_found_in_checkout"

    state_inventory_available, state_ids = collect_state_inventory(mod)
    if state_inventory_available:
        for item in highlight_state_refs:
            if item["state"] not in state_ids:
                unknown_highlight_states.append(item)

    metadata = [{key: value for key, value in item.items() if key != "block"} for item in decisions]
    return {
        "counts": {"files": len(decision_files), "categories": len(categories), "decisions": len(decisions)},
        "category_metadata": [{
            "id": item["id"], "path": item["path"], "line": item["line"],
            "owner_tag": item["owner_tag"], "has_allowed": item["has_allowed"],
            "has_visible": item["has_visible"], "has_priority": item["has_priority"],
            "decision_ids": [
                decision["id"] for decision in decisions
                if decision["category"] == item["id"]
                and decision["path"] == item["path"]
                and decision["category_line"] == item["line"]
            ],
        } for item in categories],
        "parse_errors": parse_errors, "duplicate_category_ids": duplicate_categories,
        "duplicate_decision_ids": duplicate_decisions, "missing_category_localisation": missing_category_loc,
        "missing_decision_localisation": missing_decision_loc, "duplicate_localisation_definitions": duplicate_loc_keys,
        "missing_tooltip_localisation": missing_tooltip_loc, "external_tooltip_localisation": external_tooltip_loc,
        "missing_decision_references": missing_decision_refs, "external_decision_references": external_decision_refs,
        "missing_focus_references": missing_focus_refs, "external_focus_references": external_focus_refs,
        "missing_event_references": missing_event_refs, "external_event_references": external_event_refs,
        "idea_reference_candidates": idea_reference_candidates, "flag_reference_candidates": flag_reference_candidates,
        "missing_scripted_localisation": missing_scripted_loc, "invalid_numeric_fields": invalid_numeric_fields,
        "custom_cost_pair_issues": custom_cost_pair_issues, "custom_cost_conflicts": custom_cost_conflicts,
        "custom_cost_without_debit": custom_cost_without_debit,
        "custom_cost_gate_only_candidates": custom_cost_gate_only_candidates,
        "repeatability_warnings": repeatability_warnings,
        "empty_effect_warnings": empty_effect_warnings, "condition_review_candidates": decision_conditions,
        "mission_gate_review_candidates": mission_gate_review_candidates,
        "decision_gate_conflicts": decision_gate_conflicts,
        "nonnumeric_highlight_states": nonnumeric_highlight_states, "unknown_highlight_states": unknown_highlight_states,
        "highlight_state_references": highlight_state_refs, "state_inventory_available": state_inventory_available,
        "state_inventory_count": len(state_ids), "metadata": metadata,
    }
