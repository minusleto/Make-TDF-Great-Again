"""Аудит потока флагов, переменных, массивов и scripted effects.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Optional, Sequence
from .core import (
    Block,
    Entry,
    Token,
    _state_flow_script_files,
    direct_entries,
    find_named_blocks,
    get_block,
    get_scalar,
    iter_event_calls,
    iter_files,
    parse_hoi,
    read,
    scalar,
    walk_entries,
)
from .decisions import (
    DECISION_CATEGORY_FIELDS,
    numeric_value,
)


STATE_FLOW_FLAG_READ_KEYS = frozenset({
    "has_country_flag", "has_global_flag", "has_state_flag", "has_province_flag",
})


STATE_FLOW_FLAG_WRITE_KEYS = frozenset({
    "set_country_flag", "clr_country_flag", "set_global_flag", "clr_global_flag",
    "set_state_flag", "clr_state_flag", "set_province_flag", "clr_province_flag",
    "set_timed_country_flag", "set_timed_global_flag",
    "set_timed_state_flag", "set_timed_province_flag",
})


STATE_FLOW_VARIABLE_WRITE_KEYS = frozenset({
    "set_variable", "set_temp_variable", "add_to_variable", "subtract_from_variable",
    "multiply_variable", "divide_variable", "clamp_variable", "modulo_variable",
})


STATE_FLOW_VARIABLE_READ_KEYS = frozenset({"check_variable", "compare_variables"})


STATE_FLOW_ARRAY_WRITE_KEYS = frozenset({"add_to_array", "remove_from_array", "clear_array"})


STATE_FLOW_ARRAY_READ_KEYS = frozenset({
    "any_of_scopes", "all_of_scopes", "random_scope_in_array", "for_each_scope_loop",
})


STATE_FLOW_FLAG_SCOPE = {
    "set_country_flag": "country", "clr_country_flag": "country",
    "set_global_flag": "global", "clr_global_flag": "global",
    "set_state_flag": "state", "clr_state_flag": "state",
    "set_province_flag": "province", "clr_province_flag": "province",
    "set_timed_country_flag": "country_timed", "set_timed_global_flag": "global_timed",
    "set_timed_state_flag": "state_timed", "set_timed_province_flag": "province_timed",
}


STATE_FLOW_FLAG_READ_SCOPE = {
    "has_country_flag": "country", "has_global_flag": "global",
    "has_state_flag": "state", "has_province_flag": "province",
}


STATE_FLOW_IDEA_READ_KEYS = frozenset({"has_idea", "has_ideas"})


STATE_FLOW_IDEA_WRITE_KEYS = frozenset({"add_ideas", "add_idea", "add_timed_idea"})


STATE_FLOW_VARIABLE_META_KEYS = frozenset({
    "var", "variable", "value", "value_add", "days", "operation", "type",
    "round", "abs", "clamp", "min", "max",
})


STATE_FLOW_ARRAY_META_KEYS = frozenset({
    "array", "source_array", "target_array", "value", "amount", "count",
    "index", "position", "scope",
})


def _state_flow_source_kind(path: Path, mod: Path) -> str:
    try:
        parts = path.relative_to(mod).parts
    except ValueError:
        parts = path.parts
    if "national_focus" in parts:
        return "focus"
    if "decisions" in parts:
        return "decision"
    if "events" in parts:
        return "event"
    if "ideas" in parts:
        return "idea"
    if "scripted_effects" in parts:
        return "scripted_effect"
    if "scripted_triggers" in parts:
        return "scripted_trigger"
    if "on_actions" in parts:
        return "on_action"
    if "history" in parts and "countries" in parts:
        return "history"
    return "common"


def _state_flow_owner_tag(path: Path, countries) -> Optional[str]:
    stem = path.stem.lower()
    for tag, country in countries.items():
        tree_name = country["tree"].name
        suffix = "_Focus_Tree.txt"
        tree_stem = tree_name[:-len(suffix)] if tree_name.endswith(suffix) else Path(tree_name).stem
        if stem == tree_stem.lower() or stem.startswith(tag.lower() + "_"):
            return tag
        if stem.startswith(tag.lower() + " ") or stem.startswith(tag.lower() + " -"):
            return tag
    match = re.match(r"^([A-Z]{3})(?:\s*[-_ ]|$)", path.name)
    if match and match.group(1) in countries:
        return match.group(1)
    return None


def _state_flow_named_value(entry: Entry, aliases: Sequence[str]) -> Optional[str]:
    if isinstance(entry.value, Token):
        return entry.value.value
    if not isinstance(entry.value, Block):
        return None
    for alias in aliases:
        value = get_scalar(entry.value, alias)
        if value:
            return value
    return None


def _state_flow_variable_names(entry: Entry) -> List[str]:
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    if entry.key.value == "compare_variables":
        values = [get_scalar(entry.value, key) for key in ("var1", "var2", "variable1", "variable2")]
        return [value for value in values if value]
    for alias in ("var", "variable"):
        value = get_scalar(entry.value, alias)
        if value:
            return [value]
    for child in entry.value.entries:
        if child.key.value not in STATE_FLOW_VARIABLE_META_KEYS and isinstance(child.value, Token):
            return [child.key.value]
    # Also accept bare comparison syntax: check_variable = { treasury > 5 }.
    for item in entry.value.items:
        if isinstance(item, Token):
            value = item.value
            if value not in (">", "<", ">=", "<=", "=", "==", "!=") and numeric_value(value) is None:
                return [value]
    return []


def _state_flow_array_name(entry: Entry) -> Optional[str]:
    if isinstance(entry.value, Token):
        return entry.value.value
    if not isinstance(entry.value, Block):
        return None
    for alias in ("array", "source_array", "target_array"):
        value = get_scalar(entry.value, alias)
        if value:
            return value
    for child in entry.value.entries:
        if child.key.value not in STATE_FLOW_ARRAY_META_KEYS and isinstance(child.value, Token):
            return child.key.value
    return None


def _state_flow_symbol_tag(symbol: str, country_tags) -> Optional[str]:
    normalized = re.sub(r"^(?:global|ROOT|FROM|PREV|THIS)\.", "", symbol)
    match = re.match(r"^([A-Z]{3})(?:_|\.|$)", normalized)
    if match and match.group(1) in country_tags:
        return match.group(1)
    return None


def _state_flow_relative(path: Path, mod: Path) -> str:
    try:
        return path.relative_to(mod).as_posix()
    except ValueError:
        return path.as_posix()


def _state_flow_entries_with_depth(block: Block, depth: int = 0):
    for item in block.items:
        if isinstance(item, Entry):
            yield item, depth
            if isinstance(item.value, Block):
                yield from _state_flow_entries_with_depth(item.value, depth + 1)


def _state_flow_effect_values(entry: Entry) -> List[str]:
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    values = [item.value for item in entry.value.items if isinstance(item, Token)]
    for child in entry.value.entries:
        if child.key.value in ("idea", "add_idea") and scalar(child):
            values.append(scalar(child))
    return values


def _state_flow_entries_with_polarity(block: Block, negated: bool = False):
    """Walk entries while marking conditions nested under NOT/NOR as negative."""
    for item in block.items:
        if not isinstance(item, Entry):
            continue
        yield item, negated
        if isinstance(item.value, Block):
            child_negated = negated or item.key.value.upper() in ("NOT", "NOR")
            yield from _state_flow_entries_with_polarity(item.value, child_negated)


def _state_flow_idea_values(entry: Entry) -> List[str]:
    """Read static idea IDs from scalar, block and list-style idea commands."""
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    values = [
        scalar(child) for child in entry.value.entries
        if child.key.value in ("idea", "add_idea", "has_idea") and scalar(child)
    ]
    if not values:
        values = [item.value for item in entry.value.items if isinstance(item, Token)]
    return list(dict.fromkeys(values))


def _state_flow_positive_state_reads(block: Block):
    for entry, negated in _state_flow_entries_with_polarity(block):
        if negated:
            continue
        command = entry.key.value
        if command in STATE_FLOW_FLAG_READ_KEYS:
            symbol = _state_flow_named_value(entry, ("flag", "name", "id"))
            if symbol:
                yield {
                    "family": "flag", "id": symbol, "command": command,
                    "scope": STATE_FLOW_FLAG_READ_SCOPE[command], "line": entry.line,
                }
        elif command in STATE_FLOW_IDEA_READ_KEYS:
            for symbol in _state_flow_idea_values(entry):
                yield {
                    "family": "idea", "id": symbol, "command": command,
                    "scope": None, "line": entry.line,
                }


def _state_flow_positive_state_writes(block: Block):
    for entry, _ in _state_flow_entries_with_polarity(block):
        command = entry.key.value
        if command in STATE_FLOW_FLAG_WRITE_KEYS and command.startswith("set_"):
            symbol = _state_flow_named_value(entry, ("flag", "name", "id"))
            if symbol:
                yield {
                    "family": "flag", "id": symbol, "command": command,
                    "scope": STATE_FLOW_FLAG_SCOPE.get(command), "line": entry.line,
                }
        elif command in STATE_FLOW_IDEA_WRITE_KEYS:
            for symbol in _state_flow_idea_values(entry):
                yield {
                    "family": "idea", "id": symbol, "command": command,
                    "scope": None, "line": entry.line,
                }


def _state_flow_flag_scope_matches(write_scope: Optional[str], read_scope: Optional[str]) -> Optional[bool]:
    if not write_scope or not read_scope:
        return None
    normalized_write = write_scope.replace("_timed", "")
    return normalized_write == read_scope


def build_state_flow_audit(repo, countries, event_parsed=None):
    """Build a conservative cross-file map of flags, variables, arrays and script hooks."""
    mod = Path(repo) / "mdredux"
    common_dir = mod / "common"
    country_tags = set(countries)

    history_dirs = (
        mod / "history" / "countries",
        common_dir / "history" / "countries",
    )
    history_files = sorted({
        path for directory in history_dirs for path in iter_files(directory, ".txt")
    })
    script_folders = ("scripted_effects", "scripted_triggers", "on_actions")
    script_files = {
        folder: _state_flow_script_files(common_dir / folder)
        for folder in script_folders
    }

    source_paths = set(iter_files(common_dir, ".txt"))
    source_paths.update(iter_files(mod / "events", ".txt"))
    source_paths.update(history_files)
    for paths in script_files.values():
        source_paths.update(paths)

    parsed_sources = {}
    for path in sorted(source_paths, key=lambda item: str(item)):
        if event_parsed and path in event_parsed:
            parsed_sources[path] = event_parsed[path]
        else:
            parsed_sources[path] = parse_hoi(read(path))

    source_meta = {}
    parse_errors = []
    for path, parsed in parsed_sources.items():
        owner_tag = _state_flow_owner_tag(path, countries)
        source_meta[path] = {
            "kind": _state_flow_source_kind(path, mod),
            "owner_tag": owner_tag,
            "display_path": _state_flow_relative(path, mod),
        }
        for issue in parsed.issues:
            parse_errors.append({
                "path": source_meta[path]["display_path"],
                "line": issue.line,
                "message": issue.message,
            })

    script_definition_indexes = {}
    script_definition_locations = set()
    script_parse_errors = []
    for folder, wrapper in (
        ("scripted_effects", "scripted_effects"),
        ("scripted_triggers", "scripted_triggers"),
    ):
        definitions = []
        for path in script_files[folder]:
            parsed = parsed_sources[path]
            containers = [
                entry.value for entry in direct_entries(parsed.root, wrapper)
                if isinstance(entry.value, Block)
            ] or [parsed.root]
            for container in containers:
                for entry in container.entries:
                    if isinstance(entry.value, Block):
                        item = {
                            "id": entry.key.value,
                            "path": _state_flow_relative(path, mod),
                            "line": entry.line,
                        }
                        definitions.append(item)
                        script_definition_locations.add((path, entry.line, entry.key.value, folder))
            for issue in parsed.issues:
                script_parse_errors.append({
                    "path": _state_flow_relative(path, mod),
                    "line": issue.line,
                    "message": issue.message,
                })
        script_definition_indexes[folder] = definitions

    effect_groups = defaultdict(list)
    trigger_groups = defaultdict(list)
    for item in script_definition_indexes["scripted_effects"]:
        effect_groups[item["id"]].append(item)
    for item in script_definition_indexes["scripted_triggers"]:
        trigger_groups[item["id"]].append(item)
    effect_ids, trigger_ids = set(effect_groups), set(trigger_groups)

    duplicate_effects = [
        {"id": key, "definitions": values}
        for key, values in sorted(effect_groups.items()) if len(values) > 1
    ]
    duplicate_triggers = [
        {"id": key, "definitions": values}
        for key, values in sorted(trigger_groups.items()) if len(values) > 1
    ]

    effect_calls, trigger_calls, unresolved_script_calls = [], [], []
    for path, parsed in parsed_sources.items():
        rel = source_meta.get(path, {}).get("display_path", _state_flow_relative(path, mod))
        for entry, _depth in _state_flow_entries_with_depth(parsed.root):
            key = entry.key.value
            if key in effect_ids and (path, entry.line, key, "scripted_effects") not in script_definition_locations:
                effect_calls.append({"scripted_effect": key, "path": rel, "line": entry.line})
            if key in trigger_ids and (path, entry.line, key, "scripted_triggers") not in script_definition_locations:
                trigger_calls.append({"scripted_trigger": key, "path": rel, "line": entry.line})
            if (key not in effect_ids and key not in trigger_ids
                    and isinstance(entry.value, Token)
                    and entry.value.value.lower() in ("yes", "no")):
                match = re.match(r"^([A-Z]{3,5})_[A-Za-z0-9_]+$", key)
                if match:
                    tag = match.group(1)
                    unresolved_script_calls.append({
                        "candidate": key,
                        "classification": "local_definition_not_found_candidate" if tag in country_tags
                                          else "external_or_unknown_dependency",
                        "tag": tag,
                        "path": rel,
                        "line": entry.line,
                        "owner_tag": source_meta.get(path, {}).get("owner_tag"),
                    })

    unresolved_script_calls.sort(key=lambda item: (item["candidate"], item["path"], item["line"]))
    deduped_unresolved, seen_unresolved = [], set()
    for item in unresolved_script_calls:
        marker = (item["candidate"], item["path"], item["line"])
        if marker not in seen_unresolved:
            seen_unresolved.add(marker)
            deduped_unresolved.append(item)

    effect_call_counts = Counter(item["scripted_effect"] for item in effect_calls)
    trigger_call_counts = Counter(item["scripted_trigger"] for item in trigger_calls)
    unreferenced_effects = [
        {**item, "status": "no_local_call_found"}
        for item in script_definition_indexes["scripted_effects"]
        if not effect_call_counts[item["id"]]
    ]
    unreferenced_triggers = [
        {**item, "status": "no_local_call_found"}
        for item in script_definition_indexes["scripted_triggers"]
        if not trigger_call_counts[item["id"]]
    ]

    flag_records = defaultdict(lambda: {"reads": [], "writes": [], "scopes": set()})
    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        for entry in walk_entries(parsed.root):
            key = entry.key.value
            if key in STATE_FLOW_FLAG_READ_KEYS:
                flag = _state_flow_named_value(entry, ("flag", "name", "id"))
                usage = "read"
            elif key in STATE_FLOW_FLAG_WRITE_KEYS:
                flag = _state_flow_named_value(entry, ("flag", "name", "id"))
                usage = "write"
            else:
                continue
            if not flag or flag.lower() in ("no", "none", "empty"):
                continue
            item = {
                "command": key, "path": rel, "line": entry.line,
                "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
            }
            flag_records[flag]["scopes"].add(STATE_FLOW_FLAG_SCOPE.get(key, key.replace("has_", "")))
            flag_records[flag]["reads" if usage == "read" else "writes"].append(item)

    flag_symbols, potentially_unread_flags, flags_read_without_local_writer = [], [], []
    for flag, record in sorted(flag_records.items()):
        local_tag = _state_flow_symbol_tag(flag, country_tags)
        if not local_tag:
            continue
        item = {
            "id": flag, "local_tag": local_tag, "scopes": sorted(record["scopes"]),
            "read_count": len(record["reads"]), "write_count": len(record["writes"]),
            "reads": record["reads"][:20], "writes": record["writes"][:20],
        }
        flag_symbols.append(item)
        if record["writes"] and not record["reads"]:
            potentially_unread_flags.append({
                "flag": flag, "tag": local_tag, "writes": record["writes"][:10],
                "status": "no_reader_in_available_checkout_external_reader_possible",
            })
        elif record["reads"] and not record["writes"]:
            flags_read_without_local_writer.append({
                "flag": flag, "tag": local_tag, "reads": record["reads"][:10],
                "status": "no_writer_in_available_checkout_external_initialisation_possible",
            })

    variable_records = defaultdict(lambda: {"reads": [], "writes": [], "operations": set()})
    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        for entry in walk_entries(parsed.root):
            command = entry.key.value
            if command in STATE_FLOW_VARIABLE_WRITE_KEYS:
                names = _state_flow_variable_names(entry)
                for variable in names:
                    record = variable_records[variable]
                    record["writes"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })
                    record["operations"].add(command)
                    if command in ("add_to_variable", "subtract_from_variable", "multiply_variable",
                                   "divide_variable", "clamp_variable", "modulo_variable"):
                        record["reads"].append({
                            "command": command, "path": rel, "line": entry.line,
                            "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                        })
            elif command in STATE_FLOW_VARIABLE_READ_KEYS:
                for variable in _state_flow_variable_names(entry):
                    variable_records[variable]["reads"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })
        for entry in walk_entries(parsed.root):
            value = scalar(entry)
            if not value:
                continue
            for match in re.finditer(r"\b(?:var|global_var):([A-Za-z0-9_.^]+)", value):
                variable = match.group(1)
                variable_records[variable]["reads"].append({
                    "command": "variable_expression", "path": rel, "line": entry.line,
                    "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                })

    variable_symbols, potentially_unread_variables, variables_read_without_local_writer = [], [], []
    for variable, record in sorted(variable_records.items()):
        local_tag = _state_flow_symbol_tag(variable, country_tags)
        if not local_tag:
            continue
        variable_symbols.append({
            "id": variable, "local_tag": local_tag,
            "read_count": len(record["reads"]), "write_count": len(record["writes"]),
            "operations": sorted(record["operations"]),
            "reads": record["reads"][:20], "writes": record["writes"][:20],
        })
        if record["writes"] and not record["reads"]:
            potentially_unread_variables.append({
                "variable": variable, "tag": local_tag, "writes": record["writes"][:10],
                "status": "no_reader_in_available_checkout_external_reader_possible",
            })
        elif record["reads"] and not record["writes"]:
            variables_read_without_local_writer.append({
                "variable": variable, "tag": local_tag, "reads": record["reads"][:10],
                "status": "no_writer_in_available_checkout_external_initialisation_possible",
            })

    array_records = defaultdict(lambda: {"reads": [], "writes": [], "operations": set()})
    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        for entry in walk_entries(parsed.root):
            command = entry.key.value
            if command in STATE_FLOW_ARRAY_WRITE_KEYS:
                array_name = _state_flow_array_name(entry)
                if array_name:
                    record = array_records[array_name]
                    record["writes"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })
                    record["operations"].add(command)
                    if command == "remove_from_array":
                        record["reads"].append({
                            "command": command, "path": rel, "line": entry.line,
                            "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                        })
            elif command in STATE_FLOW_ARRAY_READ_KEYS and isinstance(entry.value, Block):
                array_name = _state_flow_array_name(entry)
                if array_name:
                    array_records[array_name]["reads"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })

    array_symbols, potentially_unread_arrays, arrays_read_without_local_writer = [], [], []
    for array_name, record in sorted(array_records.items()):
        local_tag = _state_flow_symbol_tag(array_name, country_tags)
        if not local_tag:
            continue
        array_symbols.append({
            "id": array_name, "local_tag": local_tag,
            "read_count": len(record["reads"]), "write_count": len(record["writes"]),
            "operations": sorted(record["operations"]),
            "reads": record["reads"][:20], "writes": record["writes"][:20],
        })
        if record["writes"] and not record["reads"]:
            potentially_unread_arrays.append({
                "array": array_name, "tag": local_tag, "writes": record["writes"][:10],
                "status": "no_reader_in_available_checkout_external_reader_possible",
            })
        elif record["reads"] and not record["writes"]:
            arrays_read_without_local_writer.append({
                "array": array_name, "tag": local_tag, "reads": record["reads"][:10],
                "status": "no_writer_in_available_checkout_external_initialisation_possible",
            })

    idea_on_add_without_matching_on_remove = []
    idea_files = _state_flow_script_files(common_dir / "ideas")
    for path in idea_files:
        if path.suffix.lower() != ".txt":
            continue
        parsed = parsed_sources.get(path)
        if parsed is None:
            parsed = parse_hoi(read(path))
        for ideas_block in find_named_blocks(parsed.root, "ideas"):
            for group_name in ("country", "hidden_ideas"):
                for group_entry in direct_entries(ideas_block, group_name):
                    if not isinstance(group_entry.value, Block):
                        continue
                    for idea_entry in group_entry.value.entries:
                        if not isinstance(idea_entry.value, Block):
                            continue
                        idea_block = idea_entry.value
                        on_add = get_block(idea_block, "on_add")
                        on_remove = get_block(idea_block, "on_remove")
                        if on_add is None:
                            continue

                        def collect_mutations(effect_block):
                            found = []
                            if effect_block is None:
                                return found
                            for op_entry in walk_entries(effect_block):
                                command = op_entry.key.value
                                if command in STATE_FLOW_FLAG_WRITE_KEYS and not command.startswith("set_timed_"):
                                    symbol = _state_flow_named_value(op_entry, ("flag", "name", "id"))
                                    family = "flag"
                                elif command in STATE_FLOW_VARIABLE_WRITE_KEYS:
                                    names = _state_flow_variable_names(op_entry)
                                    symbol = names[0] if names else None
                                    family = "variable"
                                elif command in STATE_FLOW_ARRAY_WRITE_KEYS:
                                    symbol = _state_flow_array_name(op_entry)
                                    family = "array"
                                else:
                                    continue
                                if symbol:
                                    found.append({"family": family, "id": symbol, "command": command,
                                                  "line": op_entry.line})
                            return found

                        adds = collect_mutations(on_add)
                        removes = collect_mutations(on_remove)
                        inverse = {
                            "set_country_flag": "clr_country_flag", "set_global_flag": "clr_global_flag",
                            "set_state_flag": "clr_state_flag", "set_province_flag": "clr_province_flag",
                            "add_to_array": "remove_from_array", "remove_from_array": "add_to_array",
                            "add_to_variable": "subtract_from_variable", "subtract_from_variable": "add_to_variable",
                        }
                        for mutation in adds:
                            command = mutation["command"]
                            if command in inverse:
                                matched = any(
                                    item["family"] == mutation["family"] and item["id"] == mutation["id"]
                                    and item["command"] == inverse[command] for item in removes
                                )
                            elif command in ("set_variable", "set_temp_variable"):
                                matched = any(
                                    item["family"] == "variable" and item["id"] == mutation["id"]
                                    and item["command"] in ("set_variable", "set_temp_variable")
                                    for item in removes
                                )
                            else:
                                matched = True
                            if not matched:
                                idea_on_add_without_matching_on_remove.append({
                                    "idea": idea_entry.key.value, "family": mutation["family"],
                                    "id": mutation["id"], "on_add_command": command,
                                    "path": _state_flow_relative(path, mod),
                                    "line": mutation["line"],
                                    "status": "manual_review_one_sided_state_change",
                                })

    # Link direct flag/idea writes in decision and event effects to positive gates
    # in other objects. This graph is diagnostic evidence, not runtime proof.
    state_writers = defaultdict(list)
    state_readers = defaultdict(list)

    def register_state_refs(bucket, extractor, block, metadata, object_key):
        for item in extractor(block):
            local_tag = _state_flow_symbol_tag(item["id"], country_tags)
            if not local_tag:
                continue
            bucket[(item["family"], item["id"])].append({
                **item, **metadata, "object_key": object_key, "local_tag": local_tag,
            })

    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        if meta["kind"] == "decision":
            for category_entry in parsed.root.entries:
                if not isinstance(category_entry, Entry) or not isinstance(category_entry.value, Block):
                    continue
                category_id = category_entry.key.value
                category_block = category_entry.value
                for gate in ("potential", "allowed", "visible"):
                    for gate_entry in direct_entries(category_block, gate):
                        if isinstance(gate_entry.value, Block):
                            key = "decision_category|{}|{}|{}".format(rel, category_id, gate)
                            register_state_refs(
                                state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                {"object_kind": "decision_category", "object_id": category_id,
                                 "category": category_id, "gate": gate, "path": rel,
                                 "owner_tag": meta["owner_tag"]},
                                key,
                            )
                for decision_entry in category_block.entries:
                    if (not isinstance(decision_entry, Entry)
                            or not isinstance(decision_entry.value, Block)
                            or decision_entry.key.value in DECISION_CATEGORY_FIELDS):
                        continue
                    decision_id = decision_entry.key.value
                    decision_block = decision_entry.value
                    for gate in ("visible", "available", "allowed", "activation"):
                        for gate_entry in direct_entries(decision_block, gate):
                            if isinstance(gate_entry.value, Block):
                                key = "decision|{}|{}|{}|{}".format(rel, category_id, decision_id, gate)
                                register_state_refs(
                                    state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                    {"object_kind": "decision", "object_id": decision_id,
                                     "category": category_id, "gate": gate, "path": rel,
                                     "owner_tag": meta["owner_tag"]},
                                    key,
                                )
                    for effect in ("complete_effect", "remove_effect", "timeout_effect", "cancel_effect"):
                        for effect_entry in direct_entries(decision_block, effect):
                            if isinstance(effect_entry.value, Block):
                                key = "decision|{}|{}|{}|{}".format(rel, category_id, decision_id, effect)
                                register_state_refs(
                                    state_writers, _state_flow_positive_state_writes, effect_entry.value,
                                    {"object_kind": "decision", "object_id": decision_id,
                                     "category": category_id, "effect": effect, "path": rel,
                                     "owner_tag": meta["owner_tag"]},
                                    key,
                                )
        elif meta["kind"] == "event":
            for event_kind in ("country_event", "news_event"):
                for event_entry in direct_entries(parsed.root, event_kind):
                    if not isinstance(event_entry.value, Block):
                        continue
                    event_block = event_entry.value
                    event_id = get_scalar(event_block, "id")
                    if not event_id:
                        continue
                    for gate_entry in direct_entries(event_block, "trigger"):
                        if isinstance(gate_entry.value, Block):
                            key = "event|{}|{}|trigger".format(rel, event_id)
                            register_state_refs(
                                state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                {"object_kind": "event", "object_id": event_id,
                                 "gate": "trigger", "path": rel,
                                 "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                                key,
                            )
                    for immediate_entry in direct_entries(event_block, "immediate"):
                        if isinstance(immediate_entry.value, Block):
                            key = "event|{}|{}|immediate".format(rel, event_id)
                            register_state_refs(
                                state_writers, _state_flow_positive_state_writes, immediate_entry.value,
                                {"object_kind": "event", "object_id": event_id,
                                 "effect": "immediate", "path": rel,
                                 "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                                key,
                            )
                    for option_entry in direct_entries(event_block, "option"):
                        if not isinstance(option_entry.value, Block):
                            continue
                        option_name = get_scalar(option_entry.value, "name") or "(unnamed option)"
                        for gate_entry in direct_entries(option_entry.value, "trigger"):
                            if isinstance(gate_entry.value, Block):
                                key = "event_option|{}|{}|{}|trigger".format(rel, event_id, option_name)
                                register_state_refs(
                                    state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                    {"object_kind": "event_option", "object_id": event_id,
                                     "option": option_name, "gate": "trigger", "path": rel,
                                     "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                                    key,
                                )
                        key = "event_option|{}|{}|{}|effect".format(rel, event_id, option_name)
                        register_state_refs(
                            state_writers, _state_flow_positive_state_writes, option_entry.value,
                            {"object_kind": "event_option", "object_id": event_id,
                             "option": option_name, "effect": "option", "path": rel,
                             "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                            key,
                        )

    decision_event_state_links = []
    for (family, symbol), writers in sorted(state_writers.items()):
        readers = state_readers.get((family, symbol), [])
        if not readers:
            continue
        for writer in writers:
            for reader in readers:
                same_event = (
                    writer["object_kind"] in ("event", "event_option")
                    and reader["object_kind"] in ("event", "event_option")
                    and writer["object_id"] == reader["object_id"]
                )
                if writer["object_key"] == reader["object_key"] or same_event:
                    continue
                scope_match = (
                    _state_flow_flag_scope_matches(writer.get("scope"), reader.get("scope"))
                    if family == "flag" else None
                )
                decision_event_state_links.append({
                    "family": family, "id": symbol, "local_tag": writer["local_tag"],
                    "relationship": "{}_to_{}".format(
                        writer["object_kind"].replace("_option", ""),
                        reader["object_kind"].replace("_option", ""),
                    ),
                    "status": (
                        "same_id_scope_mismatch_candidate"
                        if scope_match is False else "same_id_cross_object_candidate"
                    ),
                    "scope_match": scope_match,
                    "writer": {key: value for key, value in writer.items()
                               if key not in ("object_key", "family", "id", "scope", "local_tag")},
                    "reader": {key: value for key, value in reader.items()
                               if key not in ("object_key", "family", "id", "scope", "local_tag")},
                })
    decision_event_state_links.sort(
        key=lambda item: (item["local_tag"], item["family"], item["id"],
                          item["writer"]["path"], item["writer"]["line"],
                          item["reader"]["path"], item["reader"]["line"])
    )

    on_action_hooks = []
    for path in script_files["on_actions"]:
        parsed = parsed_sources[path]
        containers = [
            entry.value for entry in direct_entries(parsed.root, "on_actions")
            if isinstance(entry.value, Block)
        ] or [parsed.root]
        for container in containers:
            for entry in container.entries:
                if isinstance(entry.value, Block):
                    on_action_hooks.append({
                        "id": entry.key.value, "path": _state_flow_relative(path, mod), "line": entry.line,
                    })

    history_summaries, history_tags = [], set()
    for path in history_files:
        parsed = parsed_sources[path]
        tag = _state_flow_owner_tag(path, countries)
        if tag:
            history_tags.add(tag)
        date_blocks = [
            entry for entry in parsed.root.entries
            if isinstance(entry, Entry) and isinstance(entry.value, Block)
            and re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}", entry.key.value)
        ]
        idea_grants, variable_initialisations = [], []
        for date_entry in date_blocks:
            for item in walk_entries(date_entry.value):
                if item.key.value in ("add_ideas", "add_idea"):
                    for idea_id in _state_flow_effect_values(item):
                        idea_grants.append({
                            "idea": idea_id, "date": date_entry.key.value,
                            "path": _state_flow_relative(path, mod), "line": item.line,
                        })
                elif item.key.value in ("add_timed_idea",) and isinstance(item.value, Block):
                    idea_id = get_scalar(item.value, "idea")
                    if idea_id:
                        idea_grants.append({
                            "idea": idea_id, "date": date_entry.key.value,
                            "path": _state_flow_relative(path, mod), "line": item.line,
                            "timed": True,
                        })
                elif item.key.value in ("set_variable", "set_temp_variable"):
                    for variable in _state_flow_variable_names(item):
                        variable_initialisations.append({
                            "variable": variable, "command": item.key.value, "date": date_entry.key.value,
                            "path": _state_flow_relative(path, mod), "line": item.line,
                        })
        history_summaries.append({
            "tag": tag, "path": _state_flow_relative(path, mod),
            "date_blocks": len(date_blocks),
            "first_date": date_blocks[0].key.value if date_blocks else None,
            "startup_idea_grants": idea_grants,
            "startup_variable_initialisations": variable_initialisations,
            "startup_event_calls": [
                {"kind": kind, "id": event_id, "line": line}
                for kind, event_id, line in iter_event_calls(parsed.root)
            ],
        })

    missing_history_tags = sorted(country_tags - history_tags) if history_files else sorted(country_tags)
    scope_usage_counts = Counter()
    for parsed in parsed_sources.values():
        for entry in walk_entries(parsed.root):
            value = scalar(entry) or ""
            for scope in re.findall(r"\b(ROOT|FROM|PREV|THIS)\.", value):
                scope_usage_counts[scope] += 1

    return {
        "counts": {
            "source_files": len(parsed_sources), "history_files": len(history_files),
            "history_tags": len(history_tags),
            "scripted_effect_files": len(script_files["scripted_effects"]),
            "scripted_effect_definitions": len(script_definition_indexes["scripted_effects"]),
            "scripted_effect_calls": len(effect_calls),
            "scripted_trigger_files": len(script_files["scripted_triggers"]),
            "scripted_trigger_definitions": len(script_definition_indexes["scripted_triggers"]),
            "scripted_trigger_calls": len(trigger_calls),
            "on_action_files": len(script_files["on_actions"]), "on_action_hooks": len(on_action_hooks),
            "flag_symbols": len(flag_symbols), "variable_symbols": len(variable_symbols),
            "array_symbols": len(array_symbols),
            "decision_event_state_links": len(decision_event_state_links),
        },
        "parse_errors": parse_errors, "script_parse_errors": script_parse_errors,
        "duplicate_scripted_effect_definitions": duplicate_effects,
        "duplicate_scripted_trigger_definitions": duplicate_triggers,
        "scripted_effect_calls": effect_calls, "scripted_trigger_calls": trigger_calls,
        "scripted_effects_without_local_call": unreferenced_effects,
        "scripted_triggers_without_local_call": unreferenced_triggers,
        "unresolved_scripted_call_candidates": deduped_unresolved,
        "flag_symbols": flag_symbols,
        "potentially_unread_local_flags": potentially_unread_flags,
        "local_flags_read_without_writer": flags_read_without_local_writer,
        "variable_symbols": variable_symbols,
        "potentially_unread_local_variables": potentially_unread_variables,
        "local_variables_read_without_writer": variables_read_without_local_writer,
        "array_symbols": array_symbols,
        "decision_event_state_links": decision_event_state_links,
        "potentially_unread_local_arrays": potentially_unread_arrays,
        "local_arrays_read_without_writer": arrays_read_without_local_writer,
        "idea_on_add_without_matching_on_remove": idea_on_add_without_matching_on_remove,
        "on_action_hooks": on_action_hooks,
        "on_action_inventory_available": bool(script_files["on_actions"]),
        "scripted_trigger_inventory_available": bool(script_files["scripted_triggers"]),
        "history_inventory_available": bool(history_files),
        "history_tags": sorted(history_tags), "history_summaries": history_summaries,
        "countries_without_local_history": [
            {"tag": tag, "status": "unknown_or_external_history_not_in_checkout"}
            for tag in missing_history_tags
        ],
        "scope_usage_counts": dict(sorted(scope_usage_counts.items())),
        "scope_analysis_limit": (
            "Static indexing does not resolve ROOT/FROM/PREV/THIS or prove that a scripted effect "
            "is called by another target TDF file. Treat unreferenced definitions and unmatched lifecycle "
            "mutations as review candidates, not automatic errors."
        ),
    }
