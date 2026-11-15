# Aral Sea mechanic: install notes and in-game checklist

## Install (copy into your mod folder, overwrite when asked)
Everything is relative to the mod root. **Do not copy a descriptor.mod** (none is included).

| Path | What it is |
|---|---|
| `history/countries/KAZ - Kazakhstan.txt` | your file + 5 lines (start values + setup). Replaces any startup file |
| `common/decisions/aral_sea_decisions.txt`, `categories/aral_sea_categories.txt` | 16 project decisions + 3 debug decisions |
| `common/scripted_effects/aral_sea_effects.txt` | all maths: level, debuffs, picture frame, monthly drift, state tiers |
| `common/scripted_triggers/aral_sea_triggers.txt` | focus-tree unlock hooks (all open) + debug switch |
| `common/scripted_localisation/aral_sea_scripted_loc.txt` | status text, text bar |
| `common/dynamic_modifiers/aral_sea_modifiers.txt` | country spirit + state modifier |
| `common/scripted_guis/aral_sea_category_gui.txt`, `interface/aral_sea.gui`, `interface/aral_sea.gfx` | the panel inside the decisions tab |
| `common/on_actions/aral_sea_on_actions.txt` | **monthly only** (merge if you already have on_monthly) |
| `gfx/interface/aral_sea/*.dds`, `gfx/interface/modifiers/aral_sea.dds` | art (about 435 KB in total) |
| `events/aral_sea_events.txt` | 9 events (completions, outcomes, warnings, milestones); pictures are vanilla placeholders |
| `optional_focus_tree/` | **not active.** Shared-focus branch (6 focuses) + focus-gated triggers + localisation (section K) |
| `optional_province_photo/` | **not active.** 4 photos for the state view + snippets (section L) |
| `localisation/english/…`, `localisation/russian/…` | all text, no years |

Delete leftovers from older versions: `gfx/interface/decisions/decision_category_aral_sea.*`, old `aral_sea_picture*.dds` (except the strip), any old `aral_sea_gui.txt`.

## Start a NEW game as KAZ (old saves hold old variables)

### A. Logs (do this first)
- [ ] Open `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`. No lines mention `aral`, `aral_sea.gui`, `aral_sea_decisions`.
- [ ] If an unknown-modifier error appears, note which one (MDC names used: `agricolture_productivity_modifier`, `productivity_growth_modifier`, `migration_rate_value_factor`, `base_unemployment_modifier`, `agriculture_tax_modifier`, `state_productivity_growth_modifier`, `state_monthly_population`, `local_building_slots_factor`, `recruitable_population_factor`, `state_renewable_energy_generation_modifier`).

### B. Day 1 state
- [ ] National spirit "Impact of the Aral Sea" exists. Expected at 0%: agriculture productivity -10%, infrastructure speed -10%, productivity growth -3%, pop growth -3%, migration -5%, unemployment +5%, agriculture tax -10%.
- [ ] State modifier "Aral Sea Fallout" on Kyzylorda (717): productivity -10%, pop -5%, building slots -6%, recruitable -10%. Half of that on Turkistan 1224, Aktobe 1231, Ulutau 1226. A quarter on Mangystau 1230 and Atyrau 718. Nothing on other states.
- [ ] Other tags (e.g. UZB, RUS) have no Aral category and no panel.

### C. Panel (decisions tab, "The Aral Sea")
- [ ] Order top to bottom: stats row, framed picture, bar, status row, banner, then decisions.
- [ ] Shows: Water level 30.0 m, Restoration 0%, status Drying, empty bar with a **white zero marker**, the 2000 photo.
- [ ] Scale labels under the bar: `-30%` at the left end, `0%` under the white marker, `100%` at the right end.
- [ ] Picture is centered with a frame; no text overlaps anything; "0%" and "100%" labels are visible at the bar's ends.
- [ ] White zero marker + three gold ticks (36 / 42 / 44 m); hovering each shows its tooltip.
- [ ] Banner reads "Restoration projects" (Russian: "Проекты восстановления") and is centered on the ribbon.
- [ ] Rows from top: stats, picture, bar, scale labels, status, per-month row, banner. Nothing overlaps (the zero label must not touch the status text).

