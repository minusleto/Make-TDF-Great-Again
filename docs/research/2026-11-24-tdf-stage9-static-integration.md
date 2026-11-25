---
status: partial-static-review
updated: 2026-11-24
scope: Static cross-file review of the TDF main snapshot; no game files changed.
limits: Historical static review only; no HOI4 runtime, unit tests or full auditor run were performed. External-source confirmations in the original review are withdrawn by the 2026-11-26 correction below.
---

# Stage 9 — static integration review

> **Source-policy correction — 2026-11-26.** This historical review used a non-TDF upstream source for some dependency conclusions. That source is not approved for TDF. The CSTO and other external confirmations in this report are withdrawn. Exact TDF-local definitions remain confirmed only where the defining block exists in the repository; all other references are unknown until the target TDF source file is checked or supplied by the user.


## Result

**Partial; Stage 9 is not complete.** The review checks representative cross-file links and the documented routing/tests. It is not a substitute for executing the unit-test suite, the full repository auditor, per-country runs, or the game.

Reviewed repository snapshot: `main` at `5bd30427553b9c884c80cb6be30afcd96ea804b8` (2026-11-24).

## Representative country — ENG

The UK slice contains 862 focus blocks, 188 local event definitions, and 130 focus-to-event call sites.

A concrete focus → event → idea → localisation path resolves:

1. `United Kingdom_Focus_Tree.txt:265` defines `ENG_expanding_hospitals`; its completion logic schedules `britain_blair.2` (`...:298`).
2. `events/Britain.txt:1090` defines `britain_blair.2`; its option adds timed `ENG_pfi_crisis` for 365 days (`...:1101`).
3. `common/ideas/Britain_ideas.txt:306` defines `ENG_pfi_crisis`.
4. The ENG English localisation contains the event title/description/option keys and `ENG_pfi_crisis` (`MD_focus_ENG_l_english.yml:281,303`).

A separate focus → idea → decision link also resolves: `ENG_mixed_model` adds `ENG_mixed_house` (`United Kingdom_Focus_Tree.txt:1018,1035`); the idea is defined in `Britain_ideas.txt:398`; the UK decision logic checks that idea (`common/decisions/United Kingdom.txt:1659`).

Industry/equipment checks:

- Eight ENG MIO definitions are present in `MD_ENG_organizations.txt`; all eight `include` targets resolve to templates in `MD_generic_organization.txt`.
- The ENG country history uses `medium_tank_chassis_0/1/2` and `util_vehicle_equipment`; those archetypes are present in `MD_tank_chassis.txt` and `MD_utility_vehicle.txt`.
- The ENG focus-localisation file contains the focus IDs found in this tree except one local-slice candidate: `ENG_affordable_housing`. That ID is present in the focus tree (`United Kingdom_Focus_Tree.txt:7935`) but was not found in any of the 18 local English YML files. `ENG_affordable_housing_programme` is a different focus ID and is not a substitute. No approved TDF source file containing this key was present in the files checked, so it remains unresolved until the exact target localisation file is checked.
- `MD_ENG_organizations.txt:8-12` has a probable copy/paste mismatch: `ENG_qinetiq_materiel_manufacturer` uses `name = ENG_bae_land_systems_materiel_manufacturer`, the same name key as the preceding BAE MIO despite its QinetiQ icon and distinct MIO ID. Record for country-content review; not changed here.

## More complex country — ISR

The Israel tree has 667 focus blocks and 296 focus-to-event call sites (176 unique event IDs). Across the ten local event files, 171 unique IDs resolve locally; five do not:

- `md4.1`
- `md4.2`
- `md4.4`
- `generic.5`
- `TUR_flavor_event.8`

These are unresolved against the TDF files checked; do not infer an external source or global absence. The local Israeli ideas file contains 357 idea definitions. All 13 distinct idea IDs used as gates in the Israel decision file are defined locally. Seven Israeli MIO definitions were found, and every generic `include` target resolves in the shared generic MIO file.

## Missing local event/decision files — SLO and HUN

- Slovakia has a local focus tree (180 focus blocks), but no Slovakia event file and no Slovakia decision file in the current TDF directories. The focus tree references `slo_army.*`, `slo_foreign.*`, `slo_mechair.*` and `CSTO.1`. `CSTO.1` was previously confirmed using a source that is not approved for TDF; that confirmation is withdrawn. The `CSTO.1` and `slo_*` references remain unknown until their TDF definitions are checked.
- Hungary has a local focus tree and `common/decisions/hungary.txt`, but no local Hungary event file. Its many `hungary_*` event references therefore cannot be classified as local missing events from this slice alone. The registry's `CSTO.1` confirmation is withdrawn; Hungary references remain unknown until the relevant TDF source files are checked.

Absence from this repository slice is not sufficient evidence for an ERROR. Keep these references separate from broken IDs in a complete checkout.

## Existing regression-fixture coverage inspected

The current test file contains fixtures for:

- external event references versus missing local references (`test_event_reference_audit_scans_decisions_and_marks_missing_vs_external`, line 471);
- external event option labels and event-added ideas (`test_event_ideas_and_external_option_labels_are_classified_safely`, line 382);
- tooltip references that are not scripted calls (`test_effect_tooltips_are_not_calls_and_scripted_effects_are_uncertain_roots`, line 522);
- external decisions/events, timers and custom-cost patterns (`test_decision_audit_separates_external_refs_and_accepts_timer_and_custom_cost_patterns`, line 670);
- local/external MIO and equipment/variant indexing (`test_industry_audit_indexes_global_mio_equipment_and_variant_references`, line 705);
- hidden ideas, legacy IDs and static versus dynamic tooltip modes (`test_idea_lifecycle_audit_keeps_legacy_ids_and_checks_tooltip_modes`, line 836);
- positive flag/idea writer-reader links and a negative `NOT` reader (`test_state_flow_links_decisions_and_events_by_exact_positive_flag_and_idea_ids`, line 1080);
- editorial heuristics remaining WARN/INFO rather than ERROR (`test_editorial_heuristics_remain_warnings_or_info`, line 1294).

This is source/fixture inspection only. The tests have **not** been executed in this review. The disabled-branch and broader false-positive matrix still need a run against the complete checkout.

## Skill routing

Static route walkthroughs were checked for: a single focus/localisation edit, an event chain, a decision, MIO/equipment work, and whole-branch design. The index and primary skill route these to the matching domain reference; country cards are loaded only for represented tags. For HUN/SLO, where a card is not present, the index instructs the agent to work from current country files and not fill gaps with stereotypes.

## Blockers and exact remaining work

- The available environment has no repository checkout. Download/clone attempts failed at DNS resolution, so files could be inspected through GitHub but not assembled into a working checkout for execution.
- The repository has no `.github/workflows/` directory and no existing CI run to report.
- Unit tests were not run:
  `python3 -I -m unittest discover -s skills/tdf-country-content/tests -v`
- Full and per-country auditor runs were not run:
  `python3 -I skills/tdf-country-content/scripts/tdf_audit.py .`
  `python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .`
- Consequently, a complete ERROR/WARN triage and executed false-positive verification remain open. No PASS claim is made.
- No `mdredux/` game-content files were edited; no issue or PR was created.

## Changelog for this partial pass

- Added a dated static integration report and linked it from the root and research READMEs.
- Verified representative ENG, ISR and missing-local-file SLO/HUN cross-file patterns by reading current source files.
- Identified two ENG content candidates for Issue #18 only; did not edit country content.
- Left unit-test execution, full/per-country auditor execution, complete warning triage and Stage 9 completion pending.
