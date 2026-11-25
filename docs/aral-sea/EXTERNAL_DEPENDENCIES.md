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
