---
name: aral-sea-mechanic
description: 'Use when developing, reviewing, simulating, documenting or debugging the Kazakhstan Aral Sea mechanic in this repository: decisions, treasury and debt costs, generators, localisation, events, monthly updates, dynamic modifiers, scripted GUI and the mechanic audit.'
---

# Aral Sea mechanic — development and QA

## When to use this skill

Use this specialist skill for work on the Kazakhstan Aral Sea mechanic and its toolchain. In this TDF repository it supplements `tdf-country-content/SKILL.md`; do not load the generic `md-hoi4-country-content` skill alongside the TDF skill.

Before changing anything, read:

1. `docs/aral-sea/README.md` — current design, variables, projects, file map and simulation commands.
2. GitHub issue #12 — design rationale, decisions already made and outstanding in-game checks.
3. The exact code being changed. The live code is the source of truth when it differs from an older note or issue description.
4. `skills/tdf-country-content/SKILL.md` and the relevant TDF references (especially the KAZ maintenance notes). Use repository code and verified engine behaviour as the final authority.

Do not load every wiki page or every skill reference by default. Search for a specific unresolved mechanic or engine behaviour.

## Scope and branch discipline

- The mechanic is developed on `aral-sea-mechanic`. Keep its changes on that branch unless the user explicitly asks to port or merge them.
- Before editing, confirm the current branch, HEAD and worktree status. Do not assume a previous Claude session left the repository on the right branch.
- Never move the branch ref backwards or overwrite concurrent commits. Create the commit from the freshly fetched HEAD and update the ref with an expected-SHA check.
- Keep one commit per coherent task. A documentation/skill-only change must not include unrelated gameplay edits.
- The repository is a partial MDC/HOI4 snapshot. The base mod and some engine-facing definitions are external. Mark such dependencies as unverified; do not report them as broken solely because they are absent from this checkout.

## Mechanic model and invariants

The design is a long-running restoration system, not a one-off national bonus. Preserve its distinctions:

- `aral_sea_restoration` tracks the water level relative to the 40 m baseline; confirm the current scale and bounds in code/README before changing calculations.
- The crest is the maximum level allowed by the currently completed dam project. Extra water must spill above the crest rather than silently raising the target.
- `aral_pending` is earned water that arrives gradually. Project completion should not instantly dump the whole amount into the sea.
- `aral_relief` mitigates environmental and social fallout; it does not itself add water.
- The monthly tick, dry-year events, dike failure and project effects must use the same variables and thresholds as the GUI and simulator.
- Aral decision groups use existing KAZ focus milestones. Keep decisions visible and put the unlock gate in `available` with a `custom_trigger_tooltip`; do not hide locked projects with a `visible` gate.
- Coast-dependent Aral decisions, monthly ticks and `update_aral_sea` recalculations require Kazakhstan to **own** state 717 (Kyzylorda), using `owns_state = 717`; control without ownership is not sufficient. State dynamic modifiers are deliberately persistent: once applied, they remain on their states when ownership changes. Their last values stay in place while KAZ does not own the coast and are recalculated when KAZ owns it again. State construction effects must still check that Kazakhstan currently owns each target state.
- The Siberian-water chain is deliberately uncertain and costly. Do not turn it into a guaranteed free water source or allow it to raise the dam crest.
- The optional focus and province-photo packages are not loaded by default. Do not silently move optional content into active folders.
- The monthly on_action file is an integration snippet. If the real mod already has an on_monthly block, merge the Aral call into it rather than replacing the existing on_actions file.

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
| Documentation and tools | `docs/aral-sea/README.md`, `skills/aral-sea-mechanic/scripts/generate_cost_localisation.py`, `skills/md-hoi4-country-content/scripts/mech_audit.py`, `skills/md-hoi4-country-content/scripts/aral_model_sim.py` |

Use the current tree to confirm exact paths before editing; do not copy this table blindly if the layout changes.

## Decision costs: keep the layers separate

A decision can have several different costs. Review them independently:

| Element | Role | What to verify |
|---|---|---|
| `cost` | Political Power cost charged by the decision system | The number is intentional and visible to the player where the UI requires it |
| `custom_cost_text` | Localisation key used to display a custom cost | The displayed text accurately explains the actual treasury/debt terms and does not hide a PP cost |
| `custom_cost_trigger` | Gate that decides whether the custom cost is affordable | Its threshold and comparison operator agree with the amount actually charged |
| `treasury_change` + `modify_treasury_effect` | Actual treasury transaction | It is executed exactly once, in the intended completion path |
| `debt_change` + `modify_debt_effect` | Actual debt transaction | Sign, units, timing and displayed amount match the real effect |

Important distinctions:

