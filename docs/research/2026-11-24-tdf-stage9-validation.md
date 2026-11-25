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


## Follow-up triage and false-positive refinement — 2026-11-25

Latest fully validated auditor snapshot: [GitHub Actions run 45590206276](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45590206276), HEAD [91d56ba](https://github.com/minusleto/Make-TDF-Great-Again/commit/91d56ba408197b651c3e9796fca7c7b86604f5e9).

### CI execution

- **57/57 unit tests passed.**
- **14/14 GitHub Actions jobs succeeded:** unit tests, full repository report and all 12 country reports.
- The full auditor still returns content exit code **1**; CI deliberately preserves JSON/log artifacts in report-only mode. Successful workflow jobs do not mean the content itself has zero ERROR findings.
- HOI4 runtime, actual mod load order, UI and tooltip rendering were not executed.

### Confirmed false-positive classes fixed in the auditor

- Duplicate focus-localisation keys are divided by value: identical duplicate values are WARN; differing values remain ERROR. Identical duplicate `defined_text` definitions are also separated from conflicting definitions.
- Exact event IDs with `status = confirmed` in the dependency registry are classified as `confirmed_external_references`, even where TDF declares the namespace but the exact event definition is supplied by pinned base MD. Only exact confirmed IDs are filtered; `unknown`, `assumption` and unregistered IDs remain unresolved.
- Conditional event `title = { ... text = KEY }` and `desc = { ... text = KEY }` blocks are now indexed and all nested text keys are checked. Events with `hidden = yes` are not required to carry UI title/description. Normal visible events without title/description remain errors.
- Exact confirmed upstream localisation keys are distinguished from genuinely unverified keys. Fallback filtering is source-typed: focus keys resolve focus `title_missing/desc_missing` only when their TDF usage is under `common/national_focus/`; event keys resolve event missing-localisation findings only when their TDF usage is under `events/`. Cross-type matches, `unknown`, `assumption` and unregistered keys do not suppress findings.

### Current full-report snapshot (run 45590206276)

| Finding | Result |
|---|---:|
| Missing event title fields | 0 |
| Missing event description fields | 0 |
| Missing event title/description localisation keys | 37 |
| Missing event option localisation keys | 32 |
| Exact confirmed event localisation fallbacks | 5 |
| Exact confirmed external event definitions | 8 |
| Remaining unresolved event calls | 5 |
| Missing focus descriptions in local TDF YML | 727 |
| Missing focus titles in local TDF YML | 2 |
| Exact confirmed base focus localisation fallbacks | 9 |
| Event options without a log | 38 |
| Event option standard-log ID mismatch WARN candidates | 245 |
| Triggered-event reachability candidates | 583 |
| Parser errors | 1 physical unclosed block |

The full report was produced before the final five SOV decision-title candidates were added to the registry as `unknown`. At the time of that run, the registry had 46 entries (37 confirmed, 2 assumption, 7 unknown) and the report contained 1,031 dependency findings (39 registered and 992 unregistered candidates). The registry now has **51 entries** (37 confirmed, 2 assumption, 12 unknown); a subsequent workflow run is required to refresh the report's registry finding counts. Entry counts and finding counts are different measures.

### Confirmed base-MD event references

Seven external event definitions were verified at pinned MD commit `04b2ba126fc1057bf2ab4bac0407b3235983994c`: `arm_foreign_legion.3`, `arm_foreign_legion.6`, `sov_gru.1`, `sov_gru.4`, `sov_nationalists.51`, `sov_nationalists.53` and `sov_final_strike.2`. Combined with the two local `mdc4.13/.16` generic event definitions, the report resolves these exact IDs without treating the local namespace as proof that every ID must be defined locally.

Five calls remain unresolved: `georg_monarchist.14`, `russia.3`, two uses of `russia.4`, and `syria_bashar.8`. They remain unknown; absence from the pinned files checked is not proof that no other enabled package/version supplies them.

### Exact confirmed localisation fallbacks

The dependency registry records 14 exact confirmed fallback keys that explain findings in the local TDF slice without changing TDF files:
- Focus localisation: eight descriptions (ENG ×5, ARM ×1, BLR ×2) and SOV title `SOV_the_third_rome`.
- Event localisation: three ISR keys (`israel_economy.38.b`, `israel_likud.26.a`, `israel_news.8.o6`) and two SOV descriptions (`sov_nationalists.20.d/.21.d`).

These confirm that the exact English keys exist in pinned MD. They do not confirm that upstream wording is suitable for TDF or that the user's target mod stack loads that precise baseline.

### Remaining content candidates

- One parser error remains at `mdredux/common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt:297`: `long_range_submarines = {` is not closed before EOF. It is one physical defect reported by more than one subsystem. It was not edited.
- Two focus title candidates remain: `ENG_affordable_housing` and `KAZ_wto`. The SOV `SOV_the_third_rome` title is now a confirmed upstream fallback. The large remaining desc count is concentrated in older or out-of-scope focus content (notably ENG 665 and KAZ 57); these findings are not automatically classified as defects.
- Five SOV decision titles remain absent from local English YML and were not found in the pinned MD decision, decision-flags, SOV-focus or event localisation files checked: `SOV_pmc_wagner_africe_goes` (Russia.txt:1807), `SOV_pmc_wagner_africe_goes_home` (:1864), `SOV_pmc_wagner_africe_perevorot_pipa` (:1912), `SOV_pmc_wagner_africe_perevorot_car` (:1998), `SOV_pmc_gazprom_goes` (:2085). They are registered as `unknown`, not globally missing.
- KAZ active Army/CAS scope still has five options without log: `kaz_army.7.a`, `kaz_army.7.b`, `kaz_army.8.a`, `kaz_cas.32.a` and `kaz_cas.33.a`. The other 22 KAZ options without log belong to legacy/out-of-scope event series. KAZ has one separate option-log mismatch in `KAZ_alash.2`; its 57 focus-description candidates belong to older economy / OTAN / Nazarbayev / Tokayev families, not active Army, Diplomacy or CAS.
- Other local-slice candidates include five `GEO_stc_delta_materiel_manufacturer` references, the `KAZ_strategic_partnership_china_loc` scripted-localisation candidate, 274 unknown equipment-type references and 18 unknown technology references. These cannot be conclusively classified without the complete target MD/vanilla/DLC stack.

### Stage 9 status

**Stage 9 remains open.** Auditor false-positive handling and test coverage improved, but complete content ERROR/WARN triage and the false-positive/runtime matrix are not finished. No HOI4 runtime was launched. No country gameplay files were changed, and no new issue or PR was created.


**Актуализация 2026-11-25 — коммит [902e124](https://github.com/minusleto/Make-TDF-Great-Again/commit/902e12434b30904df38f66f528cef9f31207211f), workflow [45602234704](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45602234704):**

- 58/58 unit tests прошли за 1,315 секунды; новый `test_decision_gate_conflicts_are_warn_only_and_skip_or_alternatives` прошёл вместе с существующими MIO/equipment, event, hidden/legacy idea, tooltip и disabled-branch fixtures.
- Все 14/14 CI jobs завершились `success`: unit tests/inventory, полный аудит и 12 страновых jobs. Полный аудит запустился и сохранил report artifact; его exit code — `1` из-за content ERROR findings (report-only), не из-за parser/test/CI failure.
- В полном checkout: 6 decision files / 25 categories / 279 decisions; `decision_gate_conflicts = 0`, `condition_review_candidates = 25`. Ноль конфликтов означает, что эвристика не нашла совпадающих обязательных предикатов с противоположной полярностью в текущих решениях; это не доказывает общую логическую выполнимость условий.
- MIO/equipment inventory: 57 files / 401 organizations, 414 equipment IDs, 719 modules, 993 technologies, 381 variants, 431 stockpile grants. Ideas: 15 files / 2,601 definitions / 9,054 references. External registry: 1,036 findings, 44 matched/registered, 992 not registered; missing entries remain candidates, not automatic errors.
- Full auditor still reports the existing one parser error in `navy_submarine_doctrines.txt:297` and other content candidates documented in this report. No country/gameplay files were modified; no in-game runtime was launched.


**Актуализация Stage 9 — 25.11.2026, commit [71b274e](https://github.com/minusleto/Make-TDF-Great-Again/commit/71b274ee0688d7a5bb3c8a38f6beb660a743b898), workflow [45603368266](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45603368266):**

- CI полностью завершён: **14/14 jobs success**, unit suite **58/58 OK**. Полный auditor сохранил отчёт с report-only exit code `1` из-за content findings; это не сбой тестов или workflow.
- Новый idea-lifecycle index: **659** stage-name relationships, **588** найденных transitions внутри `swap_ideas`, **23** прямые выдачи stage-idea без найденного `swap_ideas` add-transition. Последние — WARN/review candidates, не доказанные ошибки.
- Повторный полный inventory не изменил общий масштаб: 5,422 focus; 2,783 event definitions; 279 decisions; 401 MIO definitions; 2,601 idea definitions / 9,054 idea references; 246 межфайловых source files; 99 state handoffs.

#### Triage matrix for the current checkout

| Класс | Результат текущего статического среза | Как классифицировать |
|---|---|---|
| Парсер | Один незакрытый block в common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt:297; один и тот же физический дефект появляется в двух подсистемах | Подтверждённая структурная ошибка checkout; не исправлять в общем skills issue, зафиксировать владельцу игрового файла |
| Локальные межфайловые ссылки | Один GEO вызов georg_monarchist.14 не разрешается при локально объявленном namespace; один duplicate scripted-effect ID KAZ_upgrade_drone_program; один SOV swap_same_idea no-op candidate | Сильные локальные кандидаты для отдельного content review; не делать игровых правок в этом issue |
| Локализация событий/решений/идей | 37 missing event localisation entries, 32 missing option localisation entries, 5 decision localisation entries, 135 missing idea-name localisation candidates; часть ключей уже подтверждается в pinned MD | Проверять по registry и целевому load order; отсутствие в локальном checkout не равняется runtime missing |
| Внешние идеи/скрипты/техника | 1,070 local-slice idea refs без локального definition, 492 scripted-call candidates, 274 unknown equipment-type refs, 18 unknown technology refs; 5 missing local MIO refs (GEO STC family) | В основном dependency candidates: сверять полный MD/vanilla/DLC и внешние определения, не повышать автоматически до ERROR |
| Финансовые decision patterns | 5 custom-cost pair candidates, 1 конфликт с явно отображаемой второй ценой, 18 custom-cost-without-debit кандидатов, 1 threshold-only gate; 6 обычных constant-false condition candidates и 19 mission-gate candidates; direct visible/available opposite-atom conflicts = 0 | Проверять реальные price/debit пары и условия запуска миссий; gate-only, non-clickable missions и отсутствие очевидного debit не считать автоматически ошибками |
| Идеи и state lifecycle | 15 one-sided on_add state-change candidates, 28 local flag reads without local writer, 8 variable reads without local writer; 5 countries без локального history | Проверять scripted/external effects, shared history и intended lifecycle; это не доказательство отсутствующей инициализации |
| Стиль и визуал | Длинные/короткие focus descriptions и option labels, generic option labels, 150 events без picture, duplicate localization keys | Рекомендательные или review findings; нельзя массово переписывать контент по порогу |

**Граница аудита:** текущая задача Issue #18 — улучшить общие инструкции и надёжность классификации. Указанные country/content кандидаты не являются разрешением редактировать игровые файлы. Полный error/warn triage по каждому элементу остаётся открытым; неизвестные внешние зависимости и runtime-поведение не объявляются ошибками без соответствующего полного стека и проверки в игре.


### Category-level decision gates (25.11.2026)

HOI4 decision categories can define parent-level `allowed` and `visible` gates. A child decision only appears/is available when the corresponding category-level and decision-level conditions are fulfilled. Therefore an `original_tag = SOV` filter on a category is sufficient for all decisions inside it; do not repeat the same static gate inside every child. A decision-level `allowed` remains useful for an additional narrower restriction. `allowed` is checked at game start/save load; dynamic conditions belong in `visible`/`available`. Reference: [HOI4 Wiki — Decision modding](https://github.com/thelight0211/hoi4-wiki/blob/main/Decision%20modding%20-%20Hearts%20of%20Iron%204%20Wiki.md).

Auditor output now exposes `category_metadata` and `category_has_allowed` alongside each decision's own `has_allowed`, so reviewers can distinguish parent and child gates. Regression fixtures cover both a child relying on its category gate and a child with an additional `allowed`. Full workflow [45605594176](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45605594176) passed 58/58 unit tests and all 14/14 jobs. In the current TDF checkout, 0/25 decision categories define category-level `allowed`; 31/279 individual decisions define their own. No gameplay files were edited.


### Decision-auditor classification refinement — 25.11.2026

Последний прогон на [92c410c](https://github.com/minusleto/Make-TDF-Great-Again/commit/92c410c8cfc14b1b053b126195a76aa185653617), [workflow 45607362477](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45607362477): **61/61 unit tests OK; 14/14 CI jobs success**. Full auditor по-прежнему использует report-only exit code 1 для content findings; тесты и workflow не падают.

- Category metadata теперь привязана к конкретному блоку категории по строке определения, поэтому повторные category IDs в одном файле не смешивают списки дочерних решений. Regression test покрывает два блока с одинаковым ID.
- 25 категорий / 279 решений: ни одна категория текущего checkout не задаёт собственный allowed; 31 решение задаёт свой. При этом category-level gate остаётся допустимым общим фильтром всех дочерних решений.
- Автомиссии с activation + days_mission_timeout и available = { always = no } выведены из generic dead-condition candidates: 19 mission-gate review candidates отдельно, 6 обычных condition candidates остаются.
- Custom-cost triage: 1 отображаемый custom-cost конфликт, 22 custom-cost-without-debit candidates, 1 threshold-only requirement candidate. Сочетание стандартного cost и простого eligibility trigger без custom text больше не считается автоматически второй ценой.
- Прямые противоположные атомарные предикаты между visible и available: 0.

Страновые игровые файлы не изменялись. Содержательная проверка конкретных оставшихся кандидатов, технологических unlocks и runtime на полной сборке остаётся открытой.


### Equipment technology unlock index — 25.11.2026

Коммит [80f6624](https://github.com/minusleto/Make-TDF-Great-Again/commit/80f6624ed765eba4bcce136532ba6c1f182def28), workflow [45616388016](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45616388016): аудитор читает прямые unlock-поля `enable_equipments` и `enable_equipment_modules` в локальных technology definitions и связывает найденные технологии с `create_equipment_variant.type` и каждым module slot.

- В локальных technology files найдено **1,181** direct equipment/module unlock references.
- Из **381** equipment variants у **323** есть хотя бы один локальный unlock для типа техники; у **58** локального type unlock в текущем TDF slice не найдено.
- **7** вариантов содержат `allow_without_tech = yes`; все 7 имеют локально найденную технологию для своего type.
- Это не доказывает полную доступность варианта: индекс не разворачивает всю цепочку prerequisites/AND/XOR, внешние MD/vanilla/DLC definitions, dynamic triggers и реальные правила версии движка. Отсутствие локального mapping остаётся dependency/runtime candidate, а не ERROR.
- Unit suite прошёл **61/61**; весь workflow [45616388016](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45616388016) завершился: **14/14 jobs success**, включая полный аудит и все 12 country jobs. Auditor сохранил content findings отдельно; report-only exit code не является падением CI. Страновые файлы не менялись.


### Custom-cost trigger-only refinement and candidate triage — 25.11.2026

Коммит [1121135](https://github.com/minusleto/Make-TDF-Great-Again/commit/11211354302481adbb497f2cc9d20cb95986fe96), workflow [45617380290](https://github.com/minusleto/Make-TDF-Great-Again/actions/runs/45617380290): **61/61 tests OK, 14/14 CI jobs success**. Debit analysis now runs only when `custom_cost_text` explicitly presents a player-facing custom price. A `custom_cost_trigger` without a text remains a trigger/text pairing candidate, not a missing-debit finding.

Final decision counts: **5** custom-cost pair issues; **1** cost/custom-cost display conflict; **18** displayed custom-cost candidates without a detected debit; **1** threshold-only requirement; **6** ordinary constant-false condition candidates; **19** automatic mission/ticker gate candidates. The full audit still uses report-only exit code 1 for content findings; this is not a workflow/test failure.

#### 18 strong static missing-debit candidates

The following groups show a treasury threshold and a visible `cost_*` string, while the local decision effect and any directly called local event checked do not show the corresponding treasury debit. They are **strong static candidates**, not runtime-confirmed bugs: a target mod package or version-specific effect could still provide an external payment path. Details/call sites are listed in [Issue #18 — country candidates](https://github.com/minusleto/Make-TDF-Great-Again/issues/18).

- **BLR (2):** `blr_hold_eu_summit` and `blr_hold_nato_summit` — [Belarus.txt:2301](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Belarus.txt#L2301), [Belarus.txt:2342](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Belarus.txt#L2342). Both show `cost_2_0`; their local effects change influence and variables, with no treasury debit in the decision block.
- **SOV (5):** `SOV_begin_funding`, `SOV_dissassemble_the_shuttle`, `SOV_announce_full_restoration`, `SOV_againg_stabfund`, `SOV_wagner_rusich` — [Russia.txt:653](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Russia.txt#L653), [Russia.txt:770](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Russia.txt#L770), [Russia.txt:910](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Russia.txt#L910), [Russia.txt:959](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Russia.txt#L959), [Russia.txt:1779](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/Russia.txt#L1779). For `SOV_begin_funding`, the called local `russia.200`/`.300` branches were checked; for `SOV_announce_full_restoration`, `russia.301`/`.302` were checked. No treasury debit was found in those event options. The other three decisions directly set flags/add ideas or display tooltips without a treasury debit in their local effect.
- **HUN (11):** `HUN_coup_in_slovakia`, `HUN_coup_in_czech`, `HUN_coup_in_poland`, `HUN_coup_in_austria`, `HUN_coup_in_serbia`, `HUN_coup_in_bosnia`, `HUN_coup_in_greece`, `HUN_coup_in_bulgaria`, `HUN_coup_in_romania`, `HUN_coup_in_croatia`, `HUN_coup_in_albania` — [hungary.txt:915](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/hungary.txt#L915) through [hungary.txt:1315](https://github.com/minusleto/Make-TDF-Great-Again/blob/main/mdredux/common/decisions/hungary.txt#L1315). Each uses a treasury threshold `> 4.9` and `cost_5_0`; local effects change foreign influence/party popularity and grant a timed idea, with no treasury debit found in the decision file.

No country/gameplay files were changed. Each candidate needs confirmation against the exact installed target load order and, if absent there too, a separate content fix authorized by the user.
