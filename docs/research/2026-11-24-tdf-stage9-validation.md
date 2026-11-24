---
status: executed-static-validation
updated: 2026-11-24
scope: Unit tests, complete static auditor, all available country-specific auditor runs, and limited false-positive triage for TDF/MDC.
limits: Static validation only. The full HOI4 runtime, installed base-MD/DLC/mod load order, and in-game UI were not run.
---

# Stage 9 — executed validation (2026-11-24)

## Run and revision

- Repository: `minusleto/Make-TDF-Great-Again`, branch `main`.
- Final validated revision: [`e5da487f452452eb465ea8e88f0316e656c8c72b`](https://github.com/minusleto/Make-TDF-Great-Again/commit/e5da487f452452eb465ea8e88f0316e656c8c72b).
- GitHub Actions: [run 45470365586](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45470365586).
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
