# Aral mechanic: unresolved target-TDF dependencies

TDF is a standalone mod. This file records what the focused Aral branch itself does not define; it does not assign missing identifiers to another mod.

## Documented in the MDC wiki

| Identifier | Wiki reference | What the wiki establishes |
|---|---|---|
| `modify_treasury_effect` | [Economy effects](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/effects/economy.md) | Usage example with `treasury_change`; implementation side effects are not specified by the example |
| `custom_cost_trigger`, `custom_cost_text` | [Culture and tourism](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/triggers/culture-tourism.md) | Trigger and display-label roles; Aral uses an always-true trigger so the price display does not impose a treasury gate |
| `cost_X_Y` | Shared `mdredux/localisation/english/MD_decisions_l_english.yml` at the reviewed TDF revision | Existing generic treasury-cost labels; Aral references them directly and does not duplicate their localisation |

Political Power uses native decision `cost = N`. Each Aral project charges its full cash price once in `complete_effect` through `modify_treasury_effect`; the TDF treasury system automatically finances a negative balance through national debt. Aral therefore does not call `modify_debt_effect`, split project prices into treasury/debt components, or gate project/event spending on the current treasury balance. Project timers and non-financial effects remain unchanged.

## Modifier identifiers

The following identifiers are documented in MDC. Check scope against the corresponding page rather than relying on names alone:

| Modifier | Wiki reference |
|---|---|
| `stability_factor`, `political_power_factor` | [Political modifiers](https://github.com/minusleto/MDC/blob/main/src/content/docs/en/code-resource/modifiers/political.md) |
| `state_productivity_growth_modifier`, `local_building_slots_factor`, `recruitable_population_factor` | [Regional modifiers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/modifiers/regional.md) |

The active mechanic no longer uses country-wide agricultural, population, unemployment or migration modifiers. Those ecological effects are state-scoped; the two event-only national spirits use only political stability and political-power modifiers. Whether a documented modifier is appropriate for this mechanic is a separate design decision from whether the identifier exists.

## Sprite dependencies still requiring target-file confirmation

The two event-only national spirits use existing vanilla HOI4 sprite `GFX_idea_generic_agrarian_society`; the local state fallout modifier uses `GFX_idea_generic_agrarian_reform`. Both are defined in the base game's [`interface/ideas.gfx`](https://github.com/Killeritch/Hearts-of-Iron-IV/blob/master/interface/ideas.gfx#L2190-L2212) / [agrarian reform entry](https://github.com/Killeritch/Hearts-of-Iron-IV/blob/master/interface/ideas.gfx#L2906-L2912). The help icon now uses vanilla `GFX_help_button`, defined in [`interface/menubar.gfx`](https://github.com/Killeritch/Hearts-of-Iron-IV/blob/master/interface/menubar.gfx#L182-L184). No custom icon or texture is required for the Aral modifiers or help button. The `ARAL_HELP_TT` English and Russian tooltip texts are present in the Aral localisation files.

## Verification rules

- A wiki entry confirms that an identifier is documented; it does not prove implementation, runtime scope or side effects in the target build.
- An identifier absent from this branch is unknown, not automatically invalid or supplied by another project.
- If the MDC wiki does not document the required behaviour, ask for the exact target TDF source file.
- Keep runtime, GUI and load-order claims unverified until tested against the target TDF installation.