### C2. Monthly change (new)
- [ ] **Russian: the row must show real letters, no `?`** (it uses hoi_18mbs, the font with Cyrillic). Metres show 3 decimals (e.g. -0.046).
- [ ] A row under the status line reads "Per month: -0.20% / -0.046 m" (red). Hover it: tooltip lists the four rates and "Now: ...".
- [ ] National spirit tooltip ends with "Water level: X m. Change per month: -0.20% (-0.05 m)". Kyzylorda's "Aral Sea Fallout" tooltip ends with its own level/change line (state variables). **If the state line shows 0.0 or empty, tell me: that is the one uncertain scope.**
- [ ] After the Kokaral Dam completes the row turns to -0.05%; after the Uzbekistan agreement -0.02%; after irrigation too it shows yellow 0.00%.
- [ ] Advance one month: restoration drops by exactly the shown amount and the level by 0.23 x that.
- [ ] Reaching -30 shows 0.00% (floor).

### D. Debug decisions (set `aral_debug_enabled = { always = no }` before release)
Click "Improve (+10%)" / "Worsen (-10%)" and check the panel updates **immediately** (if it lags, `dirty` is the suspect).

| Restoration | Level | Status | Picture frame |
|---|---|---|---|
| -30 | 23.1 m | Desertifying | 2014 (driest) |
| -20 | 25.4 m | Desertifying | 2009 |
| -10 | 27.7 m | Desertifying | 2006 |
| 0 | 30.0 m | Drying | 2000 |
| 10 | 32.3 m | Drying | 1998 |
| 40 | 39.2 m | Stable | 1987 |
| 70 | 46.1 m | Recovering | 1977 |

- [ ] Frame changes happen at -8, -15, -22, 10, 35, 65 (the table rows sit between thresholds).
- [ ] Bar is two-sided: blue fills **right** of the zero marker (1 segment per 2%; at 50% exactly 25), red fills **left** (1 segment per 2% below zero; at -10% exactly 5; at -30% all 15).
- [ ] Status flips: Desertifying below -8, Drying below 25, Stable from 25, Recovering from 60.
- [ ] "Reset" returns to 0 / 30.0 m / 2000 photo. Debuffs in the spirit and state tooltips shrink as restoration rises and grow below 0.
- [ ] Restoration cannot go below -30 or above 100.

### E. Projects, money, tooltips
- [ ] Each decision row shows the **treasury share** on the right (e.g. `$1 bn` for irrigation; Russian `1 млрд $`), **red when the treasury is below it**. No `_blocked` text anywhere. (Start treasury is 0.245, so everything above that starts red: irrigation 2.0, saxaul 0.7, Amanotkel 1.5, Phase II 0.8, Second Dam 1.2, joint plan 3.0.)
- [ ] The cost also appears in the tooltip.
- [ ] Money leaves the treasury when the project **starts**: only the *treasury share*; the borrowed share goes to **debt** (check both before and after, e.g. irrigation: treasury -1.0, debt +1.0).
- [ ] Requirement lines show readable text with green/red marks (not raw keys).
- [ ] After-completion block shows the gain line and two lines "Modifies <Impact of the Aral Sea / Aral Sea Fallout>" (the `modifies_dynamic_modifier_tt` key must resolve).
- [ ] Hovering a decision highlights Kyzylorda (and Turkistan for channel / irrigation) on the map.
- [ ] Order works: loan -> channel, Kokaral -> Aklak, fisheries (needs 36 m), irrigation (needs channel) -> Amanotkel -> Phase II **or** Second Dam (needs 40 m, mutually exclusive) -> joint plan (needs Uzbekistan agreement + one of them).
- [ ] Completed decisions disappear; the gain is applied at the end of the timer.
- [ ] Channel adds +1 infrastructure in Kyzylorda; irrigation adds +1 agriculture district in Turkistan (if no free slot, note it).
- [ ] Sibaral: tooltip shows 10% / 90%; after it ends either +25% or "rejected", and it does not return.
- [ ] Fisheries / irrigation add their permanent +5% to the spirit.

