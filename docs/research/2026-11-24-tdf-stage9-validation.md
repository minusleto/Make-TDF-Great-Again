---
status: executed-static-validation
updated: 2026-11-25
scope: Unit tests, complete static auditor, all available country-specific auditor runs, and limited false-positive triage for TDF/MDC.
limits: Static validation only. The full HOI4 runtime, installed base-MD/DLC/mod load order, and in-game UI were not run.
---

# Stage 9 — executed validation (2026-11-24)

## Run and revision

- Repository: `minusleto/Make-TDF-Great-Again`, branch `main`.
- Final validated revision: [`e5da487f452452eb465ea8e88f0316e656c8c72b`](https://github.com/minusleto/Make-TDF-Great-Again/commit/e5da487f452452eb465ea8e88f0316e656c8c72b).
- GitHub Actions: first run [45470365586](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45470365586); registry revalidation run [45471844803](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45471844803).
- The workflow stores the full JSON/log and one JSON/log artifact per country for 14 days.
- Python version: 3.12.

## Changes required to execute validation

The local runtime could not clone the repository because DNS resolution for `github.com` failed. A bounded GitHub Actions workflow was therefore added:

1. [`696cec4`](https://github.com/minusleto/Make-TDF-Great-Again/commit/696cec466d2876210c6060ff158fa8d99789a8c1) added the workflow.
2. [`a00a5a6`](https://github.com/minusleto/Make-TDF-Great-Again/commit/a00a5a6c0ced648bf8fce27679d07ab0143ba1c8) fixed an incomplete no-registry report shape that raised `KeyError: registered_findings` in fixture runs.
3. [`b4fc59b`](https://github.com/minusleto/Make-TDF-Great-Again/commit/b4fc59b1cf08a57b580c360a814775e4eac8852e) split full and country audits into separate jobs; country jobs run in a bounded matrix with `fail-fast: false`.
4. [`7b5dcce`](https://github.com/minusleto/Make-TDF-Great-Again/commit/7b5dcce745e47b2a714c369b7ef95b771d6efbf7) corrected parser handling for anonymous list blocks in HOI4 files. Test assertions were corrected in [`8c35317`](https://github.com/minusleto/Make-TDF-Great-Again/commit/8c353174d1ba7a52eab3204716506359e73448e1) and [`e5da487`](https://github.com/minusleto/Make-TDF-Great-Again/commit/e5da487f452452eb465ea8e88f0316e656c8c72b).

No country/gameplay files were edited by these commits.

## Execution results

| Check | Result |
|---|---|
| Unit tests (`python -m unittest discover -s skills/tdf-country-content/tests -v`) | **PASS — 43 tests** |
| Full repository auditor | Executed; exit code 1 because an ERROR was found |
| ARM, BLR, ENG, GEO, HUN, ISR, KAZ, POL, POR, SLO, SOV, SYR | All 12 executed separately; each produced its report and returned exit code 1 because country ERROR findings remain |
| Workflow / artifact upload | Completed; full and per-country artifacts were uploaded |

Running the auditor is not the same as passing the content audit. Stage 9 remains open.

## Parser false-positive correction and remaining structural error

Before the parser change, the full report contained 45 parser findings across:

- `common/doctrines/grand_doctrines/air_grand_doctrines.txt`
- `common/doctrines/grand_doctrines/land_grand_doctrines.txt`
- `common/doctrines/grand_doctrines/sea_grand_doctrines.txt`

These files use valid anonymous list blocks under doctrine milestone lists. The parser incorrectly emitted “block without name” for each such item. The parser now retains the anonymous AST node but does not flag that syntax as malformed. The 45 false positives disappeared.

One parser finding remains:

- `mdredux/common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt:297`
- The `long_range_submarines = {` block is not closed before EOF.
- This is a structural game-content candidate. It was not fixed because this roadmap's scope does not permit editing country/gameplay content.

## Aggregate country findings

These counts are aggregated from the 12 country JSON reports. They identify audit findings, not 100% proven runtime failures:

| Check | Count |
|---|---:|
| Focus completion log ID mismatches | 220 |
| Focus completion rewards without log | 5 |
| Focus description keys missing from local English localisation | 735 |
| Focus title keys missing from local English localisation | 3 |
| Duplicate focus localisation keys | 48 |
| Duplicate scripted-localisation IDs | 2 |
| SOV swaps that use the same idea on both sides | 1 |
| Local focus event reference not resolved | 1 |
| Missing event option-name keys | 33 |
| Event options without `log` | 37 |
| Missing event title keys | 14 |
| Missing event description keys | 20 |

### Focus localisation

The 735 missing local focus description keys are concentrated in ENG (670) and KAZ (57); ARM, BLR, HUN, POL, SOV and SYR account for the remaining eight. Three focus title keys are missing locally: `ENG_affordable_housing`, `KAZ_wto`, `SOV_the_third_rome`. The SOV missing description example is `SOV_jirik_lustration_desc`.

One ENG example, `ENG_britain_road_socialism_desc`, is absent from the pinned upstream [`MD_focus_ENG_l_english.yml`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/04b2ba126fc1057bf2ab4bac0407b3235983994c/localisation/english/MD_focus_ENG_l_english.yml) at baseline SHA `04b2ba1`. This confirms that this particular key is not supplied by that pinned upstream file. The other missing keys still require source/override verification before any content patch.

The 48 duplicate focus localisation keys were compared across all 18 local English YML files:

- 26 keys have conflicting values (including five cross-file conflicts).
- 22 keys repeat the exact same value.
- The project standard in `file-formatting.md` requires unique keys across the available localisation set, so all 48 remain ERROR candidates. The repeated-identical subset is lower priority, not a false positive.

### Event and decision localisation

The 14 missing event title keys, 20 missing event descriptions and 33 missing option-name keys include candidates already recorded during Stage 1. Some may exist in the installed base MD/shared packages; verify against the target mod stack before editing local keys.

The event audit also found ten unresolved event-call candidates. One high-priority case is:

- Caller: `GEO_crucial_marriage`
- TDF focus path/line: `mdredux/common/national_focus/Georgia_Focus_Tree.txt:7901`
- Target: `georg_monarchist.14`
- No matching definition was found in TDF `mdredux/events/Georgia.txt` or pinned upstream `events/Georgia.txt` at SHA `04b2ba1`.

The target is recorded as `unknown`, not confirmed present or globally absent. Five SOV decision title keys are missing from the local English YML; their IDs and lines are in Issue #18.

### MIO, equipment and technology

- `GEO_stc_delta_materiel_manufacturer` has five call sites (three focus references and two Georgia event references) but no definition in the 57 local MIO organization files. Its existence in another installed mod remains unknown.
- Six MIO names match the ID of another MIO; ENG QinetiQ → BAE is one example. These are copy/paste candidates, not patches.
- Unknown equipment, module and technology IDs remain review candidates because the checkout does not contain the complete base MD, vanilla and DLC definitions.

## External dependency registry

At execution time, the registry had 17 entries (13 confirmed, 2 assumption, 2 unknown). The auditor emitted 1,017 dependency findings, of which 10 matched registry entries and 1,007 were unregistered/unknown candidates. Unregistered references did not become ERROR solely because they were absent from this checkout.

After the run, the unresolved GEO event `georg_monarchist.14` was added as an explicit `unknown` registry record, with the TDF call site and both local/upstream source checks. This post-run registry addition does not alter the recorded run output; the next workflow execution will validate the updated 18-entry registry.

## Limitations and remaining work

- This was static validation. HOI4 was not launched, tooltips/UI were not inspected, and runtime load order was not tested.
- The TDF checkout does not contain the complete base Millennium Dawn, vanilla and DLC. External IDs and localisation may resolve in a user's installed mod stack.
- All ERROR candidates still need triage; unresolved items must either be fixed in a separately authorised country-content task, explained with evidence, or retained as documented exceptions.
- The false-positive matrix is not fully complete. In particular, shared MIO, external event chains, hidden ideas, tooltip rendering, legacy IDs and disabled branches still need runtime/target-stack verification.
- Issue #18 remains open. No other issues or PRs were created.

## Follow-up validation and auditor hardening — 2026-11-25


Latest validation: [GitHub Actions run 45476073618](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45476073618), HEAD `ba6d38a88cb5c29fb774713927a55f5738536cbb`.

### Execution

- **Auditor/inventory unit tests: PASS — 47 tests.**
- **Full repository auditor: executed, exit code 1.** The report contains content ERROR candidates; this is the expected nonzero result, not an infrastructure or parser-launch failure.
- **Country matrix: 12/12 executed** (ARM, BLR, ENG, GEO, HUN, ISR, KAZ, POL, POR, SLO, SOV, SYR). Every country job uploaded its JSON/log artifact and returned exit code 1 because that country slice contains ERROR findings.
- **Structural inventory: PASS.** `tdf_inventory.py` ran even after the full auditor returned 1; `inventory.json` and `inventory.log` are included in the `tdf-full-audit` artifact.
- No country/gameplay files were modified.

### Structural inventory snapshot

| Item | Files / definitions |
|---|---:|
| Focus trees / focuses | 12 / 5,422 |
| Idea files / ideas | 15 / 2,601 (1,806 visible; 795 hidden) |
| Event files / events | 10 / 2,764 (2,606 country; 158 news) |
| Decision files / decisions | 6 / 279 (25 categories) |
| Scripted-localisation files / `defined_text` | 10 / 602 |
| MIO organization files / definitions | 57 / 401 |
| Technology files | 28 |
| Equipment files | 36 |

The inventory parser reported zero parse issues in the inventory's focus, idea, event, decision, scripted-localisation and MIO domains. This is a scoped inventory result, not proof that the entire repository parses or that the content works in-game.

### Auditor changes validated

- Global event checks now affect the auditor's exit code: missing event `title`, missing `desc`, missing option `name`, and missing option `log` are no longer only printed diagnostics. The option `log` check runs independently even when `name` is absent.
- The full report currently records 8 events without `title`, 8 without `desc`, 0 options without `name`, and 38 options without `log`. It also records 39 missing event title/description localisation keys and 35 missing option localisation keys.
- Added `--require-external-registry`; CI runs the auditor with this flag so a missing registry is a clear input error (exit code 2). Regression tests cover absent and valid registries.
- Idea-lifecycle discovery now includes extensionless files under `scripted_effects`, `scripted_triggers` and `on_actions`, avoiding false `not_locally_granted` candidates when an idea is granted from an extensionless scripted effect.
- The CI workflow now runs the structural inventory even when the full audit has content errors, and stores its output in the same artifact.
- The commands in the module docstring, `SKILL.md` and `AGENTS.md` now document strict registry validation.

### Remaining findings and limits

- The full report has one structural parse error at `mdredux/common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt:297` (`long_range_submarines` is not closed before EOF). It appears in both idea-source and state-flow diagnostics but is the same physical defect. The gameplay file remains untouched.
- Event audit: 10 unresolved local-reference candidates, 590 `is_triggered_only` reachability candidates, 8 duplicate event-localisation definitions, plus external references that cannot be proven absent without the full upstream stack.
- Dependency registry: 18 entries; 1,019 findings, of which 11 are registered and 1,008 remain unregistered candidates. Their status distribution is 6 confirmed, 2 assumption and 1,011 unknown. Most unknown references require comparison against the pinned complete base MD, vanilla and DLC; they are not automatically upgraded to ERROR.
- Other candidate groups remain for manual review: 5 missing local MIO references, 51 missing local MIO name localisations, 6 MIO-name collisions, 274 unknown equipment-type references, and 18 unknown technology references. These may resolve in the full installed mod stack.
- Static validation only: HOI4 was not launched; runtime scopes, UI/tooltips, DLC load order and the complete base MD were not available.

### Code changes

- `2261bb0` — make global event field errors actionable; add strict external-registry mode; require the registry in CI; add regression tests.
- `4ecf907` — check option logs even if the option name is missing.
- `0ef7ed8` — include extensionless scripted grants in idea lifecycle auditing.
- `2cd1376` — document strict validation in skill entrypoints.
- `ba6d38a` — execute and archive structural inventory in the validation workflow.

**Stage 9 remains open.** Execution and regression-test criteria are now met, but the content ERROR/WARN triage and false-positive/runtime matrix are not complete. Do not close Issue #18 or change the country gameplay content under this skill-only scope.
