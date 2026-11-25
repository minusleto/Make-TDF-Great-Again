# Aral Sea mechanic — focused working branch

This branch is deliberately scoped to the Kazakhstan Aral Sea mechanic. It is not a mirror of the full TDF/MDC repository.

Included:
- Aral decisions, scripted effects and triggers, monthly hooks, events, dynamic modifiers and GUI;
- Aral EN/RU localisation and interface graphics;
- the KAZ history integration file containing the startup call;
- optional Aral focus-tree and province-photo prototypes;
- Aral-specific documentation, localisation generator, auditor, simulator and tests.

Excluded:
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
