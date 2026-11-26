# Agent instructions — Aral Sea mechanic branch

This branch intentionally contains only the Kazakhstan Aral Sea mechanic and its directly related maintenance material. It is a focused snapshot, not a complete TDF/MDC checkout.

## Scope
- Keep gameplay content under `mdredux/**` limited to Aral-named files, plus the KAZ country-history file that contains the Aral startup integration call.
- Keep optional content only under `optional/aral_sea/**`.
- Keep documentation only under `docs/aral-sea/**`.
- Keep scripts and tests only under `skills/aral-sea-mechanic/**`.
- Do not add other countries' files, unrelated events, generic wiki pages, general TDF research, broad country skills or generic tools to this branch.
- Base-MD definitions are external. Track the Aral-specific verified dependencies in `docs/aral-sea/EXTERNAL_DEPENDENCIES.md`.

## Required mechanic invariants
- All 18 active decisions in the KAZ Aral category, including regional recovery, require `controls_state = 717` in `available`. Never use `owns_state = 717` as a decision-availability gate.
- Do not add ownership-based `cancel_trigger` or `cancel_effect`: a project already started continues its timer after loss of state 717.
- Keep `fire_only_once = yes` on the 17 one-shot decisions; `aral_sibaral` is the repeatable exception and keeps its `days_re_enable = 365` behaviour.
- The monthly tick and `update_aral_sea` recalculation require KAZ legal ownership of state 717 through their internal `owns_state = 717` guards.
- State dynamic modifiers remain attached to their states when ownership changes; state construction effects remain limited to states KAZ currently owns.
- Issue #12 is a historical design record and contains superseded ownership and cost instructions. When it conflicts with the active code, `docs/aral-sea/README.md`, or `docs/aral-sea/HOI4_SCRIPTING_REVIEW.md`, follow the current code and current branch documentation; do not restore obsolete issue text.
- Keep EN/RU localisation in sync, preserving UTF-8 BOM and CRLF in YML.
- Do not install the optional six-focus prototype over the live KAZ focus tree.

## Workflow
1. Read `docs/aral-sea/README.md`, `docs/aral-sea/EXTERNAL_DEPENDENCIES.md`, issue #12 and the specialist `skills/aral-sea-mechanic/SKILL.md`.
2. Inspect only the Aral files relevant to the task and trace each changed variable across code, GUI, localisation, tests and simulator.
3. Run the dedicated unit tests, localisation generator check, mechanic audit and simulator.
4. Review the exact file list and diff before committing. Keep one commit per coherent task.
5. Never describe a static audit or simulation as an in-game test.

## Git discipline
- Work on `aral-sea-mechanic`.
- Fetch and inspect the current branch head before creating commits.
- Never move the ref backwards or overwrite a concurrent commit; update refs with an expected-SHA lease.
- Because this branch intentionally omits unrelated repository files, do not merge its entire tree into the full TDF branch. Transfer only the Aral-specific paths.
