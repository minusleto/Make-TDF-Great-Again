"""Классификация находок (ERROR/WARN/INFO) и точка входа командной строки.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import argparse
import json
import sys
from typing import Optional, Sequence
from .connectivity import (
    build_branch_connectivity_audit,
)
from .core import (
    AuditInputError,
    reports_have_parse_errors,
)
from .country import (
    audit_country,
)
from .decisions import (
    build_decision_audit,
)
from .events import (
    build_event_audit,
)
from .external_dependencies import (
    build_external_dependency_audit,
    classify_confirmed_external_event_localisation,
    classify_confirmed_external_event_references,
    classify_confirmed_external_focus_localisation,
)
from .ideas import (
    build_idea_lifecycle_audit,
)
from .indexes import (
    build_content_indexes,
    build_global_indexes,
    discover,
)
from .industry import (
    build_industry_audit,
)
from .state_flow import (
    build_state_flow_audit,
)


ERRORS = [
    "parse_errors", "dup_focus_ids", "log_mismatch", "no_log", "prereq_missing",
    "mutex_missing", "relpos_missing", "title_missing", "desc_missing", "dup_loc_keys",
    "scripted_loc_duplicate", "swap_same_idea", "event_not_found",
    "event_option_label_missing", "event_option_no_log",
    "event_title_key_missing", "event_desc_key_missing",
]


WARNS = [
    "empty_reward", "nonstandard_filter", "hidden_branch_focus", "event_external",
    "dup_loc_keys_identical", "scripted_loc_duplicate_identical",
    "tech_bonus_no_uses", "title_gt30", "desc_lt150", "desc_gt340", "banned_phrase",
    "tooltip_only_reward", "event_generic_label", "event_label_gt35", "event_option_label_external",
    "foreign_tag_ref", "idea_not_found",
    "scripted_loc_missing", "scripted_loc_loc_missing", "scripted_loc_idea_missing", "scripted_loc_unused",
    "event_title_key_external", "event_desc_key_external",
]


INFOS = ["event_without_picture"]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Статический аудит HOI4/TDF country content")
    ap.add_argument("repo", nargs="?", default=".", help="корень репозитория (по умолчанию текущая папка)")
    ap.add_argument("--tags", help="список тегов через запятую, например POR,KAZ")
    ap.add_argument("--details", help="показать подробности проверок одной страны")
    ap.add_argument("--json", metavar="PATH", help="сохранить полный отчёт в UTF-8 JSON")
    ap.add_argument(
        "--require-external-registry", action="store_true",
        help="завершиться с ошибкой, если реестр внешних зависимостей отсутствует",
    )
    args = ap.parse_args(argv)

    try:
        countries, loc_index = discover(args.repo)
        all_focus, defined_events, defined_namespaces, event_parsed = build_global_indexes(countries, args.repo)
        content_indexes = build_content_indexes(args.repo, countries, loc_index)
        idea_report = build_idea_lifecycle_audit(args.repo, countries, loc_index, content_indexes, event_parsed)
        event_report = build_event_audit(
            args.repo, countries, loc_index, event_parsed, content_indexes, idea_report
        )
        decision_report = build_decision_audit(args.repo, countries, loc_index, all_focus, defined_events,
                                               defined_namespaces, event_parsed, content_indexes)
        industry_report = build_industry_audit(args.repo, countries, loc_index, all_focus, event_parsed)
        state_flow_report = build_state_flow_audit(args.repo, countries, event_parsed)
        external_dependency_report = build_external_dependency_audit(
            args.repo, event_report, decision_report, idea_report, industry_report, state_flow_report
        )
        classify_confirmed_external_event_references(event_report, external_dependency_report)
        classify_confirmed_external_event_localisation(event_report, external_dependency_report)
        if args.require_external_registry and not external_dependency_report.get("registry_available"):
            raise AuditInputError(
                "обязательный реестр внешних зависимостей не найден: {}".format(
                    external_dependency_report.get("registry_path", "docs/research/external-dependencies.json")
                )
            )
        wanted = [part.strip().upper() for part in args.tags.split(",") if part.strip()] if args.tags else sorted(countries)
        unknown = sorted(set(wanted) - set(countries))
        if unknown:
            ap.error("не найдены теги: {}. Доступны: {}".format(", ".join(unknown), ", ".join(sorted(countries))))
        if args.details and args.details.upper() not in wanted:
            ap.error("--details {} не входит в проверяемый набор тегов".format(args.details.upper()))
        results = {
            tag: audit_country(tag, countries[tag], loc_index, all_focus, set(countries), defined_events,
                               defined_namespaces, event_parsed, content_indexes)
            for tag in wanted
        }
        classify_confirmed_external_focus_localisation(results, external_dependency_report)
        branch_connectivity_report = build_branch_connectivity_audit(
            countries, event_report, idea_report, industry_report, state_flow_report,
            event_parsed, content_indexes, loc_index, tags=wanted,
        )

        columns = ["n_focus", "desc_median"] + ERRORS + WARNS + ["space_indent_lines", "brace_balance"]
        def short(name: str) -> str:
            return name.replace("_", " ")[:11]

        print("\t".join(["tag"] + [short(col) for col in columns]))
        for tag, result in results.items():
            row = [tag]
            for key in columns:
                value = result.get(key, 0)
                row.append(str(len(value)) if isinstance(value, list) else str(value))
            print("\t".join(row))
        print("\nERROR-проверки: " + ", ".join(ERRORS) + "\nWARN-проверки: " + ", ".join(WARNS))
        print("event_not_found — ссылка на ID в namespace, который объявлен в срезе, но не содержит такое событие.")
        print("event_external — namespace не найден в срезе; определение может находиться в файлах целевой сборки вне среза.")
        print("\nГлобальный аудит событий: {} определений (country_event {}, news_event {}), {} namespace.".format(
            event_report["counts"]["definitions"], event_report["counts"]["country_event"],
            event_report["counts"]["news_event"], event_report["counts"]["namespaces"]))
        print("\nАудит решений: {} файлов, {} категорий, {} решений.".format(
            decision_report["counts"]["files"], decision_report["counts"]["categories"],
            decision_report["counts"]["decisions"]))
        for key in ("parse_errors", "duplicate_category_ids", "duplicate_decision_ids",
                    "missing_category_localisation", "missing_decision_localisation",
                    "duplicate_localisation_definitions", "missing_tooltip_localisation",
                    "external_tooltip_localisation", "missing_decision_references",
                    "external_decision_references", "missing_focus_references",
                    "external_focus_references", "missing_event_references",
                    "external_event_references", "idea_reference_candidates",
                    "flag_reference_candidates", "missing_scripted_localisation",
                    "invalid_numeric_fields", "custom_cost_pair_issues", "custom_cost_conflicts",
                    "custom_cost_without_debit", "custom_cost_gate_only_candidates",
                    "repeatability_warnings",
                    "empty_effect_warnings", "condition_review_candidates", "mission_gate_review_candidates",
                    "decision_gate_conflicts", "nonnumeric_highlight_states", "unknown_highlight_states"):
            print("  decision {}: {}".format(key, len(decision_report[key])))
        print("  highlight states: {}, local state inventory available: {}".format(
            len(decision_report["highlight_state_references"]), decision_report["state_inventory_available"]))

        print("\nАудит MIO/техники: {} MIO-файлов, {} организаций, {} ссылок; {} equipment IDs, {} модулей, {} технологий; {} вариантов и {} выдач техники.".format(
            industry_report["counts"]["mio_files"], industry_report["counts"]["mio_definitions"],
            industry_report["counts"]["mio_references"], industry_report["counts"]["equipment_ids"],
            industry_report["counts"]["module_ids"], industry_report["counts"]["technology_ids"],
            industry_report["counts"]["equipment_variants"], industry_report["counts"]["stockpile_grants"]))
        for key in ("mio_parse_errors", "equipment_parse_errors", "module_parse_errors",
                    "technology_parse_errors", "duplicate_mio_ids", "missing_local_mio_references",
                    "external_mio_references", "missing_local_mio_name_localisation",
                    "external_mio_name_localisation_candidates", "mio_name_matches_other_mio",
                    "local_mio_visibility_focus_candidates", "duplicate_equipment_ids",
                    "unknown_equipment_type_references", "unknown_module_references",
                    "unknown_technology_references",
                    "invalid_stockpile_amounts", "local_equipment_localisation_candidates"):
            print("  industry {}: {}".format(key, len(industry_report[key])))

        print("\nВнешние зависимости: {} кандидатов; зарегистрировано {}, без записи в реестре {}; baseline {} @ {}.".format(
            external_dependency_report["counts"]["findings"],
            external_dependency_report["counts"]["registered_findings"],
            external_dependency_report["counts"]["unregistered"],
            external_dependency_report.get("baseline", {}).get("repository", "unknown"),
            external_dependency_report.get("baseline", {}).get("commit", "unknown")))
        print("\nАудит межфайлового состояния: {} файлов; {} history; {} scripted effects / {} calls; {} scripted triggers / {} calls; {} on_actions; {} flags, {} variables, {} arrays.".format(
            state_flow_report["counts"]["source_files"], state_flow_report["counts"]["history_files"],
            state_flow_report["counts"]["scripted_effect_definitions"], state_flow_report["counts"]["scripted_effect_calls"],
            state_flow_report["counts"]["scripted_trigger_definitions"], state_flow_report["counts"]["scripted_trigger_calls"],
            state_flow_report["counts"]["on_action_hooks"], state_flow_report["counts"]["flag_symbols"],
            state_flow_report["counts"]["variable_symbols"], state_flow_report["counts"]["array_symbols"]))
        print("  decision/event state links: {}".format(state_flow_report["counts"]["decision_event_state_links"]))
        for key in ("parse_errors", "script_parse_errors", "duplicate_scripted_effect_definitions",
                    "duplicate_scripted_trigger_definitions", "scripted_effects_without_local_call",
                    "scripted_triggers_without_local_call", "unresolved_scripted_call_candidates",
                    "potentially_unread_local_flags", "local_flags_read_without_writer",
                    "potentially_unread_local_variables", "local_variables_read_without_writer",
                    "potentially_unread_local_arrays", "local_arrays_read_without_writer",
                    "idea_on_add_without_matching_on_remove", "countries_without_local_history"):
            print("  state_flow {}: {}".format(key, len(state_flow_report[key])))
        print("  on_action inventory available: {}; scripted-trigger inventory available: {}; history inventory available: {}".format(
            state_flow_report["on_action_inventory_available"],
            state_flow_report["scripted_trigger_inventory_available"],
            state_flow_report["history_inventory_available"]))

        for key in ("parse_errors", "missing_event_ids", "missing_title_fields", "missing_desc_fields",
                    "missing_option_names", "duplicate_event_ids", "duplicate_namespaces",
                    "missing_localisation", "external_localisation", "duplicate_localisation_definitions",
                    "missing_option_localisation", "external_option_localisation", "generic_option_labels",
                    "long_option_labels", "options_without_log", "option_log_key_mismatches",
                    "missing_event_idea_candidates",
                    "missing_event_scripted_localisation", "reused_title_desc_keys",
                    "unresolved_references", "confirmed_external_references",
                    "external_references", "scripted_effect_references",
                    "unreachable_triggered_events",
                    "events_without_picture"):
            print("  {}: {}".format(key, len(event_report[key])))

        branch_counts = branch_connectivity_report["counts"]
        print("\nСвязность веток: {} focus, {} prerequisite, {} focus→event, {} event→event, {} focus→idea, {} event→idea, {} idea-tooltip, {} state handoff; {} review candidates.".format(
            branch_counts["focus_nodes"], branch_counts["focus_prerequisite_edges"],
            branch_counts["focus_event_edges"], branch_counts["event_event_edges"],
            branch_counts["focus_idea_grant_edges"] + branch_counts["focus_idea_gate_edges"],
            branch_counts["event_idea_grant_edges"], branch_counts["idea_tooltip_edges"],
            branch_counts["state_handoff_edges"], branch_counts["review_candidates"]))
        print("\nАудит нацдухов: {} файлов, {} идей (видимых {}, скрытых {}), {} ссылок.".format(
            idea_report["counts"]["idea_files"], idea_report["counts"]["definitions"],
            idea_report["counts"]["visible_ideas"], idea_report["counts"]["hidden_ideas"],
            idea_report["counts"]["idea_references"]))
        for key in ("parse_errors", "source_parse_errors", "duplicate_idea_ids", "missing_name_localisation",
                    "stage_name_links", "stage_swap_transitions", "stage_grant_without_swap_candidates",
                    "missing_local_idea_references", "external_idea_references",
                    "unresolved_unprefixed_idea_references", "not_locally_granted_candidates",
                    "custom_modifier_tooltip_missing_localisation",
                    "custom_modifier_tooltip_scripted_loc_candidates",
                    "custom_modifier_tooltip_static_key_candidates"):
            print("  ideas {}: {}".format(key, len(idea_report[key])))

        if args.details:
            tag = args.details.upper()
            result = results[tag]
            for key in ERRORS + WARNS + INFOS:
                if result.get(key):
                    print("\n[{}] {}".format(key, len(result[key])))
                    for item in result[key][:60]:
                        print("  ", item)
            flow = branch_connectivity_report.get("by_country", {}).get(tag, {})
            for key, items in flow.get("review_candidates", {}).items():
                if items:
                    print("\n[branch_connectivity:{}] {}".format(key, len(items)))
                    for item in items[:60]:
                        print("  ", item)

            gate_conflicts = [
                item for item in decision_report.get("decision_gate_conflicts", [])
                if item.get("owner_tag") == tag
            ]
            if gate_conflicts:
                print("\\n[decision_gate_conflicts] {}".format(len(gate_conflicts)))
                for item in gate_conflicts[:60]:
                    print("  ", item)

        if args.json:
            report_data = dict(results)
            report_data["_events"] = event_report
            report_data["_decisions"] = decision_report
            report_data["_industry"] = industry_report
            report_data["_ideas"] = idea_report
            report_data["_state_flow"] = state_flow_report
            report_data["_external_dependencies"] = external_dependency_report
            report_data["_branch_connectivity"] = branch_connectivity_report
            with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(report_data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")

        content_index_script_errors = [
            error
            for errors in content_indexes.get("script_parse_errors", {}).values()
            for error in errors
        ]
        registry_errors = (
            external_dependency_report.get("registry_available", False)
            and bool(external_dependency_report.get("registry_validation_issues"))
        )
        has_errors = any(result.get(key) for result in results.values() for key in ERRORS)
        has_errors = has_errors or reports_have_parse_errors(
            idea_report, event_report, decision_report, industry_report, state_flow_report,
            {"script_parse_errors": content_index_script_errors},
        ) or registry_errors
        has_errors = has_errors or bool(
            event_report["missing_event_ids"]
            or event_report["duplicate_event_ids"]
            or event_report["unresolved_references"]
            or event_report["missing_localisation"]
            or event_report["missing_option_localisation"]
            or event_report["missing_title_fields"]
            or event_report["missing_desc_fields"]
            or event_report["missing_option_names"]
            or event_report["options_without_log"]
        )
        same_file_category_duplicates = any(
            item["scope"] == "same_file" for item in decision_report["duplicate_category_ids"]
        )
        has_errors = has_errors or bool(same_file_category_duplicates
                                         or decision_report["duplicate_decision_ids"]
                                         or decision_report["missing_category_localisation"]
                                         or decision_report["missing_decision_localisation"]
                                         or decision_report["invalid_numeric_fields"]
                                         or decision_report["missing_decision_references"]
                                         or decision_report["missing_focus_references"]
                                         or decision_report["missing_event_references"])
        return 1 if has_errors else 0
    except AuditInputError as exc:
        print("ОШИБКА: {}".format(exc), file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("ОШИБКА чтения входных данных / JSON: {}".format(exc), file=sys.stderr)
        return 2
