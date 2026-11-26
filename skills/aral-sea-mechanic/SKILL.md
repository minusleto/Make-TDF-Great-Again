---
name: aral-sea-mechanic
description: 'Use when developing, reviewing, simulating, documenting or debugging the Kazakhstan Aral Sea mechanic in this repository: decisions, treasury and debt costs, generators, localisation, events, monthly updates, dynamic modifiers, scripted GUI and the mechanic audit.'
---

# Aral Sea mechanic — development and QA

## When to use this skill

Use this specialist skill for work on the Kazakhstan Aral Sea mechanic and its toolchain. The `aral-sea-mechanic` branch is intentionally kept as an Aral-focused snapshot: do not add unrelated country content, events, localisation, wiki pages or generic TDF research files.

Before changing anything, read:

1. `docs/aral-sea/README.md` — current design, variables, projects, file map and simulation commands.
2. GitHub issue #12 — design rationale, decisions already made and outstanding in-game checks.
3. The exact code being changed. The live code is the source of truth when it differs from an older note or issue description.
4. `docs/aral-sea/EXTERNAL_DEPENDENCIES.md` for unresolved target-TDF dependencies. Check documented modifiers, effects and triggers in the MDC wiki first. If the wiki does not define the required identifier or behaviour, request the exact target TDF source file from the user. Never use another mod as the authority for TDF.

Do not load every wiki page or every skill reference by default. Search for a specific unresolved mechanic or engine behaviour.

## Scope and branch discipline

- The mechanic is developed on `aral-sea-mechanic`. Keep its changes on that branch unless the user explicitly asks to port or merge them.
- Before editing, confirm the current branch, HEAD and worktree status. Do not assume a previous Claude session left the repository on the right branch.
- Never move the branch ref backwards or overwrite concurrent commits. Create the commit from the freshly fetched HEAD and update the ref with an expected-SHA check.
- Keep one commit per coherent task. A documentation/skill-only change must not include unrelated gameplay edits.
- This branch is a focused snapshot, not the complete target TDF installation. An identifier missing from this branch is unknown, not automatically invalid or supplied by another mod. Check the MDC wiki; if the definition or behaviour is not documented, ask the user for the relevant target TDF file.

## Mechanic model and invariants

The design is a long-running restoration system, not a one-off national bonus. Preserve its distinctions:

- `aral_sea_restoration` tracks the water level relative to the 40 m baseline; confirm the current scale and bounds in code/README before changing calculations.
- The crest is the maximum level allowed by the currently completed dam project. Extra water must spill above the crest rather than silently raising the target.
- `aral_pending` is earned water that arrives gradually. Project completion should not instantly dump the whole amount into the sea.
- `aral_relief` mitigates environmental and social fallout; it does not itself add water.
- Ecological penalties must remain in `aral_state_modifier` on the six explicitly targeted states; never recreate a country-wide environmental modifier just to access country-scope-only stats. National consequences are event-driven political/administrative spirits: one annual warning above the deficit threshold, a 730-day neglect spirit after postponement, a permanent crisis spirit after repeated inaction, and the separate `aral_regional_response` decision to remove that crisis.
- The monthly tick, dry-year events, dike failure and project effects must use the same variables and thresholds as the GUI and simulator.
- Aral decision groups use existing KAZ focus milestones. Keep decisions visible and put the unlock gate in `available` with a `custom_trigger_tooltip`; do not hide locked projects with a `visible` gate.
- All 17 Aral project decisions require Kazakhstan to control state 717 (Kyzylorda) in `available`, using plain `controls_state = 717`; do not wrap this coast check in `custom_trigger_tooltip`. Do not add `cancel_trigger` / `cancel_effect` for this ownership condition: if KAZ loses 717 after starting a project, its active timer continues and its normal `remove_effect` still runs. Keep `fire_only_once = yes` on the 16 one-shot decisions; `aral_sibaral` retains its existing `days_re_enable = 365` behaviour. The `on_startup` hook has no country scope, so enter `KAZ` and initialize directly: KAZ owns 717 at new-game start, so no startup ownership test is needed. Use `on_monthly_KAZ` for the monthly pulse, not generic `on_monthly` plus `original_tag`; it already runs only for KAZ. Keep the legal-ownership check inside `aral_monthly_tick` and `update_aral_sea`, where it protects later updates if Kazakhstan loses 717. State dynamic modifiers remain on their states when ownership changes, retaining their last calculated values until KAZ owns the coast again and recalculation resumes. State construction effects must still check that Kazakhstan currently owns each target state.
- The Siberian-water chain is deliberately uncertain and costly. Do not turn it into a guaranteed free water source or allow it to raise the dam crest.
- The optional focus and province-photo packages are not loaded by default. Do not silently move optional content into active folders.
- The Aral on_action file is a standalone, uniquely named file under common/on_actions/. It contains both fresh-game startup initialization and the ownership-gated monthly tick. Keep it alongside the target TDF on_actions files; do not replace those files or ask the user to merge a call manually.
- The active payload must remain directly copyable as one mdredux/ folder. Do not add the full KAZ country-history file or other country files just to initialize this mechanic; on_startup handles initialization after country selection. Remember that on_startup is not run when loading an existing save.

