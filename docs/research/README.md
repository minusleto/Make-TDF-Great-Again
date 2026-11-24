# Research notes

Consolidated reviews and fact-checking notes for TDF / MDC.

## Documents
- [TDF inventory (2026-11-24)](2026-11-24-tdf-inventory.md) — reproducible file and block counts from main, with scope, counting method and limitations.
- [TDF trees audit vs skills (2026-10-30)](2026-10-tdf-trees-audit.md) — historical audit of the 10-tree sample available on 2026-10-30; its counts and findings are not the current repository baseline.
- [Kazakhstan navy branch review (2026-10-31)](2026-10-kazakhstan-navy-design-review.md) — navy branch run through design-guide: Russia event routing and gate bugs fixed, descriptions rewritten, open design decisions.
- [Content review principles](2026-10-content-review-principles.md) — reusable checklist, with summary takeaways from Portugal, Poland and Russia.
- [Kazakhstan military tree audit](2026-10-kazakhstan-tree-audit.md) — focus-level issues and technical QA priorities from the focus tree.
- [Kazakhstan aviation fact-check](2026-10-kazakhstan-aviation-fact-check.md) — China / US / Iran procurement status and recommendations for the 2000–2030 sandbox.
- [Standard vs MD skill and country trees](2026-10-standard-vs-country-trees.md) — comparison with the Claude/MD skill and static review of Portugal, Russia, Syria, Armenia, Israel, Poland and Kazakhstan.

These documents are research and recommendations, not game-script patches. Findings marked as localization candidates require checking shared focuses and text overrides before edits.

- [External dependency registry](external-dependencies.md) — machine-readable IDs, source/status evidence and dated official Millennium Dawn baseline; auditor output: `_external_dependencies`.

## Skills
- [`skills/tdf-country-content`](../../skills/tdf-country-content/SKILL.md) — how to write focuses, national spirits, events and localisation for TDF, plus `scripts/tdf_audit.py` and `scripts/tdf_inventory.py`.
