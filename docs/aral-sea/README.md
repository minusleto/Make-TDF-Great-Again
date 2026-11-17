# Aral Sea mechanic (Kazakhstan)

A slow, risky, historically calibrated restoration of the Northern Aral. Numbers come from the real project
(Kokaral dam, SYNAS, Phase II with the Amanotkel complex, the older second-dam plan). Design notes and the
reasons for every choice are in issue #12.

## How it works
- `aral_sea_restoration` (-30..100) is the water restored. Level in metres = 30 + 0.23 x restoration
  (0 = about 30 m, the low point; 54 = 42.4 m; 61 = 44 m; 70 = 46 m; 100 = 53 m, the sea of 1960, never reachable).
- A **dam crest** is the highest level the sea can reach: no dam 100, Kokaral 54, Phase II 61, Second Dam 70.
  Water above the crest spills away, so extra rain or projects cannot push the sea past its plans.
- The sea dries by 0.20%/month; behind an earth dike 0.10; after the Kokaral dam 0.06, then -0.04 for the Uzbekistan flow
  agreement and -0.04 for irrigation modernization (with both the river slowly refills the sea); the Second Dam adds +0.03.
- Finished projects put water into `aral_pending`; 15% of it (min 0.5) arrives every month.
- `aral_relief` (forests, fisheries, IFAS) eases the fallout but adds no water.
  Penalties scale with `aral_deficit = 100 - restoration - relief`.
- Once a year the Syr Darya is dry (20%), wet (15%, +2 water) or normal. A dry year is an event: pay 0.03 bn + 15 PP for
  extra releases or lose 3% (2% with Aklak, 1% with Amanotkel, +2% after the Second Dam).
- The earth dike halves the drying but is washed out with 3% chance per month until the Kokaral dam stands.
- **Control of the coast.** Every decision needs `controls_state = 717` (Kyzylorda, the Aral coast), and the monthly tick runs only while
  Kazakhstan exists and controls it. Building effects and state modifiers touch a state only while Kazakhstan owns it
  (`is_owned_by = ROOT`), so a conqueror never gets free infrastructure. A lost coast freezes the sea until it is retaken.

## Projects (14 decisions)
IFAS programme, SYNAS loan, emergency dike, Syr Darya channel, Kokaral dam, Aklak works, irrigation modernization,
fisheries (needs 36 m), protective forests I and II, Uzbekistan flow agreement, Amanotkel complex, then one of
Phase II (44 m) or the Second Dam (46 m, about twice the cost, wide surface evaporates more). Both need 42 m.

## Files
`common/` decisions, scripted_effects, scripted_triggers, dynamic_modifiers, on_actions, scripted_guis, scripted_localisation;
`events/aral_sea_events.txt` (dry year, dike washed out, salt storms); `interface/aral_sea.gui|gfx`, `gfx/`; EN and RU localisation;
three lines in the KAZ history file. `optional/aral_sea/` holds a focus-gated trigger set, six focuses and a province photo
(not loaded). Install the on_actions file only if your mod has no `on_monthly` block, otherwise merge the call
`aral_monthly_tick = yes` for KAZ.

## Tools (run from the repository root)
```
python3 -I skills/md-hoi4-country-content/scripts/mech_audit.py mdredux --prefix aral
python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux
python3 -I skills/md-hoi4-country-content/scripts/aral_model_sim.py mdredux --income 0.03 --route dam2 --dike yes --once --seed 5
```
The simulator parses the code, so its report never drifts from the mod. Treasury income and political power per month
live in the base mod and are parameters.

## In-game check (what the scripts cannot see)
- [ ] `error.log` has no lines about `aral`, `aral_sea.gui`, the decisions or the events.
- [ ] Let an enemy take control of state 717 (console `controlled_by`/occupation): every decision is greyed out with the tooltip about the Kyzylorda region and the sea stops changing.
- [ ] Day 1: the panel shows 30 m, the picture frame 4, penalties on the national spirit and on Kyzylorda (state view).
- [ ] The price line of a decision shows treasury and PP (for example `$0.15 bn + 60 PP`) and fits in the row.
- [ ] Take IFAS, the loan and the dike: the dike halves the monthly change in the tooltip of the trend line.
- [ ] Console `set_country_flag aral_dike`, then wait: the washed-out event appears at about 3% per month and `Rebuild` charges 0.04 bn.
- [ ] Console `set_variable aral_year_clock = 11` and wait a month: roll of dry / wet / normal year.
- [ ] After Kokaral the sea fills to 42.4 m within a year and does not go higher however much water is added.
- [ ] Phase II and the Second Dam stay locked below 42 m and exclude each other; the second one adds drying and dry-year loss.
- [ ] Ticks on the bar: 36, 42, 44, 46 m; the part of the bar to the right of 46 m stays empty (the lost sea).
- [ ] The picture frame follows the restoration (1..7) and the status text changes (critical, drying, stable, recovering).
