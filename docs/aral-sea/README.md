# Aral Sea mechanic (Kazakhstan)

The Northern (Small) Aral, restored step by step as in reality: the Kokaral dam, SYNAS, Phase II with the Amanotkel complex
and the older second-dam plan. Design notes and the reason for every choice are in issue #12.

## The real picture it is built on
- Since the 1987-1989 split the Small Aral stands at about **40 m** above the Baltic (the sill of the Berg Strait: whatever
  is above it spills into the Large Aral). It did not collapse, its problem was salt, a shrinking shoreline and no fish.
- The earth dikes of the 1990s were broken by spring floods again and again (the last in April 1999).
- The Kokaral dam (2005) lifted the level to **42 m** within about six months; the crest limits it. Phase II aims at **44 m**
  (3,913 km2); the older plan with a second dam aimed at about 46 m.

## How it works
- `aral_sea_restoration` (-30..100) counts **decimetres above 40 m**: 0 = 40 m, 20 = 42 m, 40 = 44 m, 60 = 46 m.
- A **crest** is the highest level the sea can reach: nothing 40 m, an earth dike 41, Kokaral 42, Phase II 44, Second Dam 46.
  Water above the crest spills away, so extra rain or projects never push the sea past its plans.
- The river refills a sea that stands below its crest: +0.05 dm/month, +0.05 more for each of the Syr Darya channel, the
  Uzbekistan flow agreement and irrigation modernization; the Second Dam evaporates -0.10.
- Finished projects put water into `aral_pending`; 15% of it (min 0.5) arrives every month.
- `aral_relief` (forests, fisheries, IFAS) eases the fallout and adds no water. `aral_deficit = 100 - 1.25 x restoration - relief` scales the local state modifier only; there is no nationwide ecological productivity, population or migration penalty.
- **Regional coordination.** Once per year, a deficit above 70 triggers a warning if no monitoring programme exists. Funding monitoring costs $0.5 bn + 25 PP and prevents escalation. Postponing adds a two-year temporary national spirit (stability −2%, political power gain −3%); after 540 days a second event offers a $1.0 bn + 50 PP response. Ignoring it replaces the temporary spirit with a permanent crisis spirit (stability −4%, political power gain −5%). The crisis can later be removed with `aral_regional_response` ($1.5 bn + 60 PP, 365 days). These national modifiers represent the political cost of delayed government coordination, not environmental damage across all Kazakhstan.
- Once a year the Syr Darya is dry (20%), wet (15%, +2 dm) or normal. A dry year is an event: pay 0.3 bn + 15 PP for extra
  releases or lose 3 dm (2 with Aklak, 1 with Amanotkel, +2 after the Second Dam). The first spring brings salt storms
  unless the first forests stand; rebuilding a washed-out dike costs 0.4 bn, and shelter belts in a salt-storm event cost 0.5 bn.
- The earth dike lifts the crest to 41 m but is washed out with 3% chance per month until the Kokaral dam stands;
  the sea then falls back to 40 m.
## Monetary calibration

All Aral treasury and debt amounts below are multiplied by 10 versus the previous implementation. Political Power costs, project durations, restoration gains, event probabilities and effects are unchanged. This follows the price scale in TDF rather than treating a national water programme as a token expense: direct treasury spending in Kazakhstan's focus tree has a median of 3.5 bn (p75 5 bn), and the reviewed Kazakhstan events have a median of 5.5 bn (p75 7.5 bn). The same main-branch sample shows Georgian infrastructure decisions of 8-20 bn and Russian stream-preparation decisions of 15 bn each. TDF also documents small/medium/large expenditure effects as 0.2% / 0.4% / 0.6% of GDP; those are relative expense tiers, not fixed cash prices.

The 2000 Kazakhstan history starts with 0.245 bn in treasury and 16 bn in debt, so these projects are intentionally staged and usually require time to build reserves and/or borrow. The cash thresholds, charges and debt additions match exactly.