Aral localisation follows the project house style: write key: "text" and never add the optional :0 version suffix. Keep the EN/RU key sets aligned; generic `cost_X_Y` keys are supplied by the parent TDF localisation.
Reuse sprites only when their definitions and textures are confirmed in TDF source files or target files supplied by the user. If a referenced sprite is not present in available sources, record it as unknown and request the target interface/GFX file before relying on it or replacing it.

When changing a variable, threshold or formula, search every writer and reader: scripted effects, decisions, events, dynamic modifiers, GUI, scripted localisation, simulator and both language files. A correct formula in one file is not enough.

## File map

| Area | Main files |
|---|---|
| Decisions and category | `mdredux/common/decisions/aral_sea_decisions.txt`, `.../categories/aral_sea_categories.txt` |
| Monthly effects and triggers | `mdredux/common/scripted_effects/aral_sea_effects.txt`, `mdredux/common/scripted_triggers/aral_sea_triggers.txt`, `mdredux/common/on_actions/aral_sea_on_actions.txt` |
| Events | `mdredux/events/aral_sea_events.txt` |
| Dynamic modifiers | `mdredux/common/dynamic_modifiers/aral_sea_modifiers.txt` |
| GUI | `mdredux/common/scripted_guis/aral_sea_category_gui.txt`, `mdredux/interface/aral_sea.gui`, `mdredux/interface/aral_sea.gfx`, `mdredux/gfx/interface/aral_sea/` |
| Localisation | `mdredux/localisation/english/aral_sea_l_english.yml`, `mdredux/localisation/russian/aral_sea_l_russian.yml` |
| Optional content | `optional/aral_sea/` |
| Documentation and tools | `docs/aral-sea/README.md`, `skills/aral-sea-mechanic/scripts/check_generic_costs.py`, `skills/aral-sea-mechanic/scripts/mech_audit.py`, `skills/aral-sea-mechanic/scripts/aral_model_sim.py` |

Use the current tree to confirm exact paths before editing; do not copy this table blindly if the layout changes.

## Aral treasury costs: use the TDF debt system

Keep the cost layers explicit, but do not manufacture a second debt transaction:

| Element | Role | Aral contract |
|---|---|---|
| `cost` | Native Political Power cost | Keep the existing `cost = N`; PP is separate from treasury |
| `custom_cost_trigger` | Optional eligibility check for a custom resource | Omit it for Aral treasury prices; there is no treasury-balance gate |
| `custom_cost_text` | Player-facing treasury price | Use the shared TDF `cost_X_Y` key matching the full cash price |
| `treasury_change` + `modify_treasury_effect` | Actual cash transaction | Charge the complete project/event price exactly once |
| `debt_change` + `modify_debt_effect` | Explicit debt transaction | Do not use for Aral cash expenses: the TDF treasury system automatically finances a negative balance |

Important rules:

- A project with a total price of 4.5 bn charges `treasury_change = -4.5`; do not charge 1.5 bn from the treasury and then separately add 3 bn to debt.
- Never add a `treasury > N` condition to an Aral decision or cash-cost event option. A negative treasury balance is financed by the TDF debt system; it must not prevent the project from starting.
- Keep PP requirements. A decision's native `cost = N` remains a real PP cost, and event options may retain `has_political_power = N`.
- Do not change project prices by splitting them into a treasury portion and an explicit debt portion. The displayed `cost_X_Y` and the single treasury debit must match the full cash price.
- The existing shared `cost_X_Y` labels live in the parent TDF `MD_decisions_l_english.yml`; use `custom_cost_text` directly without an empty `custom_cost_trigger`. Do not recreate project-specific `*_cost_label`, `_blocked` or `_tooltip` variants in Aral localisations.
- Yearly Siberian fees and event expenses use the same treasury-only mechanism. Keep non-cash conditions such as PP requirements and the Siberian contract's price cap.
- Run `skills/aral-sea-mechanic/scripts/check_generic_costs.py mdredux`, the static audit, unit tests and simulator after changing a cost.