### F. Monthly drying
Watch restoration over several months (or advance time):
- [ ] No dam: -0.20 per month.
- [ ] After Kokaral: -0.05 per month. With the Uzbekistan agreement: -0.02. With irrigation too: 0.
- [ ] No monthly drift of any kind once restoration reaches -30.

### G. Text and language
- [ ] English and Russian: no raw keys, no `$`/`§` leftovers, no years anywhere, decimal comma in Russian costs.
- [ ] Russian label widths do not wrap or clip in the panel.

### H. Save / load and AI
- [ ] Save, quit, load: panel, picture frame, modifiers and decision timers all intact; modifiers are not doubled.
- [ ] Let the AI play KAZ for a year: no error spam, treasury never driven absurdly negative.

### I. Things I could not verify outside the game
`modifies_dynamic_modifier_tt` key exists in your base loc · MDC modifier names above · `treasury` is the right variable for cost checks · history block applies state-scope dynamic modifiers at the start date · picture `frame` property and `dirty` behave as documented · DXT1/DXT5 textures render without artifacts · hover area of the 9 px ticks. New since the last version: `modify_debt_effect` / `debt_change` units match the treasury's billions (and that MDC's debt system accepts the extra debt) · `custom_cost_text` shows the *treasury share* correctly in the row · ghost segments (50 extra icons) stay cheap thanks to `dirty` · event pictures (vanilla names `GFX_report_event_generic_construction` / `_read_write`) exist in your mod · `remove_province_modifier` syntax (optional photo package) · `shared_focus` include and positions in your tree. Report anything that fails and I'll fix it.

### J. Where the numbers change (so you know what to expect)
- **Every month:** drying drift **and** gradual filling of the pending pool (restoration, level, per-month row).
- **On any project completion / debug click:** restoration, relief, level, all debuffs, picture frame, monthly rate.

### K. Optional: Aral focus branch (`optional_focus_tree/`, shared focuses)
Nothing in this folder is active. Public Millennium Dawn lists its Kazakhstan tree as WIP, so I could not anchor to real focus ids; the branch is built as **shared focuses** you include with six lines.
1. Copy `common/national_focus/KAZ_aral_sea_SHARED_focuses.txt` into your mod.
2. In your Kazakhstan `focus_tree` add `shared_focus = <id>` for each of the six ids (listed at the top of that file).
3. Set `relative_position_id` of `KAZ_aral_programme` to an existing Eco-track focus.
4. Copy the two localisation files.
5. **Then** replace `common/scripted_triggers/aral_sea_triggers.txt` with the version in this folder (installing it first fills the log with unknown-focus errors).
6. Test: each focus shows "Unlocks decisions: ..."; its decisions are hidden until the focus is completed.

| Focus | Unlocks |
|---|---|
| Aral Sea Rehabilitation Programme | IFAS Basin Programme, Protective Forests, SYNAS Loan |
| Syr Darya Water Management | Syr Darya Channel, Kokaral Dam, Aklak Hydro Works |
| Water-Saving Agriculture | Irrigation Modernization, Aralsk Fisheries |
| Green Aral | Mass Saxaul Programme, Aral Ormany Reserve |
| Northern Aral: Phase II | Amanotkel Facility, Phase II, Second Dam |
| Central Asian Water Diplomacy | Uzbekistan Flow Agreement, Joint Southern Aral Plan, Sibaral Talks |

Three-focus variant: Programme + Syr Darya, Water-Saving Agriculture + Green Aral, Phase II + Water Diplomacy (point two triggers at the same focus).

### L. Optional: live photo in the state / province view (`optional_province_photo/`)
Follow `optional_province_photo/README.md` (needs the Aralsk province id and four icons pasted into your `countrystateview.gui`). Until then the empty hook `aral_update_photo` does nothing.