- `custom_cost_text` is presentation; it does not itself deduct money.
- `custom_cost_trigger` is an affordability condition; it does not itself charge money.
- `cost` is not the same thing as a treasury amount. Do not remove or add one merely because the other exists.
- Do not assume that `cost` and `custom_cost_text` are incompatible. Inspect a working decision and the actual engine/MDC contract before changing that combination.
- Inspect the full decision block: `visible`, `available`, `custom_cost_trigger`, `custom_cost_text`, `cost`, `complete_effect`, `remove_effect`, timeout/cancel behaviour and AI weight. A cost deducted at start must not be charged again at completion.
- Compare the affordability threshold with the amount paid, including edge cases where treasury equals the price. Be deliberate about strict versus inclusive comparisons.
- For debt-financed projects, distinguish the amount paid from treasury and the amount added to debt. Never infer the debt sign or unit from the label; confirm it against a known-working `modify_debt_effect` pattern.
- A decision that can time out or be cancelled needs an explicit review of whether the money/PP is kept, refunded or never charged.

### Localisation contract for custom costs

The HOI4 custom-cost localisation contract is:
- The base key from `custom_cost_text` is used while `custom_cost_trigger` is fulfilled.
- The `_blocked` variant is used when that trigger is not fulfilled; it is required in both EN and RU.
- The `_tooltip` variant is optional and replaces the lower hover-tooltip text. Aral decisions provide it so the hover text can explain treasury, debt and PP components.

Do not mark the optional `_tooltip` key as an engine error when it is absent elsewhere. For this Aral mechanic, validate every required `_blocked` key and keep the generated optional tooltip in both languages.

For every custom cost:

- Show every real component of the price: treasury, PP and debt-financed portion where relevant.
- Ensure the label and tooltip agree with the actual cost effects and affordability gate.
- Keep English and Russian key sets aligned.
- Check that the display for an unaffordable decision remains meaningful and does not expose a misleading price.
- If a key belongs to the absent base mod rather than this repository, report it as an external dependency until verified. Do not create a false ERROR for an external key; keys generated by this mechanic must exist locally in both languages.

A repeated error pattern across many decisions and both languages is usually a generator/contract problem, not dozens of unrelated manual mistakes. Diagnose the common source before editing each decision.

## Generator workflow

Some generation scripts may live in a temporary work directory (for example, `/tmp`) rather than in Git. Treat such a script as an external working artifact, not as an authoritative repository file. Before using it, confirm that it exists, inspect the current version and identify exactly which files it writes.

1. Find the source data for the decisions and the functions that emit code/localisation. Trace one simple treasury-only decision, one PP-plus-treasury decision and one debt-financed decision from data definition through generated code and both localisation outputs.
2. Make the source data the single source of truth for amounts, days, gates, dependencies, flags and displayed prices. Avoid separately hardcoding a second copy of the same amounts in audit logic.
3. Make generation deterministic and idempotent: running it twice without changing input should produce no diff.
4. Generate only intended Aral files. Do not let a generator rewrite unrelated country files or normalise entire localisation files.
5. Preserve repository formatting: HOI4 script files use tabs and CRLF; localisation YML uses UTF-8 BOM and CRLF. Verify raw bytes after generation, not just the editor display.
6. Before replacing existing output, inspect the diff and confirm the generator has not removed hand-maintained text or keys.
7. If the generator cannot provide a safe dry run, write to temporary output first and compare it with the tracked files before copying anything back.

When changing a generator, do not patch its output files manually unless the generator is intentionally no longer the source of truth. Otherwise the next generation will erase the manual fix.

## Audit design and tests

The mechanic audit is a static checker, not a substitute for testing in HOI4. Its rules must reflect a verified project/engine contract.

- Keep audit checks narrow and explainable. One check should validate one invariant and report the exact decision/key/file involved.
- Do not make the audit stricter than the source of truth. In particular, do not classify a missing base-mod localisation key as a local defect without proving that the key is expected to be supplied by this repository.
- For custom-cost checks, validate the whole chain: displayed key(s), PP cost, treasury gate, treasury deduction, debt addition and tooltip values. Only enforce localisation variants that have been confirmed as part of the engine contract.
- Avoid string searches that treat comments, unrelated decisions or similar names as real references. Use the existing parser helpers where possible; improve parsing only when a reproducible false positive/negative justifies it.
- A systemic failure repeated for N decisions in two languages should be summarised as one likely generator defect with N affected decisions, not presented as 2N independent root causes.
- Add small regression fixtures for each cost shape: no custom cost, treasury only, PP only, PP plus treasury, treasury plus debt, repeated/recurring decision and any confirmed blocked/hover localisation behaviour.
- Test audit exit codes: 0 for clean, non-zero for detected errors and a distinct code for invalid input/read failures if the script implements one.
- Run the audit against a clean baseline before attributing old warnings to a new patch. Compare before/after results; do not demand a perfectly clean repository if pre-existing warnings are unrelated.

Useful baseline commands from the repository root:

    python3 -I skills/md-hoi4-country-content/scripts/mech_audit.py mdredux --prefix aral
    python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux
    python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux --income 0.03 --route dam2 --dike yes --once --seed 5

The simulator derives its report from the current code, but it is still a model. It does not prove that HOI4 executes the script as intended.

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

    python3 -I skills/md-hoi4-country-content/scripts/mech_audit.py mdredux --prefix aral > /tmp/aral-audit.log 2>&1
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
