---
name: md-hoi4-country-content
description: Workflow, style rules and balance numbers for writing and auditing country content (focus trees, national spirits/ideas, events, localisation) for Millennium Dawn / MDC and similar Hearts of Iron IV mods. Use this whenever the user mentions HOI4 or Hearts of Iron modding, Millennium Dawn, MD, MDC, focus trees, national spirits or ideas, event chains, .yml localisation, scripted localisation, tech bonuses, MIO, or wants a country branch reworked, balanced or checked for bugs - even if they only paste a focus block or a loc line.
---

# MD / HOI4 country content skill

> **Использование в репозитории Make-TDF-Great-Again.** Здесь файлы лежат на диске (`mdredux/...`), поэтому индексатор `scripts/mdindex.py` (он рассчитан на загрузки в `/mnt/user-data/uploads`) не нужен: искать через Grep/Glob, а для массовой проверки запускать `python3 -I skills/tdf-country-content/scripts/tdf_audit.py .`. Для правил философии, эталонов Португалии и России, нацдухов и устройства страны сначала читать `skills/tdf-country-content/SKILL.md`; этот скил - рабочий цикл и числа. При противоречии приоритет у `tdf-country-content`. Раздел "Kazakhstan focus-tree lessons" внизу относится только к Казахстану; правило про blob SHA относится к правке через GitHub API, при работе с файлами на диске не применяется.

IMPORTANT: this skill is a distilled snapshot of one long working session (Kazakhstan branch rework). It is NOT perfect and NOT a spec. Every number is a recommendation, every rule can be overridden by the user or by the target mod's own conventions. When the user's files, the mod wiki or in-game behaviour contradict this skill, trust them and tell the user. Update the skill after each project.

## 1. Start of work
1. Ask for (or locate) the country's focus tree, events, ideas, loc .yml, scripted loc, history file, and the project brief. List what is missing once; do not keep asking.
2. Build an index so you never re-read big files: `python scripts/mdindex.py build` then `get ID`, `loc REGEX`, `find REGEX`, `check`. (Set MD_UPLOADS / MD_INDEX env vars.) If files are re-uploaded, rebuild; duplicates with different upload prefixes must be resolved by newest mtime.
3. Keep a backlog file (bugs found, decisions, unverified items) and a style card. Memory may be off: files are the memory.
4. Reference countries (other trees/ideas/events/loc) are for FORM and numbers, not quality. Measure them (see references/balance.md) and check their loc for filler before imitating.

## 2. Work loop per focus
1. View code + loc + the ideas/events it touches (compact dump, not the whole file).
2. Check: log id = focus id, prerequisites exist, available is satisfiable, effects match tooltip and text, DLC guards, double bonuses, idea exists, scripted loc shows hidden ideas.
3. Research real-world basis (ONE search per focus, only for facts that enter the text). Say what is sourced and what is the player's intent.
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

## 4. References (read when needed)
- references/loc-style.md - description/title/event wording, banned phrases, yml rules.
- references/code-patterns.md - focus/event/idea code patterns and guards.
- references/balance.md - modifier medians from four countries and focus/event effect sizes.
- references/pitfalls.md - bug patterns found, audit checklist, unverified items, process lessons.

## 5. Adapting this skill
If the user states a preference (e.g. "events only for real choices", "no years in descriptions"), add it to pitfalls.md under "User decisions" and follow it above this file. Keep SKILL.md short; move detail to references.


## Kazakhstan focus-tree lessons (project-specific)
- In `mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt`, put a short English comment immediately before every focus block: `#English Focus Name`. Use the actual English focus title from localisation when available.
- The comment is the separator between focus blocks. Do not leave extra blank lines between a focus's closing brace and the next comment; keep the blocks compact. Do not reformat unrelated blocks while editing a branch.
- Distinguish source-code order, in-game layout, and gameplay prerequisites. Moving focus blocks in the file must not silently change `prerequisite` or `relative_position_id`.
- Keep each branch root attached to its intended existing parent. In the Kazakhstan air branch, `KAZ_decommission_old_planes` should use `relative_position_id = KAZ_our_military_forces` and `prerequisite = { focus = KAZ_our_military_forces }` so it does not float independently. Descendants should remain relative to the air-branch root unless the user explicitly requests a layout redesign.
- Before renaming a focus ID, search and update all references across the repository: focus tree, localisation keys, prerequisites, `available`/`bypass`, events, ideas, and scripted localisation. Never update only the definition and localisation.
- Preserve localisation format exactly. For `l_english` files, never alter or remove the `l_english:` header, BOM, or CRLF line endings. Prefer narrow key-level replacements; do not split and rejoin the entire file in a way that strips encoding markers or changes line endings.
- Before writing, fetch the current file and use its current blob SHA. Make exact edits; if the expected snippet is not found, stop rather than guessing. After writing, fetch again and verify block order, comment labels, unique IDs, prerequisites, relative positions, localisation references, header, BOM, and line endings.
- When removing/replacing a focus, trace its whole reward chain: events it starts, subsequent events, national spirits/ideas, localisation, and other references. Remove only content confirmed to be orphaned.
- Be explicit about validation: a repository text check is not an in-game test. Never claim the mod was launched or syntax-tested unless that actually happened.
- For country focus localization, keep military focus keys grouped in the same order as the in-game branches: all Army entries in focus order, then Air Force entries in focus order, then Navy entries in focus order. Keep the associated national-idea definitions in focus progression order too; place `KAZ_trained_officer_corps` after `KAZ_modern_air_forces`. When a task requires one commit across files, stage all changed blobs into one Git tree and create a single commit.
