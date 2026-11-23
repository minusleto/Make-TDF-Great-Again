---
name: md-hoi4-country-content
description: 'Generic workflow, code patterns, localisation and balance guidance for Millennium Dawn / Hearts of Iron IV country-content projects outside Make-TDF-Great-Again. Use for other MD/HOI4 projects; for TDF/MDC work in that repository use tdf-country-content instead, not both.'
---

# MD / HOI4 country content skill

> This is the generic MD/HOI4 workflow for projects outside Make-TDF-Great-Again. Do not use it alongside `tdf-country-content` for the TDF repository; the TDF skill is the source of truth there.

This skill contains reusable patterns distilled from specific MD/HOI4 project work; it is not a game-engine specification. Treat numbers as recommendations and examples as patterns, not universal requirements. The target mod's files, wiki and verified in-game behaviour take precedence. Update only the relevant reference when a new project lesson is confirmed.

## 1. Start of work
1. Locate the files touched by the task and the project brief; list missing inputs once.
2. For large uploaded file sets, optionally build an index: `python scripts/mdindex.py build`, then use `get ID`, `loc REGEX`, `find REGEX`, `check` (set `MD_UPLOADS` / `MD_INDEX`). Rebuild only after uploads change. For a checked-out repository, use normal search tools instead of indexing it.
3. For multi-step branch work, keep a short backlog of bugs, decisions and unverified items; do not create project notes for a one-line fix.
4. Use reference countries for structure and measured values, not as automatic quality examples (see `references/balance.md`).

## 2. Work loop per focus
1. View code + loc + the ideas/events it touches (compact dump, not the whole file).
2. Check: log id = focus id, prerequisites exist, available is satisfiable, effects match tooltip and text, DLC guards, double bonuses, idea exists, scripted loc shows hidden ideas.
3. Research only real-world facts that will appear in the text; skip browsing for purely mechanical edits. Separate sourced facts from the player's intended alternate-history outcome.
4. Write description (references/loc-style.md), adjust numbers to medians (references/balance.md), fix code (references/code-patterns.md).
5. Verify mechanically (brace balance, tabs, unique loc keys, lengths) with a script before delivering.
6. Deliver only changed lines; put anything over ~30 lines into a file. End with what is unverified.

## 3. Hard-learned principles
- Texts follow reality: problem that really existed -> "we will" intent -> short consequence. Facts must be date-independent (sandbox: a focus can be taken at any date). No future-focus spoilers. No hardcoded capital / country adjectives.
- Gates in `available` are real gameplay conditions (partner has the tech, opinion, no war, completed prerequisite focus), not dates.
- Events only where there is a real choice or real flavour value. Proposal chains: focus sends proposal to partner, accept sends reply to FROM, decline uses generic reply; bot always accepts when the focus gate passed (decline has has_opinion factor 0). Never give the same bonus twice.
- One spirit = one profile; modifiers should match the focus name and not repeat in sibling positive spirits.
- Before writing or revising focus descriptions, inspect the exact `completion_reward` and any ideas/events it grants. Every described outcome must be supported by an actual effect; never invent runway extensions, hangars, dispersal facilities, training systems, or other rewards that the focus does not provide. Conversely, make the prose explain the actual reward in natural flavour text, without mechanically listing every effect.
- For scripted modifier tooltips, copy the exact modifier localization tokens used by established country content (e.g. Poland/Portugal use `$MODIFIER_AIR_ATTACK_FACTOR$`, `$MODIFIER_AIR_DEFENCE_FACTOR$`, `$MODIFIER_AIR_MAX_SPEED_FACTOR$`, `$MODIFIER_ARMY_BONUS_AIR_SUPERIORITY_FACTOR$`); raw effect identifiers such as `$air_attack_factor$` may display as blank labels. Add `newline = yes` to scripted-localisation text blocks when adjacent entries otherwise run together, and verify the rendered keys/line breaks against existing country examples.
- Audit focus reward logs literally: a scripted effect call without its required assignment (e.g. `increase_conscription_effect` instead of `increase_conscription_effect = yes`) can cause the parser to misread the following block. Do not assume helper effects exist: confirm them or replace them with a supported built-in effect in the correct scope. Put experience/research rewards first, idea swaps/additions near the end, and treasury deductions after them.
- Keep answers short (token budget). Use files for bulk. Never re-dump what was summarised.
- Command output: keep text output UTF-8; never print binary data to stdout/stderr; avoid byte-based truncation (`head -c`, `tail -c`, `cut -c`) on text; for arbitrary slices use Python strings and decode subprocess output with its actual source encoding.

## 4. References (read when needed)
- references/loc-style.md - description/title/event wording, banned phrases, yml rules.
- references/code-patterns.md - focus/event/idea code patterns and guards.
- references/balance.md - modifier medians from four countries and focus/event effect sizes.
- references/pitfalls.md - bug patterns found, audit checklist, unverified items, process lessons.

## 5. Adapting this skill
If the user states a preference (e.g. "events only for real choices", "no years in descriptions"), add it to pitfalls.md under "User decisions" and follow it above this file. Keep SKILL.md short; move detail to references.


