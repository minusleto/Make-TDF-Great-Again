# Aral Sea mechanic — focused working branch

This branch is deliberately scoped to the Kazakhstan Aral Sea mechanic. It is not a mirror of the full TDF/MDC repository.

## Install in the game

1. Download this branch as a ZIP or open its files on GitHub.
2. Take only the repository's **mdredux** folder.
3. Copy it into the folder containing your installed mdredux mod folder. Let Windows merge the folders.
4. Do not delete or replace your existing mdredux folder or its other files.

The active payload uses uniquely named Aral files, including common/on_actions/aral_sea_on_actions.txt. It does not include or replace Kazakhstan's country-history file, the KAZ focus tree, or any other country's files. No manual edits in Kazakhstan history or existing on_actions files are required. Start a new 2000 game as Kazakhstan for the first initialization check; HOI4's on_startup hook does not run when loading an existing save.

Included:
- Aral decisions, scripted effects and triggers, monthly hooks, events, dynamic modifiers and GUI;
- Aral EN/RU localisation and interface graphics;
- optional Aral focus-tree and province-photo prototypes;
- Aral-specific documentation, localisation generator, auditor, simulator and tests.

Excluded:
- Kazakhstan's full country history and active focus tree (the mechanic uses existing KAZ focus IDs);
- other countries' focus trees, ideas, events, localisation and history;
- generic TDF/MDC wiki pages, research notes, skills and tools unrelated to Aral;
- base-MD files that are external dependencies rather than Aral-owned content.

Start with [the mechanic documentation](docs/aral-sea/README.md) and [the Aral skill](skills/aral-sea-mechanic/SKILL.md).

Run the checks from the repository root:

```bash
python -m unittest discover -s skills/aral-sea-mechanic/tests -v
python -I skills/aral-sea-mechanic/scripts/generate_cost_localisation.py
python -I skills/aral-sea-mechanic/scripts/mech_audit.py mdredux --prefix aral
python -I skills/aral-sea-mechanic/scripts/aral_model_sim.py mdredux --runs 20
```

**Branching note:** this is a focused snapshot. Do not merge the entire branch tree into the full TDF repository, because excluded files appear as deletions in a whole-branch comparison. Port only the Aral paths through a file-scoped change or a dedicated patch.
