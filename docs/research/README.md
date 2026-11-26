# Research notes

Consolidated reviews and fact-checking notes for TDF / MDC.

## Documents
- [TDF Stage 9 static integration review (2026-11-24)](2026-11-24-tdf-stage9-static-integration.md) — initial selective cross-file review of ENG, ISR and countries without local event/decision files.
- [TDF Stage 9 executed validation (2026-11-24, updated 2026-11-25)](2026-11-24-tdf-stage9-validation.md) — historical 43/47-test runs plus 2026-11-25 triage: 57 unit tests and 14/14 CI jobs passed; exact external event/localisation fallbacks and conditional/hidden event false positives were refined. Content ERROR/WARN and runtime validation remain open.
- [TDF inventory (2026-11-24)](2026-11-24-tdf-inventory.md) — reproducible file and block counts from main, with scope, counting method and limitations.
- [KAZ branch-connectivity triage (2026-11-25)](2026-11-25-kazakhstan-connectivity-review.md) — KAZ false-positive review: idea lifecycle event roots, remaining unresolved triggered-event candidates, external references and tooltip linkage.
- [TDF trees audit vs skills (2026-10-30)](2026-10-tdf-trees-audit.md) — historical audit of the 10-tree sample available on 2026-10-30; its counts and findings are not the current repository baseline.
- [Kazakhstan navy branch review (2026-10-31)](2026-10-kazakhstan-navy-design-review.md) — navy branch run through design-guide: Russia event routing and gate bugs fixed, descriptions rewritten, open design decisions.
- [Content review principles](2026-10-content-review-principles.md) — reusable checklist, with summary takeaways from Portugal, Poland and Russia.
- [Kazakhstan military tree audit](2026-10-kazakhstan-tree-audit.md) — focus-level issues and technical QA priorities from the focus tree.
- [Kazakhstan aviation fact-check](2026-10-kazakhstan-aviation-fact-check.md) — China / US / Iran procurement status and recommendations for the 2000–2030 sandbox.
- [Standard vs MD skill and country trees](2026-10-standard-vs-country-trees.md) — comparison with the Claude/MD skill and static review of Portugal, Russia, Syria, Armenia, Israel, Poland and Kazakhstan.
- [External dependency registry](external-dependencies.md) — registry of unresolved and external IDs with source policy, status (`confirmed` / `assumption` / `unknown`) and verification evidence; machine-readable copy: `external-dependencies.json`; auditor output: `_external_dependencies`.
- `audit-baseline.json` — служебный baseline известных ERROR-находок `tdf_audit.py` (отпечатки без номеров строк). Не читать целиком; сравнение и обновление: `skills/tdf-country-content/scripts/tdf_baseline.py check` / `update`.

These documents are research and recommendations, not game-script patches. Findings marked as localisation candidates require checking shared focuses and text overrides before edits. The initial Stage 9 static note remains a partial source review; the executed validation report records the actual unittest and full/per-country auditor results. Neither report claims HOI4 runtime validation.

## Skills
- [`skills/tdf-country-content`](../../skills/tdf-country-content/SKILL.md) — how to write focuses, national spirits, events and localisation for TDF, plus `scripts/tdf_audit.py` and `scripts/tdf_inventory.py`.
