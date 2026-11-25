# Aral mechanic: unresolved target-TDF dependencies

TDF is a standalone mod. This file records what the focused Aral branch itself does not define; it does not assign missing identifiers to another mod.

## Documented in the MDC wiki

| Identifier | Wiki reference | What the wiki establishes |
|---|---|---|
| `modify_treasury_effect` | [Economy effects](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/effects/economy.md) | Usage example with `treasury_change`; implementation side effects are not specified by the example |
| `modify_debt_effect` | [Economy effects](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/effects/economy.md) | Usage example with `debt_change`; implementation side effects are not specified by the example |
| `custom_cost_trigger`, `custom_cost_text` | [Culture and tourism](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/triggers/culture-tourism.md) | Affordability condition and display-label roles |

The MDC wiki searches checked on 2026-11-26 did not return entries for `ai_hint_pp_cost` or `has_political_power`; these helpers are not used by Aral decisions. Political power now uses native `cost = N`. This pattern is present in target-TDF decisions `SOV_nabi_techosphere_agremmeent` and `SOV_nabi_silkroad_agremmeent` in [Russia.txt at the reviewed TDF revision](https://github.com/minusleto/Make-TDF-Great-Again/blob/ff3e760dbde6e97cdeb16bc7c13b2ba3f94a49db/mdredux/common/decisions/Russia.txt), where native PP `cost` coexists with a treasury `custom_cost_trigger`. The treasury display/charge uses the [MDC custom-cost reference](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/triggers/culture-tourism.md) and the [TDF Georgia example](https://github.com/minusleto/Make-TDF-Great-Again/blob/ff3e760dbde6e97cdeb16bc7c13b2ba3f94a49db/mdredux/common/decisions/Georgia.txt). Treasury and debt remain charged in `complete_effect` when a project starts; project timers and all PP, treasury and debt amounts are unchanged.

## Modifier identifiers

The following identifiers are documented in MDC. Check scope against the corresponding page rather than relying on names alone:

| Modifier | Wiki reference |
|---|---|
| `agricolture_productivity_modifier`, `agriculture_tax_modifier`, `monthly_population`, `high_unemployment_threshold_modifier`, `base_unemployment_modifier` | [Economic modifiers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/modifiers/economic.md) |
| `migration_rate_value_factor` | [Migration modifiers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/modifiers/migration.md) |
| `state_productivity_growth_modifier`, `state_monthly_population`, `local_building_slots_factor`, `recruitable_population_factor` | [Regional modifiers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/modifiers/regional.md) |

The MDC wiki documents both `monthly_population` and `state_monthly_population`, and documents both `base_unemployment_modifier` and `high_unemployment_threshold_modifier`. The audit must not reject either of the former identifiers as unsupported. Whether a modifier is appropriate for this mechanic is a separate design decision from whether the identifier is documented.

## Sprite dependencies still requiring target-file confirmation

The Aral GUI refers to `GFX_destroyed_dam` and `GFX_help_button_custom`. Their target-TDF definitions and texture paths are not included in this focused branch. Confirm them in the target TDF interface/GFX files supplied by the user before relying on them or replacing them.

## Verification rules

- A wiki entry confirms that an identifier is documented; it does not prove implementation, runtime scope or side effects in the target build.
- An identifier absent from this branch is unknown, not automatically invalid or supplied by another project.
- If the MDC wiki does not document the required behaviour, ask for the exact target TDF source file.
- Keep runtime, GUI and load-order claims unverified until tested against the target TDF installation.
