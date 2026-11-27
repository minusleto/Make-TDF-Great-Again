"""Аудит внешних зависимостей и сверка с реестром.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import json
from collections import Counter
from pathlib import Path
from .core import (
    AuditInputError,
    read,
)


EXTERNAL_DEPENDENCY_STATUSES = frozenset({"confirmed", "assumption", "unknown"})


EXTERNAL_DEPENDENCY_DEFAULT_SOURCE = (
    "Not verified in the available TDF source files; request the relevant target file from the user."
)


EXTERNAL_DEPENDENCY_DEFAULT_SOURCES = {
    key: EXTERNAL_DEPENDENCY_DEFAULT_SOURCE
    for key in (
        "event", "idea", "scripted_effect", "scripted_trigger",
        "scripted_effect_or_trigger", "localisation", "scripted_localisation",
        "mio", "equipment", "equipment_module", "technology", "decision", "focus", "other",
    )
}


def build_external_dependency_audit(repo, event_report, decision_report, idea_report,
                                    industry_report, state_flow_report):
    """Match unresolved references against the TDF dependency registry.

    This report is diagnostic, not an allowlist. A confirmation is trusted only
    when its provenance is an approved TDF-local or user-provided source file.
    Unregistered or invalidly confirmed references remain visible as unknown.
    """
    registry_path = Path(repo) / "docs" / "research" / "external-dependencies.json"
    relative_registry_path = "docs/research/external-dependencies.json"
    if not registry_path.is_file():
        return {
            "registry_available": False, "registry_path": relative_registry_path,
            "registry_validation_issues": ["external dependency registry is missing"],
            "project_scope": {}, "findings": [], "unregistered_candidates": [],
            "counts": {
                "registry_entries": 0, "findings": 0, "registered_findings": 0,
                "unregistered": 0, "by_status": {}, "by_type": {},
            },
        }

    try:
        registry = json.loads(read(registry_path))
    except (ValueError, TypeError) as exc:
        raise AuditInputError("{}: некорректный JSON реестра внешних зависимостей: {}".format(
            registry_path, exc
        )) from exc
    if not isinstance(registry, dict):
        raise AuditInputError("{}: корень реестра должен быть JSON object".format(registry_path))

    validation_issues = []
    if registry.get("schema_version") != 1:
        validation_issues.append("unsupported schema_version: {!r}".format(registry.get("schema_version")))
    entries = registry.get("dependencies")
    if not isinstance(entries, list):
        raise AuditInputError("{}: поле dependencies должно быть массивом".format(registry_path))

    registry_index = {}
    valid_entries = []
    for index, dependency in enumerate(entries):
        if not isinstance(dependency, dict):
            validation_issues.append("dependencies[{}] is not an object".format(index))
            continue
        dep_type, dep_id, status = (
            dependency.get("type"), dependency.get("id"), dependency.get("status")
        )
        if not isinstance(dep_type, str) or not dep_type.strip() or not isinstance(dep_id, str) or not dep_id.strip():
            validation_issues.append("dependencies[{}] needs non-empty type and id".format(index))
            continue
        if status not in EXTERNAL_DEPENDENCY_STATUSES:
            validation_issues.append("dependencies[{}] has unsupported status {!r}".format(index, status))
            continue
        dependency = dict(dependency)
        if status == "confirmed":
            origin = dependency.get("verification_origin")
            verification = dependency.get("verification")
            exact_file_evidence = False
            if isinstance(verification, list):
                for evidence in verification:
                    if not isinstance(evidence, dict):
                        continue
                    path = evidence.get("path")
                    if not isinstance(path, str) or not path.strip():
                        continue
                    normalized_path = path.strip().replace("\\", "/")
                    if origin == "tdf_local" and not normalized_path.startswith("mdredux/"):
                        continue
                    exact_file_evidence = True
                    break
            if origin not in ("tdf_local", "user_provided") or not exact_file_evidence:
                validation_issues.append(
                    "dependencies[{}] is confirmed without approved provenance and an exact source-file path".format(index)
                )
                dependency["status"] = "unknown"
                dependency.pop("verification_origin", None)
                dependency["verification"] = []
                dependency["notes"] = (
                    "Previous confirmation rejected: no approved TDF-local or user-provided "
                    "source file was recorded. Keep unknown until the exact definition is checked."
                )
                status = "unknown"
        if not isinstance(dependency.get("checked_at"), str) or not dependency.get("checked_at"):
            validation_issues.append("dependencies[{}] needs checked_at".format(index))
        if not isinstance(dependency.get("expected_source"), str) or not dependency.get("expected_source"):
            validation_issues.append("dependencies[{}] needs expected_source".format(index))
        key = (dep_type, dep_id)
        if key in registry_index:
            validation_issues.append("duplicate registry entry: {} {}".format(dep_type, dep_id))
            continue
        registry_index[key] = dependency
        valid_entries.append(dependency)

    grouped = {}

    def add_reference(dep_type, identifier, reference):
        if not isinstance(identifier, str) or not identifier.strip():
            return
        identifier = identifier.strip()
        key = (dep_type, identifier)
        dependency = registry_index.get(key)
        item = grouped.get(key)
        if item is None:
            item = {
                "type": dep_type, "id": identifier,
                "status": dependency.get("status") if dependency else "unknown",
                "registry_status": "registered" if dependency else "unregistered",
                "expected_source": (
                    dependency.get("expected_source") if dependency
                    else EXTERNAL_DEPENDENCY_DEFAULT_SOURCES.get(
                        dep_type, EXTERNAL_DEPENDENCY_DEFAULT_SOURCES["other"]
                    )
                ),
                "checked_at": dependency.get("checked_at") if dependency else None,
                "verification_origin": dependency.get("verification_origin") if dependency else None,
                "verification": dependency.get("verification", []) if dependency else [],
                "notes": dependency.get("notes") if dependency else (
                    "No exact registry record. Treat as unknown until the matching TDF "
                    "or user-provided target source file is checked."
                ),
                "references": [],
            }
            grouped[key] = item
        normalized = {
            field: value for field, value in reference.items()
            if value is not None and value != ""
        }
        if normalized not in item["references"]:
            item["references"].append(normalized)

    # External event calls and their external localisation keys.
    for reference in event_report.get("external_references", []):
        add_reference("event", reference.get("target"), {
            "path": reference.get("source"), "line": reference.get("line"),
            "source_kind": reference.get("source_kind"), "caller": reference.get("caller"),
            "classification": "namespace_not_defined_in_local_checkout",
        })
    # A local namespace declaration does not prove every referenced ID is defined in the
    # available TDF files. Keep each exact unresolved ID unknown until its source is checked.
    for reference in event_report.get("unresolved_references", []):
        if reference.get("kind") not in ("country_event", "news_event"):
            continue
        add_reference("event", reference.get("target"), {
            "path": reference.get("source"), "line": reference.get("line"),
            "source_kind": reference.get("source_kind"), "caller": reference.get("caller"),
            "lifecycle": reference.get("lifecycle"),
            "classification": "id_missing_from_local_definition_but_namespace_is_declared",
        })
    for list_key in ("external_localisation", "external_option_localisation"):
        for reference in event_report.get(list_key, []):
            add_reference("localisation", reference.get("key"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "event_localisation", "caller": reference.get("event_id"),
                "field": reference.get("field"),
            })
    for reference in event_report.get("missing_event_idea_candidates", []):
        if reference.get("classification") == "external_or_cross_country_candidate":
            add_reference("idea", reference.get("idea"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "event", "caller": reference.get("event_id"),
                "classification": reference.get("classification"),
            })

    # External references made by decisions.
    for reference in decision_report.get("external_tooltip_localisation", []):
        add_reference("localisation", reference.get("key"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "decision_localisation", "caller": reference.get("decision"),
        })
    for list_key, dep_type in (
        ("external_event_references", "event"),
        ("external_focus_references", "focus"),
        ("external_decision_references", "decision"),
    ):
        for reference in decision_report.get(list_key, []):
            add_reference(dep_type, reference.get("target"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "decision", "caller": reference.get("decision"),
                "field": reference.get("field"),
            })

    # External / shared ideas, including IDs without a three-letter country prefix.
    for reference in idea_report.get("external_idea_references", []):
        add_reference("idea", reference.get("idea"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "idea_reference", "usage": reference.get("usage"),
        })
    for reference in idea_report.get("unresolved_unprefixed_idea_references", []):
        add_reference("idea", reference.get("idea"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "idea_reference", "usage": reference.get("usage"),
            "classification": "unprefixed_or_shared_idea_candidate",
        })

    # MIO, equipment, equipment modules and technology references.
    for list_key in ("external_mio_references", "missing_local_mio_references"):
        for reference in industry_report.get(list_key, []):
            add_reference("mio", reference.get("mio"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "mio_reference", "usage": reference.get("usage"),
                "classification": (
                    "external_tag_candidate" if list_key == "external_mio_references"
                    else "local_tag_missing_in_checkout_or_base_dependency"
                ),
            })
    for reference in industry_report.get("external_mio_name_localisation_candidates", []):
        add_reference("localisation", reference.get("name_key"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "mio_name", "caller": reference.get("mio"),
        })
    for reference in industry_report.get("unknown_equipment_type_references", []):
        add_reference("equipment", reference.get("type"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": reference.get("action"), "caller": reference.get("variant"),
            "classification": "not_defined_in_local_equipment_slice",
        })
    for reference in industry_report.get("unknown_module_references", []):
        add_reference("equipment_module", reference.get("module"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "create_equipment_variant", "caller": reference.get("variant"),
            "classification": "not_defined_in_local_module_slice",
        })
    for reference in industry_report.get("unknown_technology_references", []):
        add_reference("technology", reference.get("technology"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": reference.get("command"),
            "classification": reference.get("classification"),
        })

    # Unresolved scripted calls remain candidates until the matching TDF source is checked.
    for reference in state_flow_report.get("unresolved_scripted_call_candidates", []):
        add_reference("scripted_effect_or_trigger", reference.get("candidate"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "scripted_call", "owner_tag": reference.get("owner_tag"),
            "classification": reference.get("classification"),
        })

    # Include explicit TDF usage entries even when the shared definition resolves locally.
    for dependency in valid_entries:
        for reference in dependency.get("where_used", []):
            if reference.get("repository") == "TDF":
                add_reference(dependency["type"], dependency["id"], {
                    **reference, "source_kind": "registry_usage",
                })

    # Expand only declared transitive dependencies (e.g. a scripted effect invoked by a
    # base event), and only if the parent is referenced by this checkout.
    used_keys = set(grouped)
    for dependency in valid_entries:
        for parent in dependency.get("related_to", []):
            if (parent.get("type"), parent.get("id")) in used_keys:
                add_reference(dependency["type"], dependency["id"], {
                    "source_kind": "transitive_dependency", "related_to": parent,
                })

    findings = sorted(grouped.values(), key=lambda item: (item["type"], item["id"].casefold()))
    for item in findings:
        item["references"].sort(key=lambda reference: (
            reference.get("path", ""), reference.get("line", 0),
            reference.get("source_kind", ""), reference.get("caller", "")
        ))
    unregistered = [item for item in findings if item["registry_status"] == "unregistered"]
    status_counts = Counter(item["status"] for item in findings)
    type_counts = Counter(item["type"] for item in findings)
    return {
        "registry_available": True, "registry_path": relative_registry_path,
        "schema_version": registry.get("schema_version"),
        "last_reviewed": registry.get("last_reviewed"),
        "project_scope": registry.get("project_scope", {}),
        "registry_validation_issues": validation_issues,
        "registry_entries": valid_entries, "findings": findings,
        "unregistered_candidates": unregistered,
        "counts": {
            "registry_entries": len(valid_entries), "findings": len(findings),
            "registered_findings": len(findings) - len(unregistered),
            "unregistered": len(unregistered),
            "by_status": dict(sorted(status_counts.items())),
            "by_type": dict(sorted(type_counts.items())),
        },
    }


def has_approved_confirmation(item):
    """Return True only for an exact confirmation with approved source provenance."""
    if not isinstance(item, dict) or item.get("status") != "confirmed":
        return False
    origin = item.get("verification_origin")
    if origin not in ("tdf_local", "user_provided"):
        return False
    verification = item.get("verification")
    if not isinstance(verification, list):
        return False
    for evidence in verification:
        if not isinstance(evidence, dict):
            continue
        path = evidence.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        normalized_path = path.strip().replace("\\", "/")
        if origin == "tdf_local" and not normalized_path.startswith("mdredux/"):
            continue
        return True
    return False


def classify_confirmed_external_event_references(event_report, external_dependency_report):
    """Move only exact event IDs confirmed by an approved TDF source out of local missing-ID errors."""
    confirmed_event_ids = {
        item.get("id")
        for item in external_dependency_report.get("findings", [])
        if item.get("type") == "event" and has_approved_confirmation(item)
    }
    confirmed, unresolved = [], []
    for reference in event_report.get("unresolved_references", []):
        target = reference.get("target")
        if reference.get("kind") in ("country_event", "news_event") and target in confirmed_event_ids:
            confirmed.append({
                **reference,
                "resolution": "confirmed_external_definition",
                "registry_status": "confirmed",
            })
        else:
            unresolved.append(reference)
    event_report["confirmed_external_references"] = confirmed
    event_report["unresolved_references"] = unresolved
    return event_report


def classify_confirmed_external_focus_localisation(results, external_dependency_report):
    """Move only exact focus localisation keys confirmed by an approved TDF source out of local missing-key errors."""
    confirmed_keys = {
        item.get("id")
        for item in external_dependency_report.get("findings", [])
        if item.get("type") == "localisation"
        and has_approved_confirmation(item)
        and any(
            reference.get("repository") == "TDF"
            and "/common/national_focus/" in (reference.get("path") or "").replace("\\", "/")
            for reference in item.get("references", [])
        )
    }
    for tag, result in results.items():
        resolved = []
        for field, suffix in (("title_missing", ""), ("desc_missing", "_desc")):
            for focus_id in list(result.get(field, [])):
                key = focus_id + suffix
                if key in confirmed_keys:
                    result[field].remove(focus_id)
                    resolved.append({
                        "tag": tag, "focus_id": focus_id, "key": key,
                        "field": "title" if field == "title_missing" else "desc",
                        "resolution": "confirmed_external_focus_localisation",
                    })
        result["confirmed_external_localisation"] = resolved
    return results


def classify_confirmed_external_event_localisation(event_report, external_dependency_report):
    """Move only exact event localisation keys confirmed by an approved TDF source out of local missing-key errors."""
    confirmed_keys = {
        item.get("id")
        for item in external_dependency_report.get("findings", [])
        if item.get("type") == "localisation"
        and item.get("status") == "confirmed"
        and any(
            reference.get("repository") == "TDF"
            and "/events/" in (reference.get("path") or "").replace("\\", "/")
            for reference in item.get("references", [])
        )
    }
    resolved = []
    for field in ("missing_localisation", "missing_option_localisation"):
        for item in list(event_report.get(field, [])):
            key = item.get("key")
            if key in confirmed_keys:
                event_report[field].remove(item)
                resolved.append({
                    **item,
                    "resolution": "confirmed_external_event_localisation",
                })
    event_report["confirmed_external_localisation"] = resolved
    return event_report