| Project | Treasury | Debt | Total |
|---|---:|---:|---:|
| IFAS basin programme | 0.5 bn | — | 0.5 bn |
| SYNAS loan preparation | 0.5 bn | — | 0.5 bn |
| Emergency earth dike | 0.5 bn | — | 0.5 bn |
| Syr Darya channel | 0.5 bn | 1 bn | 1.5 bn |
| Kokaral dam | 1.5 bn | 3 bn | 4.5 bn |
| Aklak works | 0.5 bn | 0.5 bn | 1 bn |
| Irrigation modernization | 4 bn | 4 bn | 8 bn |
| Fisheries | 1 bn | — | 1 bn |
| Protective forests I | 1.5 bn | — | 1.5 bn |
| Mass saxaul programme | 4 bn | 4 bn | 8 bn |
| Uzbekistan flow agreement | 0.5 bn | — | 0.5 bn |
| Amanotkel complex | 4 bn | 4 bn | 8 bn |
| Phase II | 3 bn | 7 bn | 10 bn |
| Second Dam | 7.5 bn | 17.5 bn | 25 bn |
| Siberian-water study request | 0.5 bn | — | 0.5 bn |
| Siberian canal | 7.5 bn | 32.5 bn | 40 bn |
| Siberian pipeline | 10 bn | 40 bn | 50 bn |
| Regional recovery programme | 1.5 bn | — | 1.5 bn |

Recurring or event costs: a dry-year release 0.3 bn + 15 PP; dike rebuild 0.4 bn; salt-storm shelter belts 0.5 bn; regional monitoring 0.5 bn + 25 PP; the second regional response 1 bn + 50 PP. Siberian water fees are 0.6 bn/year for the canal and 0.4 bn/year for the pipeline; the accepted +50% price review is capped at 1.5 bn/year.

