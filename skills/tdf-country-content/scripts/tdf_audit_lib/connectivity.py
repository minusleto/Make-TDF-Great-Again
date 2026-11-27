"""Аудит связности веток фокусов.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import defaultdict
from typing import Dict, List, Optional
from .core import (
    Block,
    Entry,
    Token,
    direct_entries,
    find_named_blocks,
    get_block,
    get_scalar,
    nested_entries,
    scalar,
    walk_entries,
)
from .indexes import (
    focus_prerequisite_ids,
    get_loc_value,
)
from .state_flow import (
    _state_flow_positive_state_reads,
)


def _branch_values(entry: Entry) -> List[str]:
    """Read scalar or bare-list values from an idea effect/condition entry."""
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    values = []
    for item in entry.value.items:
        if isinstance(item, Token):
            if item.value.lower() not in ("yes", "no", "none", "empty"):
                values.append(item.value)
        elif isinstance(item, Entry) and item.key.value in ("idea", "add_idea", "remove_idea"):
            value = scalar(item)
            if value:
                values.append(value)
    return values


def _branch_idea_effects(block: Optional[Block]) -> List[Dict[str, str]]:
    """Collect explicit idea grants/removals, excluding has_idea conditions."""
    if block is None:
        return []
    result = []
    for entry in walk_entries(block):
        command = entry.key.value
        if command in ("add_ideas", "add_idea", "remove_ideas", "remove_idea"):
            usage = "grant" if command.startswith("add_") else "remove"
            for idea_id in _branch_values(entry):
                result.append({"idea": idea_id, "usage": usage, "command": command, "line": entry.line})
        elif command == "add_timed_idea" and isinstance(entry.value, Block):
            idea_id = get_scalar(entry.value, "idea")
            if idea_id:
                result.append({"idea": idea_id, "usage": "timed_grant",
                               "command": command, "line": entry.line})
    return result


def _branch_idea_gates(block: Optional[Block]) -> List[Dict[str, str]]:
    if block is None:
        return []
    result = []
    # Reuse the state-flow polarity walker: a has_idea inside NOT/NOR is not
    # evidence that the object requires the idea to proceed.
    for reference in _state_flow_positive_state_reads(block):
        if reference["family"] != "idea":
            continue
        result.append({
            "idea": reference["id"], "command": reference["command"], "line": reference["line"],
        })
    return result


def _branch_mio_references(block: Block) -> List[str]:
    found = set()
    for entry in walk_entries(block):
        for value in (entry.key.value, scalar(entry) or ""):
            found.update(re.findall(r"\bmio:([A-Za-z0-9_]+)\b", value))
    return sorted(found)


def _branch_equipment_outputs(block: Optional[Block]) -> List[Dict[str, str]]:
    if block is None:
        return []
    result = []
    for variant in find_named_blocks(block, "create_equipment_variant"):
        result.append({
            "kind": "variant", "name": get_scalar(variant, "name") or "",
            "equipment": get_scalar(variant, "type") or "", "line": variant.line,
        })
    for grant in find_named_blocks(block, "add_equipment_to_stockpile"):
        result.append({
            "kind": "stockpile", "name": get_scalar(grant, "variant_name") or "",
            "equipment": get_scalar(grant, "type") or "", "amount": get_scalar(grant, "amount") or "",
            "producer": get_scalar(grant, "producer") or "", "line": grant.line,
        })
    return result


def build_branch_connectivity_audit(countries, event_report, idea_report, industry_report,
                                    state_flow_report, event_parsed, content_indexes,
                                    loc_index, tags=None):
    """Assemble typed evidence edges across focus, event, idea, tooltip, MIO and state flow.

    This is a static cross-reference map. Candidate handoffs are review aids, not
    proof of runtime reachability and never affect the auditor exit code.
    """
    wanted = set(tags or countries)
    wanted &= set(countries)
    focus_by_tag = {}
    focus_lookup = {}
    focus_prerequisite_edges = []
    focus_event_edges = []
    focus_idea_grant_edges = []
    focus_idea_gate_edges = []
    focus_equipment_edges = []
    focus_mio_edges = []
    focus_nodes_by_tag = {}

    for tag in sorted(wanted):
        country = countries[tag]
        focus_nodes = []
        focus_bodies = {}
        for body in find_named_blocks(country["tree_parsed"].root, "focus"):
            focus_id = get_scalar(body, "id")
            if not focus_id:
                continue
            focus_bodies[focus_id] = body
            focus_lookup[focus_id] = (tag, body)
            focus_nodes.append({
                "id": focus_id, "path": str(country["tree"]), "line": body.line,
                "relative_position_id": get_scalar(body, "relative_position_id"),
                "prerequisites": focus_prerequisite_ids(body),
                "has_completion_reward": bool(direct_entries(body, "completion_reward")),
                "has_hidden_effect": bool(direct_entries(body, "hidden_effect")),
            })
            for prerequisite in focus_prerequisite_ids(body):
                focus_prerequisite_edges.append({
                    "tag": tag, "from": prerequisite, "to": focus_id,
                    "relation": "prerequisite", "path": str(country["tree"]), "line": body.line,
                })

            for field in ("completion_reward", "hidden_effect"):
                for effect_entry in direct_entries(body, field):
                    if not isinstance(effect_entry.value, Block):
                        continue
                    for output in _branch_idea_effects(effect_entry.value):
                        if output["usage"] in ("grant", "timed_grant"):
                            focus_idea_grant_edges.append({
                                "tag": tag, "from": focus_id, "to": output["idea"],
                                "relation": output["usage"], "command": output["command"],
                                "path": str(country["tree"]), "line": output["line"],
                            })
                    for output in _branch_equipment_outputs(effect_entry.value):
                        focus_equipment_edges.append({
                            "tag": tag, "from": focus_id, **output, "path": str(country["tree"]),
                        })

            for gate_name in ("available", "bypass", "cancel_if_invalid"):
                for gate_entry in direct_entries(body, gate_name):
                    if not isinstance(gate_entry.value, Block):
                        continue
                    for gate in _branch_idea_gates(gate_entry.value):
                        focus_idea_gate_edges.append({
                            "tag": tag, "from": focus_id, "to": gate["idea"],
                            "relation": "idea_gate", "gate": gate_name,
                            "command": gate["command"], "path": str(country["tree"]),
                            "line": gate["line"],
                        })

            for tooltip_entry in nested_entries(body, "show_ideas_tooltip"):
                target = scalar(tooltip_entry)
                if target:
                    focus_idea_gate_edges.append({
                        "tag": tag, "from": focus_id, "to": target,
                        "relation": "show_ideas_tooltip", "gate": "tooltip",
                        "command": "show_ideas_tooltip", "path": str(country["tree"]),
                        "line": tooltip_entry.line,
                    })

            for mio_id in _branch_mio_references(body):
                focus_mio_edges.append({
                    "tag": tag, "from": focus_id, "to": mio_id,
                    "relation": "uses_mio", "path": str(country["tree"]), "line": body.line,
                })

        focus_by_tag[tag] = focus_bodies
        focus_nodes_by_tag[tag] = focus_nodes

    event_file_tags = {
        str(country["events"]): tag for tag, country in countries.items()
        if country.get("events") is not None and tag in wanted
    }
    definitions_by_id = defaultdict(list)
    for item in event_report.get("metadata", []):
        definitions_by_id[item["id"]].append(item)
    defined_event_ids = set(definitions_by_id)
    references = event_report.get("references", [])
    unresolved_refs = {
        item.get("target") for item in event_report.get("unresolved_references", [])
    }
    confirmed_external_event_ids = {
        item.get("target") for item in event_report.get("confirmed_external_references", [])
    }

    focus_event_edges = []
    event_event_edges = []
    idea_event_edges = []
    unresolved_local_event_edges = []
    external_event_edges = []
    for reference in references:
        target = reference.get("target")
        if not target:
            continue
        if target in defined_event_ids:
            status = "local_definition"
        elif target in unresolved_refs:
            status = "missing_in_declared_local_namespace"
        elif target in confirmed_external_event_ids:
            status = "confirmed_external_definition"
        else:
            status = "external_or_unknown_namespace"
        source_kind = reference.get("source_kind")
        owner = None
        if source_kind == "focus":
            owner = next((tag for tag in wanted
                          if (reference.get("caller") or "").startswith(tag + "_")), None)
        elif source_kind == "event":
            owner = event_file_tags.get(reference.get("source"))
        elif source_kind == "idea":
            owner = reference.get("source_owner_tag")
            if not owner:
                match = re.match(r"^([A-Z]{3})_", reference.get("caller") or "")
                owner = match.group(1) if match else None
        edge = {
            "from_kind": source_kind, "from": reference.get("caller"),
            "to_kind": "event", "to": target,
            "relation": "idea_lifecycle_calls_event" if source_kind == "idea" else "calls_event",
            "status": status, "path": reference.get("source"), "line": reference.get("line"),
            "tag": owner, "lifecycle": reference.get("lifecycle"),
            "idea_grant_status": reference.get("idea_grant_status"),
        }
        if source_kind == "focus" and owner:
            focus_event_edges.append(edge)
        elif source_kind == "event" and owner:
            event_event_edges.append(edge)
        elif source_kind == "idea" and owner:
            idea_event_edges.append(edge)
        if source_kind in ("focus", "event", "idea") and owner in wanted:
            if status == "missing_in_declared_local_namespace":
                unresolved_local_event_edges.append(dict(edge))
            elif status == "external_or_unknown_namespace":
                external_event_edges.append(dict(edge))

    event_nodes = []
    event_idea_grant_edges = []
    event_idea_gate_edges = []
    event_equipment_edges = []
    event_edges_by_id = defaultdict(set)
    event_roots_by_focus = defaultdict(set)
    for edge in event_event_edges:
        if edge["status"] == "local_definition":
            event_edges_by_id[edge["from"]].add(edge["to"])
    for edge in focus_event_edges:
        if edge["status"] == "local_definition":
            event_roots_by_focus[edge["from"]].add(edge["to"])

    for path, parsed in event_parsed.items():
        tag = event_file_tags.get(str(path))
        if tag not in wanted:
            continue
        for kind in ("country_event", "news_event"):
            for event_entry in direct_entries(parsed.root, kind):
                if not isinstance(event_entry.value, Block):
                    continue
                body = event_entry.value
                event_id = get_scalar(body, "id")
                if not event_id:
                    continue
                event_nodes.append({
                    "tag": tag, "id": event_id, "kind": kind, "path": str(path),
                    "line": event_entry.line,
                    "is_triggered_only": (get_scalar(body, "is_triggered_only") or "").lower()
                                        in ("yes", "true", "1"),
                })
                for effect_entry in direct_entries(body, "immediate"):
                    if not isinstance(effect_entry.value, Block):
                        continue
                    for output in _branch_idea_effects(effect_entry.value):
                        if output["usage"] in ("grant", "timed_grant"):
                            event_idea_grant_edges.append({
                                "tag": tag, "from": event_id, "to": output["idea"],
                                "relation": output["usage"], "effect": "immediate",
                                "command": output["command"], "path": str(path), "line": output["line"],
                            })
                    for output in _branch_equipment_outputs(effect_entry.value):
                        event_equipment_edges.append({
                            "tag": tag, "from": event_id, **output,
                            "effect": "immediate", "path": str(path),
                        })
                for gate in _branch_idea_gates(get_block(body, "trigger")):
                    event_idea_gate_edges.append({
                        "tag": tag, "from": event_id, "to": gate["idea"],
                        "relation": "idea_gate", "gate": "event_trigger",
                        "command": gate["command"], "path": str(path), "line": gate["line"],
                    })
                for option_entry in direct_entries(body, "option"):
                    if not isinstance(option_entry.value, Block):
                        continue
                    option = option_entry.value
                    option_name = get_scalar(option, "name") or "(unnamed option)"
                    for output in _branch_idea_effects(option):
                        if output["usage"] in ("grant", "timed_grant"):
                            event_idea_grant_edges.append({
                                "tag": tag, "from": event_id, "to": output["idea"],
                                "relation": output["usage"], "effect": "option",
                                "option": option_name, "command": output["command"],
                                "path": str(path), "line": output["line"],
                            })
                    for output in _branch_equipment_outputs(option):
                        event_equipment_edges.append({
                            "tag": tag, "from": event_id, **output,
                            "effect": "option", "option": option_name, "path": str(path),
                        })
                    for gate in _branch_idea_gates(get_block(option, "trigger")):
                        event_idea_gate_edges.append({
                            "tag": tag, "from": event_id, "to": gate["idea"],
                            "relation": "idea_gate", "gate": "option_trigger",
                            "option": option_name, "command": gate["command"],
                            "path": str(path), "line": gate["line"],
                        })

    idea_definitions = idea_report.get("idea_definitions", [])
    local_idea_ids = {item["id"] for item in idea_definitions}
    all_grant_sources = defaultdict(list)
    for edge in focus_idea_grant_edges:
        all_grant_sources[edge["to"]].append({
            "kind": "focus", "id": edge["from"], "tag": edge["tag"],
            "path": edge["path"], "line": edge["line"],
        })
    for edge in event_idea_grant_edges:
        all_grant_sources[edge["to"]].append({
            "kind": "event", "id": edge["from"], "tag": edge["tag"],
            "path": edge["path"], "line": edge["line"],
        })
    known_focus_paths = {str(country["tree"]) for tag, country in countries.items() if tag in wanted}
    known_event_paths = set(event_file_tags)
    for reference in idea_report.get("idea_references", []):
        if reference.get("usage") not in ("add", "timed_add"):
            continue
        idea_id = reference.get("idea")
        if not idea_id:
            continue
        path = reference.get("path", "")
        if path in known_focus_paths or path in known_event_paths:
            continue
        match = re.match(r"^([A-Z]{3})_", idea_id)
        owner_tag = match.group(1) if match else None
        if owner_tag in wanted:
            all_grant_sources[idea_id].append({
                "kind": "other_local_source", "id": path, "tag": owner_tag,
                "path": path, "line": reference.get("line"),
            })

    def reachable_events_from_focus_ancestors(tag, focus_id):
        bodies = focus_by_tag.get(tag, {})
        ancestors = set()
        pending = list(focus_prerequisite_ids(bodies[focus_id])) if focus_id in bodies else []
        while pending:
            current = pending.pop()
            if current in ancestors:
                continue
            ancestors.add(current)
            if current in bodies:
                pending.extend(focus_prerequisite_ids(bodies[current]))
        roots = set()
        for ancestor in ancestors:
            roots.update(event_roots_by_focus.get(ancestor, ()))
        reachable = set()
        queue = list(roots)
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(event_edges_by_id.get(current, ()))
        return ancestors, reachable

    focus_idea_gate_review_candidates = []
    for edge in focus_idea_gate_edges:
        if (edge["relation"] != "idea_gate" or edge.get("gate") != "available"
                or edge["to"] not in local_idea_ids):
            continue
        tag, focus_id, idea_id = edge["tag"], edge["from"], edge["to"]
        ancestors, reachable_events = reachable_events_from_focus_ancestors(tag, focus_id)
        writers = all_grant_sources.get(idea_id, [])
        connected_writers = [
            item for item in writers
            if (item["kind"] == "focus" and item["id"] in ancestors)
            or (item["kind"] == "event" and item["id"] in reachable_events)
        ]
        if connected_writers:
            edge["upstream_grant_sources"] = connected_writers
            edge["path_status"] = "local_upstream_grant_found"
        else:
            edge["upstream_grant_sources"] = []
            edge["path_status"] = (
                "local_writer_exists_but_path_not_proven" if writers
                else "no_local_writer_found_external_or_runtime_possible"
            )
            focus_idea_gate_review_candidates.append({
                "tag": tag, "focus": focus_id, "idea": idea_id,
                "status": edge["path_status"], "path": edge["path"], "line": edge["line"],
                "known_local_writers": writers[:10],
                "reason": (
                    "A local definition and focus availability gate exist, but no grant was found "
                    "in a prerequisite ancestor or in an event called by such an ancestor. "
                    "Check alternate paths, history, decisions, on_actions and scripted effects; otherwise request the relevant source file."
                ),
            })

    idea_tooltip_edges = []
    tooltip_script_review_candidates = []
    scripted_defs = content_indexes.get("scripted_defs", {})
    scripted_by_name = {
        item["name"]: item
        for items in scripted_defs.values()
        for item in items
    }
    bracket_ref_re = re.compile(r"\[([A-Za-z_][A-Za-z0-9_]*)\]")
    for idea in idea_definitions:
        tag = idea.get("owner_tag")
        if tag not in wanted:
            continue
        for tooltip_key in idea.get("custom_modifier_tooltips", []):
            idea_tooltip_edges.append({
                "tag": tag, "from": idea["id"], "to": tooltip_key,
                "relation": "custom_modifier_tooltip",
                "path": idea["path"], "line": idea["line"],
            })
            value = get_loc_value(loc_index, tooltip_key)
            if value is None:
                continue
            for script_name in bracket_ref_re.findall(value):
                if script_name in scripted_by_name:
                    script = scripted_by_name[script_name]
                    idea_tooltip_edges.append({
                        "tag": tag, "from": tooltip_key, "to": script_name,
                        "relation": "localisation_calls_scripted_localisation",
                        "path": script["path"],
                    })
                    for idea_ref in script.get("idea_refs", []):
                        idea_tooltip_edges.append({
                            "tag": tag, "from": script_name, "to": idea_ref,
                            "relation": "scripted_localisation_checks_idea",
                            "path": script["path"],
                        })
                elif script_name.startswith(tag + "_"):
                    tooltip_script_review_candidates.append({
                        "tag": tag, "idea": idea["id"], "tooltip_key": tooltip_key,
                        "scripted_localisation": script_name,
                        "status": "local_scripted_localisation_not_found_candidate",
                        "path": idea["path"], "line": idea["line"],
                    })

    idea_stage_edges = []
    for edge in idea_report.get("stage_name_links", []):
        owner_tag = next((item["owner_tag"] for item in idea_definitions
                          if item["id"] == edge["idea"]), None)
        if owner_tag in wanted:
            idea_stage_edges.append({
                "tag": owner_tag, "from": edge["idea"], "to": edge["base_idea"],
                "relation": "stage_uses_base_name", "path": edge["path"], "line": edge["line"],
            })

    mio_visibility_edges = []
    for mio in industry_report.get("mio_definitions", []):
        if mio.get("owner_tag") not in wanted:
            continue
        for focus_id in mio.get("visible_focus_refs", []):
            mio_visibility_edges.append({
                "tag": mio["owner_tag"], "from": mio["id"], "to": focus_id,
                "relation": "visible_after_focus", "path": mio["path"], "line": mio["line"],
                "status": "local_focus" if focus_id in focus_lookup else "focus_not_found_candidate",
            })

    state_handoff_edges = []
    for link in state_flow_report.get("decision_event_state_links", []):
        if link.get("local_tag") not in wanted:
            continue
        writer, reader = link.get("writer", {}), link.get("reader", {})
        state_handoff_edges.append({
            "tag": link["local_tag"],
            "from_kind": writer.get("object_kind"), "from": writer.get("object_id"),
            "to_kind": reader.get("object_kind"), "to": reader.get("object_id"),
            "relation": "state_handoff", "state_family": link.get("family"),
            "state_id": link.get("id"), "status": link.get("status"),
            "scope_match": link.get("scope_match"), "writer": writer, "reader": reader,
        })

    local_unresolved_event_calls = [
        item for item in unresolved_local_event_edges if item.get("tag") in wanted
    ]
    external_calls = [item for item in external_event_edges if item.get("tag") in wanted]
    orphan_events = []
    for item in event_report.get("unreachable_triggered_events", []):
        tag = event_file_tags.get(item.get("path", ""))
        if tag in wanted:
            orphan_events.append({**item, "tag": tag, "status": "no_local_incoming_call_candidate"})

    by_country = {}
    for tag in sorted(wanted):
        by_country[tag] = {
            "focus_nodes": focus_nodes_by_tag.get(tag, []),
            "focus_prerequisite_edges": [x for x in focus_prerequisite_edges if x["tag"] == tag],
            "focus_event_edges": [x for x in focus_event_edges if x.get("tag") == tag],
            "focus_idea_grant_edges": [x for x in focus_idea_grant_edges if x["tag"] == tag],
            "focus_idea_gate_edges": [x for x in focus_idea_gate_edges if x["tag"] == tag],
            "focus_equipment_edges": [x for x in focus_equipment_edges if x["tag"] == tag],
            "focus_mio_edges": [x for x in focus_mio_edges if x["tag"] == tag],
            "event_nodes": [x for x in event_nodes if x["tag"] == tag],
            "event_event_edges": [x for x in event_event_edges if x.get("tag") == tag],
            "idea_event_edges": [x for x in idea_event_edges if x.get("tag") == tag],
            "event_idea_grant_edges": [x for x in event_idea_grant_edges if x["tag"] == tag],
            "event_idea_gate_edges": [x for x in event_idea_gate_edges if x["tag"] == tag],
            "event_equipment_edges": [x for x in event_equipment_edges if x["tag"] == tag],
            "idea_tooltip_edges": [x for x in idea_tooltip_edges if x["tag"] == tag],
            "idea_stage_edges": [x for x in idea_stage_edges if x["tag"] == tag],
            "mio_visibility_edges": [x for x in mio_visibility_edges if x["tag"] == tag],
            "state_handoff_edges": [x for x in state_handoff_edges if x["tag"] == tag],
            "review_candidates": {
                "focus_idea_gate_paths": [x for x in focus_idea_gate_review_candidates if x["tag"] == tag],
                "tooltip_script_resolution": [x for x in tooltip_script_review_candidates if x["tag"] == tag],
                "unresolved_local_event_calls": [x for x in local_unresolved_event_calls if x["tag"] == tag],
                "external_event_calls": [x for x in external_calls if x["tag"] == tag],
                "unreachable_triggered_events": [x for x in orphan_events if x["tag"] == tag],
                "mio_visibility_focus": [x for x in mio_visibility_edges
                                         if x["tag"] == tag and x["status"] != "local_focus"],
            },
        }

    return {
        "scope": "local_static_cross_reference",
        "limits": (
            "Edges record explicit local references. Focus prerequisite ancestry is a conservative union "
            "of referenced focus IDs; dynamic scopes, user-provided external writers, indirect scripted calls, "
            "AI/runtime timing and option probabilities are not simulated. Review candidates never affect exit code."
        ),
        "counts": {
            "focus_nodes": sum(len(item["focus_nodes"]) for item in by_country.values()),
            "focus_prerequisite_edges": len(focus_prerequisite_edges),
            "focus_event_edges": len(focus_event_edges),
            "event_event_edges": len(event_event_edges),
            "idea_event_edges": len(idea_event_edges),
            "focus_idea_grant_edges": len(focus_idea_grant_edges),
            "focus_idea_gate_edges": len(focus_idea_gate_edges),
            "event_idea_grant_edges": len(event_idea_grant_edges),
            "event_idea_gate_edges": len(event_idea_gate_edges),
            "idea_tooltip_edges": len(idea_tooltip_edges),
            "idea_stage_edges": len(idea_stage_edges),
            "focus_mio_edges": len(focus_mio_edges),
            "mio_visibility_edges": len(mio_visibility_edges),
            "state_handoff_edges": len(state_handoff_edges),
            "review_candidates": (
                len(focus_idea_gate_review_candidates) + len(tooltip_script_review_candidates)
                + len(local_unresolved_event_calls) + len(external_calls) + len(orphan_events)
                + sum(1 for item in mio_visibility_edges if item["status"] != "local_focus")
            ),
        },
        "by_country": by_country,
        "review_candidates": {
            "focus_idea_gate_paths": focus_idea_gate_review_candidates,
            "tooltip_script_resolution": tooltip_script_review_candidates,
            "unresolved_local_event_calls": local_unresolved_event_calls,
            "external_event_calls": external_calls,
            "unreachable_triggered_events": orphan_events,
        },
    }