## Cost validation and tests

The generic-cost checker verifies that each decision's `cost_X_Y` key matches the full negative `treasury_change`, that the debit is applied once, and that no treasury-balance gate or direct debt transaction remains. Regression tests also verify that the simulator can take the treasury below zero and continue scheduling projects.

The static audit is not a substitute for testing in HOI4. Keep event PP conditions, decision PP costs, timer behaviour and actual GUI price display on the in-game checklist. Never claim that a cost label or event option rendered correctly until it has been checked in the target game.

## Decision source formatting

- In a multiline `visible = {}` block, put the first condition on the immediately following line. Do not leave an empty line after the opening brace.
- The Aral unit tests scan `mdredux/common/decisions/**/*.txt` for this regression, so CI catches it before it can be reintroduced.
- Treat decision files as hand-maintained source. The Aral audit, simulator and cost checker inspect them; they are not formatters or source generators.

## Efficient Bash and Python work

Four short, purposeful commands are not inherently wasteful. The goal is to avoid broad, repetitive searches and giant opaque commands.

- Prefer scoped `rg -n` searches over recursive Python scans of every Markdown file. Search only relevant file types and folders; add a small context window around hits.
- Use `sed -n '120,170p' file` to inspect a known section instead of printing an entire long file.
- Do not combine discovery, source mutation, generation and audit into one huge heredoc. Separate inspect → edit → generate → test so a failure is easy to locate.
- Avoid editing by calculated line-number slicing such as `L[:a] + ... + L[b:]`. Prefer a unique exact block or a small parser-aware edit. Assert the expected match count is exactly one before writing.
- Check every scripted replacement. If a required pattern is absent or appears more than once, abort instead of silently writing a partial patch.
- Do not use an unguarded `str.replace` for structural code edits. Keep a backup or rely on Git, then inspect the resulting diff.
- Avoid `grep | cut | head` around a test command because the pipeline may hide the tested command's exit code or truncate the summary.
- For pipelines, enable `set -o pipefail`. For important test commands, save output to a log, capture the command's exit code, then filter the log separately.
- Limit output to the relevant lines. Do not ask the model to reread megabytes of generated files or repeated copies of the same search result.

Example preserving the audit exit code:

    python3 -I skills/aral-sea-mechanic/scripts/mech_audit.py mdredux --prefix aral > /tmp/aral-audit.log 2>&1
    rc=$?
    grep -E '^== |SUMMARY|^  \[' /tmp/aral-audit.log | sed -n '1,50p'
    echo "Audit exit code: $rc"
    exit "$rc"

If the shell uses strict mode, use `set -o pipefail` and capture the test process status explicitly. Do not rely on the status of the last formatter/filter in a pipeline.

## Resuming a Claude session

When a session is interrupted or the user presses Continue:

1. Re-check branch, HEAD and worktree status.
2. Read the latest task note/checkpoint and the exact files named there.
3. Resume from the recorded next action. Do not replay completed searches, file dumps or audits just because the assistant context restarted.
4. If HEAD changed, inspect the new commits and reconcile the work before applying a patch.
5. Keep a compact handoff note with: goal, branch + HEAD, changed files, commands/tests already completed and their exit codes, current blocker, next concrete action.
6. Store useful findings as a concise note in the active issue or project documentation when they must survive a session reset; do not paste huge raw command outputs into the checkpoint.

## Verification and reporting

Before committing:

- Review `git status --short`, `git diff --stat` and the complete `git diff`.
- Run `git diff --check`.
- Re-run the relevant audit and simulator after the final edit; record exit codes and distinguish new findings from baseline findings.
- Confirm the intended files only changed and that EN/RU localisation remains aligned.
- For on_actions, debt, dynamic modifiers and GUI, keep an explicit in-game checklist. A static audit or successful simulator run is not an in-game test.
- Never claim that the game was launched or that a UI element rendered unless someone actually performed that test.

Report the exact commit, changed files, checks run and remaining in-game checks. Be explicit about any external base-mod dependency that could not be verified.