### M. Gradual filling, ghost bar and the 40 m gate (new rules)
- Finished water projects no longer add their points at once: they go into a **pending pool** that fills the sea at 15% of the pool per month (at least 0.5). The pale "ghost" segments on the bar show points that are earned but still arriving. The per-month row shows *filling minus drying* (so it turns green while the sea is filling).
- Phase II and the Second Dam need the **actual** level 40 m (not 42): with the unavoidable drying while the dam is built, 42 m was unreachable, so those projects could never unlock. 42 m stays as an informational tick (viability); 44 m stays as the Phase II target.
- [ ] After a project completes: restoration does not jump; ghost segments appear right of the blue ones; restoration rises over ~1-2 years; pending in the tooltip shrinks to 0.
- [ ] Per-month row: negative while only drying, positive (green) while filling, 0.00% (yellow) when both are zero.
- [ ] Debug "improve / worsen" change restoration **immediately** (they bypass the pending pool); "reset" also clears pending.

### N. Financing (new)
Big projects are paid partly from the treasury and partly by **borrowing** (debt +), like the real World Bank / donor financing. Rows show the treasury share; the tooltip shows the split.

| Project | Total (bn $) | Treasury | Borrowed |
|---|---|---|---|
| Channel / Kokaral / Aklak | 0.1 / 0.15 / 0.05 | 0.03 / 0.03 / 0.01 | 0.07 / 0.12 / 0.04 |
| Protective Forests / Mass Saxaul | 0.2 / 0.7 | 0.1 / 0.49 | 0.1 / 0.21 |
| Irrigation | 2.0 | 1.0 | 1.0 |
| Amanotkel | 1.5 | 0.75 | 0.75 |
| Phase II | 0.8 | 0.12 | 0.68 |
| Second Dam | 1.2 | 0.6 | 0.6 |
| Joint Southern Aral plan | 3.0 | 0.9 | 2.1 |
| Others (IFAS, loan, fisheries, Uzbekistan, Ormany, Sibaral) | 0.05 - 0.1 | all | 0 |

Everything borrowed: about 4.2 bn on the Phase II route (your start debt is 16). Units of `debt_change` are assumed to be the same billions as the treasury (unverified).
- [ ] Start a financed project: treasury drops by the treasury share only, debt rises by the borrowed share.

### O. Events (new)
| Event | Fires when |
|---|---|
| aral_sea.1 The Water Returns | Kokaral Dam completes |
| aral_sea.2 Fish at Aralsk | Fisheries complete |
| aral_sea.3 / .4 Moscow Says No / Siberian Water | Sibaral talks end (90% / 10%) |
| aral_sea.5 Dust Over Kyzylorda | restoration first below -8 (option to pay 0.05 bn for +2 relief) |
| aral_sea.6 The Sea Retreats Again | restoration first below -22 (option to pay 0.1 bn for +3 relief) |
| aral_sea.7 Ships on the Northern Aral | restoration first reaches 60 |
| aral_sea.8 / .9 A Coastline Returns / The Second Dam Holds | Phase II / Second Dam complete |

- [ ] Use the debug decisions to cross -8, -22 and +60: each warning / milestone event fires once (they fire from the update, 2 days later).
- [ ] The pay options are greyed out when the treasury is too low. Pictures show (vanilla placeholders).

### P. Expected progression (verified by a month-by-month simulation, drying + gradual filling)
Water points added: Channel 6, Kokaral 24, Aklak 4, Irrigation 12, Amanotkel 8, Phase II 12 **or** Second Dam 18, Joint plan 8. Level = 30 + 0.23 x restoration.

| | Fast player | Slow player (36-month delay on irrigation, more on Amanotkel) |
|---|---|---|
| Kokaral Dam done | month 18 | month 18 |
| Fisheries unlock (36 m) | month 26 | month 32 |
| 40 m gate reached (Phase II / Second Dam unlock) | month 40 | month 85 |
| Status "Recovering" (60) | month 80 (Phase II) / 69 (Second Dam) | month 126 / 115 |
| Final restoration | 70.3 = 46.2 m (Phase II) / 76.3 = 47.5 m (Second Dam) | 69.8 / 75.8 |

Typical checkpoints (fast, Phase II route): month 12: -0.9 (30.0 m) | 24: 21.4 (34.9 m) | 36: 39.2 (39.0 m) | 60: 50.3 (41.6 m) | 80: 60.0 (43.8 m). Money is not modelled; with the treasury at 0.245, irrigation (1.0) and Amanotkel (0.75) will be the bottlenecks.
- [ ] Compare your game at month 12 / 24 / 36 with these numbers (use the on-screen restoration and level).
