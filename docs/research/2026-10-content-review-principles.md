# Content review principles for TDF / MDC

This note condenses the common recommendations from prior reviews of Portugal, Poland and Russia. It is intended as a reusable checklist, not a replacement for country-specific line-by-line reviews.

## Focus-tree design
- Every focus should advance a distinct political, industrial, military, diplomatic or narrative goal.
- Avoid chains of mechanically similar focuses that differ only in names or small reward variations.
- Make requirements match the narrative. A focus on foreign procurement should not require domestic industrial localization unless the purpose is specifically to localize imported equipment.
- If branches represent alternatives, make them alternatives: use OR requirements, choices or decisions rather than forcing every route.
- Keep costs and rewards proportional; large research discounts, free equipment, factories, resources and national spirits should have a clear reason.
- Prefer rewards that fit the focus title and strategic role. Separate communications from radar, airframes from transport aviation, and generic industry from a specialized manufacturer.
- Ensure capstones are achievable without unrelated optional industry or diplomacy focuses.

## Localization and flavor
- The title, description, historical framing and effect should describe the same program.
- Explain why a reform matters, not just what modifier it grants.
- Avoid unsupported historical claims. Label speculative or alternate-history choices explicitly.
- Keep terminology consistent across focuses, events, national spirits, equipment variants and localization.
- Do not claim a company or institution is being “created” if it already exists; model expansion, modernization or localization instead.

## Script and balance QA
- Verify all focus IDs, prerequisite IDs, event IDs, idea IDs, technology IDs, equipment variants, MIOs and scripted effects exist.
- Check case sensitivity of IDs, scopes, target countries and state IDs.
- Confirm actual rewards are inside executable effects such as `completion_reward`; `effect_tooltip` may only display a preview.
- Check category bonuses for unintended breadth and overlap.
- Check unique names for mastery/research bonuses and valid use counts.
- Validate resource/treasury costs and ensure the player can afford them in a normal run.
- Test focus reachability, mutually exclusive paths, AI selection, localization display, and completion in-game.
- Static review cannot fully confirm custom scripted effects or gameplay balance without the relevant files and a test run.

## Country review takeaways
### Portugal
Use the country’s actual strategic context and institutions rather than treating its tree as a generic major-power template. Validate that industrial and military branches offer distinct choices and that effects are paced sensibly.

### Poland
Pay particular attention to the relation between national direction, modernization, foreign cooperation and domestic production. Procurement and localization should be distinct but connect logically; avoid making every external partnership mandatory.

### Russia
Because the country has a large and complex tree, consistency, prerequisite clarity, event/idea dependencies and reward scale are especially important. Separate flavor from effects and validate long chains, overlapping bonuses and technical IDs systematically.

These are summary-level takeaways, not exhaustive claims about every focus in the reviewed files. Country-specific detailed notes remain the authority for individual examples.

## Kazakhstan-specific application
- Preserve the core of `KAZ_reorganization_infantry`, but validate technology categories, event IDs, bonus IDs and the final readiness prerequisites.
- Move AHKE to aviation; it already exists. Model helicopter assembly/MRO, training and localization.
- Separate Kazakhstan Engineering (broad coordination) from Kazakhstan Paramount Engineering (wheeled protected vehicles).
- Rebuild aviation around legacy-fleet maintenance, Su-30SM readiness, AHKE, UAV integration, transport aviation and integrated air defense.
- Keep the Caspian focus for the navy: patrol, ports, minesweeping, hydrography, anti-sabotage and domestic shipbuilding.
- Distinguish documented procurement from speculative alternate history, particularly in the China / US / Iran branches.
