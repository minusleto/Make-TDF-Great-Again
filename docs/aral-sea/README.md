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
- `aral_relief` (forests, fisheries, IFAS) eases the fallout and adds no water. Penalties scale with
  `aral_deficit = 100 - 1.25 x restoration - relief`.
- Once a year the Syr Darya is dry (20%), wet (15%, +2 dm) or normal. A dry year is an event: pay 0.03 bn + 15 PP for extra
  releases or lose 3 dm (2 with Aklak, 1 with Amanotkel, +2 after the Second Dam). The first spring brings salt storms
  unless the first forests stand.
- The earth dike lifts the crest to 41 m but is washed out with 3% chance per month until the Kokaral dam stands;
  the sea then falls back to 40 m.
- **Ownership of the coast.** Every Aral decision, the monthly tick and `update_aral_sea` recalculation require Kazakhstan to own state 717 (Kyzylorda), using `owns_state = 717`; control/occupation without ownership is not enough. State dynamic modifiers are intentionally attached to their states and are **not removed** when ownership changes. Their last calculated values remain on the state while another country owns it; recalculation resumes when Kazakhstan owns the coast again. State construction effects remain limited to states currently owned by Kazakhstan. If KAZ loses state 717 while a timed Aral decision is running, the timer is cancelled and its `remove_effect` does not run. `cancel_effect` refunds the exact PP, treasury and debt charged at activation, clears any `*_started` flags and resets a pending Siberian study/request. Cancelled decisions can be restarted after KAZ regains the coast; completed-project flags still prevent duplicate projects. The Russian response only records a study result while the Sibaral request is active and KAZ still owns state 717. This cancellation affects project timers only: existing state dynamic modifiers remain attached to their states.

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
3. **Technology**, only if feasible and the Kokaral dam stands: the **canal** (8 years, 4 bn, more water, fee 0.06 bn a year,
   15% a year that Russia reopens the price) or the **pipeline** (5 years, 5 bn, less water, fee 0.04, 8%). They exclude each other.
4. **Effect:** the sea refills faster (+0.30 / +0.15 dm a month), a dry year costs 3 / 2 dm less, agriculture +8% / +4%.
   It never raises the crest: only the dams do that.
5. **Dependence:** every year the fee is paid; a price review means +50% to the fee for good, or no supply for two years
   (no benefits, no fee). The +50% increase is accepted only while the new annual fee stays at or below **0.15 bn**;
   if it would exceed the cap, Kazakhstan must refuse the price and wait two years without supply. Roughly one run in four gets the water within 35 years.

## Files
`common/` decisions, scripted_effects, scripted_triggers, dynamic_modifiers, on_actions, scripted_guis, scripted_localisation;
`events/aral_sea_events.txt` (dry year, dike washed out, salt storms, the Siberian chain); `interface/aral_sea.gui|gfx`, `gfx/`; EN and RU
localisation; three lines in the KAZ history file. `optional/aral_sea/` holds an obsolete six-focus prototype and a province-photo prototype; neither is loaded or required by the active mechanic. Install the on_actions file only if your mod has no `on_monthly` block, otherwise merge the call
`aral_monthly_tick = yes` for KAZ.

## Tools (run from the repository root)
```
python3 -I skills/md-hoi4-country-content/scripts/mech_audit.py mdredux --prefix aral
python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux
python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux --income 0.03 --route dam2 --dike yes --once --seed 5
```
The simulator parses the code, so its report never drifts from the mod. Treasury income and political power per month
live in the base mod and are parameters.

## In-game check
The full list with expected numbers is in issue #12.