Benchmarks: [TDF economy effects and expenditure tiers](https://github.com/minusleto/Make-TDF-Great-Again/blob/1d85eb92c2afc9f60a074ce8b2a51430a50d098e/wiki/docs/code-resource/effects/economy.md), [Kazakhstan focus tree](https://github.com/minusleto/Make-TDF-Great-Again/blob/1d85eb92c2afc9f60a074ce8b2a51430a50d098e/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt), [Kazakhstan events](https://github.com/minusleto/Make-TDF-Great-Again/blob/1d85eb92c2afc9f60a074ce8b2a51430a50d098e/mdredux/events/Kazakhstan.txt), [Georgia infrastructure decisions](https://github.com/minusleto/Make-TDF-Great-Again/blob/1d85eb92c2afc9f60a074ce8b2a51430a50d098e/mdredux/common/decisions/Georgia.txt), [Russian infrastructure decisions](https://github.com/minusleto/Make-TDF-Great-Again/blob/1d85eb92c2afc9f60a074ce8b2a51430a50d098e/mdredux/common/decisions/Russia.txt).

- **Ownership of the coast.** All 17 restoration/supply decisions and the conditional regional-recovery decision require Kazakhstan to own state 717 (Kyzylorda) in `available` via `owns_state = 717`. Losing the coast after a project has started does not cancel its `days_remove` timer: there is no ownership-based `cancel_trigger` / `cancel_effect`, so the normal `remove_effect` still runs. The monthly tick and `update_aral_sea` recalculation remain gated by KAZ ownership of 717. State dynamic modifiers are intentionally attached to their states and are **not removed** when ownership changes. Their last calculated values remain on the state while another country owns it; recalculation resumes when Kazakhstan owns the coast again. State construction effects remain limited to states currently owned by Kazakhstan.

## Focus gates
The decision groups are tied to existing KAZ economic milestones. Decisions remain visible but grey until the relevant focus is complete; the available-state tooltip names the required focus:

| Decision group | Required Kazakhstan focus |
|---|---|
| Initial programme (IFAS, loan, dike, first saxaul) | `KAZ_economy` |
| Syr Darya works (channel, Kokaral, Aklak) | `KAZ_fight_capacity_deficit` |
| Agricultural projects (irrigation, fisheries) | `KAZ_ABP` |
| Second forest programme | `KAZ_ecologization` |
| Amanotkel and final dam choice | `KAZ_balance_north_and_south` |
| Uzbekistan agreement and Siberian-water talks | `KAZ_foreign_policy` |

The six-focus package under `optional/aral_sea/optional_focus_tree/` is an archival placeholder from before the current KAZ tree was available; do not install it or overwrite the active trigger file with it.

## Projects (14 decisions) and the Siberian chain (3 more)
IFAS programme, SYNAS loan, emergency dike, Syr Darya channel, Kokaral dam, Aklak works, irrigation modernization,
fisheries (needs 41.5 m), protective forests I and II, Uzbekistan flow agreement, Amanotkel complex, then one of
Phase II (44 m) or the Second Dam (46 m, about twice the cost, evaporates more). Both need 41.5 m.

## Siberian water (the Sibaral question)
What really happened: the Soviet plan to turn Siberian rivers south was approved in 1976 and ended by a Politburo decision in
1986. In 2002 Uzbekistan and the mayor of Moscow revived it, Putin asked a commission to study it, the press mocked it and
nothing was decided. Nazarbayev backed it in 2006 and again in 2010, and in 2025 the idea came back with pipelines. It has
never been approved or built. The mechanic therefore mostly fails, and success is a costly dependency, not a gift.
1. **Request** (`aral_sibaral`, 50 PP, needs IFAS and the loan, Russia must exist): Russia studies it (60%, never at war) or declines.
2. **Commission** (540 days): feasible 15%, more studies 30% (another year), shelved 55% (closed for 15 years, then it can return).
3. **Technology**, only if feasible and the Kokaral dam stands: the **canal** (8 years, 40 bn total: 7.5 bn treasury + 32.5 bn debt, more water, fee 0.6 bn a year,
   15% a year that Russia reopens the price) or the **pipeline** (5 years, 50 bn total: 10 bn treasury + 40 bn debt, less water, fee 0.4 bn, 8%). They exclude each other.
4. **Effect:** the sea refills faster (+0.30 / +0.15 dm a month), a dry year costs 3 / 2 dm less, agriculture +8% / +4%.
   It never raises the crest: only the dams do that.
5. **Dependence:** every year the fee is paid; a price review means +50% to the fee for good, or no supply for two years
   (no benefits, no fee). The +50% increase is accepted only while the new annual fee stays at or below **1.5 bn**;
   if it would exceed the cap, Kazakhstan must refuse the price and wait two years without supply. Roughly one run in four gets the water within 35 years.

## Player interface

The two event-only national spirits use vanilla `GFX_idea_generic_agrarian_society`; the local state modifier uses vanilla `GFX_idea_generic_agrarian_reform`; the panel help marker uses vanilla `GFX_help_button`. No custom texture is required for these entries. Hovering the question-mark icon opens a guide to the 40 m baseline, dam crest, gradual project inflow, hydrology and the ownership/focus gates.

The level readout states its deviation from the natural 40 m mark. The monthly line now explicitly distinguishes a rise, a decline and no change, in metres per month.

## Install into the game

Copy only the repository's `mdredux/` folder into the `mdredux/` directory of the target TDF installation. Let Windows merge the folders; do not delete or replace the existing folder. The active files are Aral-specific and use their own filenames, including `common/on_actions/aral_sea_on_actions.txt`.

No Kazakhstan history file is included or needs editing. On a new game, the standalone on_startup hook initializes the mechanic after country selection; the same file contains the ownership-gated monthly tick. Keep this file next to the target TDF files in common/on_actions/—do not replace existing on_actions files or manually merge their contents. The active mechanic uses existing KAZ focus IDs, so keep your installed Kazakhstan focus tree.

optional/aral_sea/ holds an obsolete six-focus prototype and a province-photo prototype; neither is copied into the game and neither is required by the active mechanic.

## Tools (run from the repository root)
```
python3 -I skills/aral-sea-mechanic/scripts/mech_audit.py mdredux --prefix aral
python3 -I skills/aral-sea-mechanic/scripts/aral_model_sim.py mdredux
python3 -I skills/aral-sea-mechanic/scripts/aral_model_sim.py mdredux --income 0.03 --route dam2 --dike yes --once --seed 5
```
The simulator parses mechanic formulas, project timings and costs from the code. Starting treasury defaults to the KAZ
2000 baseline of 0.245 bn and can be overridden with `--treasury`; monthly treasury income and political power
remain simulation inputs not defined by this mechanic's source files.

## In-game check
The full list with expected numbers is in issue #12.
