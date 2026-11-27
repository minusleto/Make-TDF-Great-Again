"""Аудит событий: определения, ссылки, локализация, опции.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional
from .core import (
    Block,
    GENERIC_LABELS,
    _state_flow_script_files,
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
    get_loc_value,
    idea_candidates,
)


def is_local_event_key(key: str, event_id: str, tag: Optional[str] = None) -> bool:
    """Recognize event-local keys without treating shared/base keys as local."""
    namespace = event_id.split(".", 1)[0] if "." in event_id else ""
    if namespace and (key == namespace or key.startswith(namespace + ".") or key.startswith(namespace + "_")):
        return True
    return bool(tag and key.startswith(tag + "_"))


def event_localisation_keys(event_block, field):
    """Collect scalar or conditional text = localisation keys for event title/desc."""
    keys = []
    for entry in direct_entries(event_block, field):
        value = scalar(entry)
        if value:
            keys.append(value)
        elif isinstance(entry.value, Block):
            for text_entry in nested_entries(entry.value, "text"):
                text_value = scalar(text_entry)
                if text_value:
                    keys.append(text_value)
    return list(dict.fromkeys(keys))


def build_event_audit(repo, countries, loc_index, event_parsed, content_indexes=None, idea_report=None):
    """Build project-wide event, localisation, reference and chain diagnostics."""
    mod = Path(repo) / "mdredux"
    file_tags = {
        str(country["events"]): tag
        for tag, country in countries.items()
        if country["events"] is not None
    }
    definitions = []
    namespace_declarations = []
    parse_errors = []
    missing_event_ids = []
    missing_title_fields = []
    missing_desc_fields = []
    missing_option_names = []

    for path, parsed in event_parsed.items():
        for issue in parsed.issues:
            parse_errors.append("{}:{}".format(path, issue))
        for entry in direct_entries(parsed.root, "add_namespace"):
            ns = scalar(entry)
            if ns:
                namespace_declarations.append({"namespace": ns, "path": str(path), "line": entry.line})
        for kind in ("country_event", "news_event"):
            for event_entry in direct_entries(parsed.root, kind):
                if not isinstance(event_entry.value, Block):
                    continue
                body = event_entry.value
                id_entry = next((item for item in direct_entries(body, "id") if scalar(item)), None)
                event_id = scalar(id_entry) if id_entry else None
                if not event_id:
                    missing_event_ids.append({"kind": kind, "path": str(path), "line": event_entry.line})
                    continue
                trigger = get_block(body, "trigger")
                trigger_tags = [scalar(item) for item in nested_entries(trigger, "tag")] if trigger else []
                trigger_tags = [value for value in trigger_tags if value]
                trigger_scopes = sorted({
                    item.key.value for item in walk_entries(trigger)
                    if isinstance(item.value, Block) and item.key.value.upper() in ("FROM", "ROOT", "PREV", "THIS")
                }) if trigger else []
                title = get_scalar(body, "title")
                desc = get_scalar(body, "desc")
                title_keys = event_localisation_keys(body, "title")
                desc_keys = event_localisation_keys(body, "desc")
                hidden = (get_scalar(body, "hidden") or "").lower() in ("yes", "true", "1")
                if not title_keys and not hidden:
                    missing_title_fields.append({"id": event_id, "kind": kind, "path": str(path), "line": id_entry.line})
                if not desc_keys and not hidden:
                    missing_desc_fields.append({"id": event_id, "kind": kind, "path": str(path), "line": id_entry.line})
                definitions.append({
                    "id": event_id, "kind": kind, "path": str(path), "line": id_entry.line,
                    "block": body, "title": title, "desc": desc,
                    "title_keys": title_keys, "desc_keys": desc_keys, "hidden": hidden,
                    "picture": get_scalar(body, "picture"),
                    "is_triggered_only": (get_scalar(body, "is_triggered_only") or "").lower() in ("yes", "true", "1"),
                    "fire_only_once": (get_scalar(body, "fire_only_once") or "").lower() in ("yes", "true", "1"),
                    "has_trigger": trigger is not None,
                    "trigger_tags": trigger_tags, "trigger_scopes": trigger_scopes,
                    "option_count": len(direct_entries(body, "option")),
                })

    definitions_by_id = defaultdict(list)
    for definition in definitions:
        definitions_by_id[definition["id"]].append(definition)
    duplicate_event_ids = []
    for event_id, occurrences in sorted(definitions_by_id.items()):
        if len(occurrences) > 1:
            duplicate_event_ids.append({
                "id": event_id,
                "definitions": [
                    {"kind": item["kind"], "path": item["path"], "line": item["line"]}
                    for item in occurrences
                ],
            })

    namespace_groups = defaultdict(list)
    for item in namespace_declarations:
        namespace_groups[item["namespace"]].append(item)
    duplicate_namespaces = []
    for namespace, occurrences in sorted(namespace_groups.items()):
        if len(occurrences) > 1:
            same_file = len({item["path"] for item in occurrences}) == 1
            duplicate_namespaces.append({
                "namespace": namespace, "scope": "same_file" if same_file else "multiple_files",
                "declarations": occurrences,
            })

    reused_loc = defaultdict(list)
    missing_loc, external_loc = [], []
    missing_option_loc, external_option_loc = [], []
    duplicate_loc_definitions = []
    generic_option_labels, long_option_labels = [], []
    option_loc_lines = []
    option_log_key_mismatches = []
    missing_event_idea_candidates = []
    missing_event_scripted_loc = []
    idea_index = (content_indexes or {}).get("idea_ids", {})
    scripted_definitions = (content_indexes or {}).get("scripted_defs", {})
    scripted_names = {
        tag: {item["name"] for item in items}
        for tag, items in scripted_definitions.items()
    }
    scripted_ref_re = re.compile(r"\[([A-Z]{3}_[A-Za-z0-9_]+)\]")
    for definition in definitions:
        tag = file_tags.get(definition["path"])
        for field in ("title", "desc"):
            keys = definition.get(field + "_keys", [])
            if not keys and definition.get(field):
                keys = [definition[field]]
            for key in keys:
                reused_loc[(field, key)].append({
                    "event_id": definition["id"], "path": definition["path"], "line": definition["line"],
                })
                if key not in loc_index:
                    item = {"field": field, "key": key, "event_id": definition["id"],
                            "path": definition["path"], "line": definition["line"]}
                    (missing_loc if is_local_event_key(key, definition["id"], tag) else external_loc).append(item)
                elif len(loc_index[key]) > 1:
                    duplicate_loc_definitions.append({
                        "field": field, "key": key,
                        "definitions": [{"path": loc.path, "line": loc.line} for loc in loc_index[key]],
                    })

        for option_entry in direct_entries(definition["block"], "option"):
            if not isinstance(option_entry.value, Block):
                continue
            option = option_entry.value
            key = get_scalar(option, "name")
            if not key:
                missing_option_names.append({
                    "event_id": definition["id"], "path": definition["path"], "line": option_entry.line,
                })
            elif key not in loc_index:
                item = {"key": key, "event_id": definition["id"],
                        "path": definition["path"], "line": option_entry.line}
                (missing_option_loc if is_local_event_key(key, definition["id"], tag) else external_option_loc).append(item)
            else:
                label = get_loc_value(loc_index, key)
                if label:
                    label_info = {
                        "key": key, "label": label, "event_id": definition["id"],
                        "path": definition["path"], "line": option_entry.line,
                    }
                    if label.strip().rstrip(".!?").lower() in GENERIC_LABELS:
                        generic_option_labels.append(label_info)
                    elif len(label) > 35:
                        long_option_labels.append(label_info)
            # Check log independently: a missing name must not hide a missing log.
            log_entry = next(
                (item for item in direct_entries(option, "log") if scalar(item)), None
            )
            log_value = scalar(log_entry)
            if log_entry is None:
                option_loc_lines.append({
                    "key": key or "?", "event_id": definition["id"],
                    "path": definition["path"], "line": option_entry.line,
                })
            elif key:
                # Only compare the established diagnostic form. Arbitrary log text
                # is intentionally left alone because it need not contain a key.
                log_match = re.search(
                    r"(?:^|:\s*)([A-Za-z0-9_]+\.\d+\.[A-Za-z0-9_]+)\s+executed\s*$",
                    log_value or "",
                )
                if log_match and log_match.group(1) != key:
                    option_log_key_mismatches.append({
                        "event_id": definition["id"], "path": definition["path"],
                        "option_key": key, "log_key": log_match.group(1),
                        "option_line": option_entry.line, "log_line": log_entry.line,
                    })

    # Event-local idea references are compared against this repository slice.
    # Missing IDs remain candidates until the exact TDF source is checked.
    for definition in definitions:
        source_tag = file_tags.get(definition["path"])
        for idea_id in idea_candidates(definition["block"]):
            match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", idea_id)
            if not match:
                continue
            tag = match.group(1)
            if tag in countries and idea_id not in idea_index.get(tag, set()):
                missing_event_idea_candidates.append({
                    "event_id": definition["id"], "idea": idea_id, "tag": tag,
                    "classification": "local_candidate" if source_tag == tag else "external_or_cross_country_candidate",
                    "path": definition["path"], "line": definition["line"],
                })

        localisation_keys = list(definition.get("title_keys", [])) + list(definition.get("desc_keys", []))
        if not localisation_keys:
            localisation_keys = [definition["title"], definition["desc"]]
        for option_entry in direct_entries(definition["block"], "option"):
            if isinstance(option_entry.value, Block):
                option_name = get_scalar(option_entry.value, "name")
                if option_name:
                    localisation_keys.append(option_name)
        for loc_key in filter(None, localisation_keys):
            for occurrence in loc_index.get(loc_key, []):
                for name in scripted_ref_re.findall(occurrence.value):
                    tag = name[:3]
                    if tag in countries and name not in scripted_names.get(tag, set()):
                        missing_event_scripted_loc.append({
                            "event_id": definition["id"], "localisation_key": loc_key,
                            "scripted_localisation": name, "path": occurrence.path,
                            "line": occurrence.line,
                        })

    reused_event_loc = []
    for (field, key), occurrences in sorted(reused_loc.items()):
        event_ids = sorted({item["event_id"] for item in occurrences})
        if len(event_ids) > 1:
            reused_event_loc.append({"field": field, "key": key, "event_ids": event_ids, "uses": occurrences})

    references = []

    def add_references(block, source_kind, source_path, caller):
        for call_kind, target_id, line in iter_event_calls(block):
            references.append({
                "kind": call_kind, "target": target_id, "source_kind": source_kind,
                "source": str(source_path), "caller": caller, "line": line,
            })

    for country in countries.values():
        for focus in find_named_blocks(country["tree_parsed"].root, "focus"):
            focus_id = get_scalar(focus, "id") or "unknown_focus"
            add_references(focus, "focus", country["tree"], focus_id)

    decisions_dir = mod / "common" / "decisions"
    for path in iter_files(decisions_dir, ".txt"):
        parsed = parse_hoi(read(path))
        add_references(parsed.root, "decision", path, path.stem)

    for folder, source_kind in (("scripted_effects", "scripted_effect"), ("on_actions", "on_action")):
        source_dir = mod / "common" / folder
        # Match state-flow inventory: HOI4 script files may be extensionless.
        for path in _state_flow_script_files(source_dir):
            parsed = event_parsed.get(path)
            if parsed is None:
                parsed = parse_hoi(read(path))
                for issue in parsed.issues:
                    parse_errors.append("{}:{}".format(path, issue))
            add_references(parsed.root, source_kind, path, path.stem)

    # Country history can schedule events at start dates; treat these as graph roots.
    history_dirs = (mod / "history" / "countries", mod / "common" / "history" / "countries")
    history_files = sorted({
        path for directory in history_dirs for path in iter_files(directory, ".txt")
    })
    for path in history_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            parse_errors.append("{}:{}".format(path, issue))
        add_references(parsed.root, "history", path, path.stem)

    for definition in definitions:
        add_references(definition["block"], "event", definition["path"], definition["id"])

    # Ideas can schedule events from on_add/on_remove. Keep these edges even if
    # no local grant is known, but only use a locally granted idea as a reachability root.
    locally_granted_ideas = {
        item["idea"] for item in (idea_report or {}).get("idea_references", [])
        if item.get("usage") in ("add", "timed_add")
    }
    for idea in (content_indexes or {}).get("idea_definitions", []):
        for call in idea.get("lifecycle_event_calls", []):
            references.append({
                "kind": call["kind"], "target": call["target"],
                "source_kind": "idea", "source": idea["path"],
                "caller": idea["id"], "line": call["line"],
                "source_owner_tag": idea.get("owner_tag"),
                "lifecycle": call["lifecycle"],
                "idea_grant_status": (
                    "local_grant_found" if idea["id"] in locally_granted_ideas
                    else "no_local_grant_found"
                ),
            })

    defined_ids = set(definitions_by_id)
    defined_namespaces = {item["namespace"] for item in namespace_declarations}
    unresolved_references, external_references = [], []
    event_edges = defaultdict(set)
    root_events = set()
    idea_event_roots = set()
    scripted_effect_references = []
    scripted_effect_targets = set()
    for reference in references:
        target = reference["target"]
        if target in defined_ids:
            if reference["source_kind"] == "event":
                event_edges[reference["caller"]].add(target)
            elif reference["source_kind"] == "scripted_effect":
                # A definition can contain a call without ever being invoked itself.
                # Keep the reference visible but do not treat it as proof of reachability.
                scripted_effect_references.append(dict(reference))
                scripted_effect_targets.add(target)
            elif reference["source_kind"] == "idea":
                if reference.get("idea_grant_status") == "local_grant_found":
                    root_events.add(target)
                    idea_event_roots.add(target)
            else:
                root_events.add(target)
            continue
        namespace = target.split(".", 1)[0] if "." in target else ""
        (unresolved_references if namespace and namespace in defined_namespaces else external_references).append(dict(reference))

    reachable = set()
    pending = list(root_events)
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(event_edges.get(current, ()))

    orphan_triggered = []
    for definition in definitions:
        if (definition["is_triggered_only"] and definition["id"] not in reachable
                and definition["id"] not in scripted_effect_targets):
            orphan_triggered.append({
                "id": definition["id"], "kind": definition["kind"], "path": definition["path"],
                "line": definition["line"], "has_trigger": definition["has_trigger"],
                "fire_only_once": definition["fire_only_once"],
            })

    missing_picture = [
        {"id": item["id"], "kind": item["kind"], "path": item["path"], "line": item["line"]}
        for item in definitions if not item["picture"]
    ]
    metadata = [{key: value for key, value in item.items() if key != "block"} for item in definitions]
    kind_counts = Counter(item["kind"] for item in definitions)

    return {
        "counts": {"definitions": len(definitions), "country_event": kind_counts.get("country_event", 0),
                   "news_event": kind_counts.get("news_event", 0), "namespaces": len(namespace_groups)},
        "parse_errors": parse_errors, "missing_event_ids": missing_event_ids,
        "missing_title_fields": missing_title_fields, "missing_desc_fields": missing_desc_fields,
        "missing_option_names": missing_option_names,
        "duplicate_event_ids": duplicate_event_ids, "duplicate_namespaces": duplicate_namespaces,
        "missing_localisation": missing_loc, "external_localisation": external_loc,
        "duplicate_localisation_definitions": duplicate_loc_definitions,
        "missing_option_localisation": missing_option_loc, "external_option_localisation": external_option_loc,
        "generic_option_labels": generic_option_labels, "long_option_labels": long_option_labels,
        "options_without_log": option_loc_lines,
        "option_log_key_mismatches": option_log_key_mismatches,
        "missing_event_idea_candidates": missing_event_idea_candidates,
        "missing_event_scripted_localisation": missing_event_scripted_loc,
        "reused_title_desc_keys": reused_event_loc, "unresolved_references": unresolved_references,
        "external_references": external_references, "scripted_effect_references": scripted_effect_references,
        "unreachable_triggered_events": orphan_triggered,
        "events_without_picture": missing_picture, "metadata": metadata,
        "references": references,
        "event_edges": [dict(item) for item in references
                        if item["source_kind"] == "event" and item["target"] in defined_ids],
        "root_events": sorted(root_events), "reachable_events": sorted(reachable),
        "idea_event_roots": sorted(idea_event_roots),
    }
