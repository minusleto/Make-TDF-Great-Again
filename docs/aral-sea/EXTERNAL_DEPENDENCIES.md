# Aral mechanic external dependencies

This focused branch intentionally does not vendor the complete Millennium Dawn base mod. The Aral decisions call two financial effects that must be supplied by the target MD/TDF installation.

Verified against the pinned upstream source snapshot:
- Repository: https://github.com/MillenniumDawn/Millennium-Dawn
- Branch: `main`
- Commit: `04b2ba126fc1057bf2ab4bac0407b3235983994c`
- Snapshot reviewed: 2026-11-25
- This is evidence that the definitions exist at that exact upstream revision, not a compatibility guarantee for every target installation.

| Effect | Definition | Contract used by Aral |
|---|---|---|
| `modify_treasury_effect` | [`common/scripted_effects/00_budget_effects.txt`, line 1643](https://github.com/MillenniumDawn/Millennium-Dawn/blob/04b2ba126fc1057bf2ab4bac0407b3235983994c/common/scripted_effects/00_budget_effects.txt#L1643) | Adds `treasury_change` to `treasury` and refreshes the money UI; the transaction is skipped only when `MD_skip_treasury_cost` is set. |
| `modify_debt_effect` | [`common/scripted_effects/00_budget_effects.txt`, line 1656](https://github.com/MillenniumDawn/Millennium-Dawn/blob/04b2ba126fc1057bf2ab4bac0407b3235983994c/common/scripted_effects/00_budget_effects.txt#L1656) | Adds `debt_change` to `debt`, clamps the result to at least zero and refreshes the money UI. |

Do not copy these upstream definitions into the Aral package. Confirm that the target base mod provides them and check any version-specific differences before integration.

## Reused MD interface sprites

The Aral modifiers and help tooltip reuse sprites already supplied by the Millennium Dawn base mod. They are deliberately not copied into the Aral payload.

| Sprite | Definition | Use |
|---|---|---|
| GFX_destroyed_dam | interface/MD_dynamic_modifiers.gfx (upstream MD) | Existing icon in gfx/interface/dynamic_modifier/destroyed_dam.dds, used by the country and state Aral modifiers. |
| GFX_help_button_custom | interface/MD_help_gui.gfx (upstream MD) | Existing help icon used by the Aral panel tooltip. |

The Aral branch no longer includes a generated modifier icon texture. Confirm these sprite definitions exist in the target base MD version.

## Confirmed Aral modifier keys in the upstream MD base

The following modifiers are used by Aral and were found in the pinned MD source snapshot `8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad` (branch `main`). These are base-mod dependencies: the focused Aral package does not vendor their definitions.

| Modifier | Scope / use | Upstream example |
|---|---|---|
| `agricolture_productivity_modifier` | Country agricultural productivity (the source spelling is intentionally retained) | [Gagauzia ideas](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/ideas/Gagauzia.txt) |
| `agriculture_tax_modifier` | Country agricultural/fishing tax income | [Gagauzia ideas](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/ideas/Gagauzia.txt) |
| `monthly_population` | Country population growth; not valid in state scope | [Greek dynamic modifiers](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/dynamic_modifiers/99_GRE_dynamic_modifiers.txt) |
| `migration_rate_value_factor` | Country migration | [Greek dynamic modifiers](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/dynamic_modifiers/99_GRE_dynamic_modifiers.txt) |
| `high_unemployment_threshold_modifier` | Country unemployment threshold; Aral applies a negative value so unemployment penalties start earlier | [Mercosur dynamic modifiers](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/dynamic_modifiers/05_MERCOSUR_dynamic_modifiers.txt), [Israeli ideas](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/ideas/Israeli.txt) |
| `state_productivity_growth_modifier` | State productivity | [Brazil dynamic modifiers](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/dynamic_modifiers/99_BRA_dynamic_modifier.txt) |
| `local_building_slots_factor` | State building slots | [Brazil dynamic modifiers](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/dynamic_modifiers/99_BRA_dynamic_modifier.txt) |
| `recruitable_population_factor` | State recruitable population | [Rajasthan dynamic modifiers](https://github.com/MillenniumDawn/Millennium-Dawn/blob/8bf8cd0b026a13ae1ffaf84553448fa79a30d2ad/common/dynamic_modifiers/99_RAJ_dynamic_modifiers.txt) |

Two previous identifiers were removed because they were not found in the target MD source: `base_unemployment_modifier` is replaced by `high_unemployment_threshold_modifier`; `state_monthly_population` is removed because HOI4's `monthly_population` does not work in state scope. The state still has three supported debuffs (productivity, building slots and recruitable population), while population growth remains a country-level modifier.
