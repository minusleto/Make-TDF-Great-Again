# Kazakhstan military tree audit (29 October 2026)

Scope: static review of `Kazakhstan_Focus_Tree.txt`. This is a review note, not a code patch. Associated localization, ideas, events, MIO, technologies, equipment and scripted effects were not all available, so suspected issues must be confirmed against those files and in-game.

## Infantry reform: keep the core, validate the implementation
The `KAZ_reorganization_infantry` branch has a useful progression from army reform through equipment, communications, logistics, training and professionalization. Main follow-ups:
- `KAZ_arsenal_update`: verify breadth/overlap of `CAT_inf`, `CAT_inf_wep`, `CAT_support_weapons` bonuses.
- `KAZ_new_military_uniform`: confirm `camouflage3` and `camouflage4` tech IDs exist and are reachable.
- `KAZ_communication_systems`: currently mixes communications and radar; verify `tech_combat_radar`, `tech_combat_radar_2`, and custom `two_radar_station`. Consider splitting tactical communications from radar network.
- `KAZ_foreign_equipment`: dependency on `KAZ_Kazakhstan_Engineering` is only thematic if this is about localization, not generic foreign procurement.
- `KAZ_modern_mortars`: bonuses to `CAT_l_at` and `CAT_artillery` may be too broad for the focus title.
- `KAZ_machine_guns`: verify `add_tech_bonus` syntax, unique name, and effect scale for `uses = 2`.
- `KAZ_creation_of_sso`: ensure mastery bonus ID is unique.
- `KAZ_professional_readiness`: remove AHKE as a hard prerequisite or make it optional; land-force professionalism should not require a helicopter enterprise.
- Verify event IDs and case (e.g. `KAZ_army.4` vs `kaz_army.6`) against event files.

## Defense industry
- Separate `KAZ_Kazakhstan_Engineering` (broad defense-industry coordination, procurement, repair, localization) from `KAZ_create_kazakhstan_paramount_engineering` / KPE (wheeled protected vehicles and subsystem integration).
- KPE product catalog lists Arlan, Alan, Nomad, Barys and Terrex-Barys-A families; do not frame it as a universal tank factory.
- `KAZ_btr_barys_6x6`: Barys is a wheeled IFV; check whether `medium_tank_amphibious_chassis_1` is a deliberate game abstraction. Check the commented unit count against the actual `amount`.
- `KAZ_arlan` gives a `CAT_util` bonus; check it matches the intended vehicle localization. `KAZ_alan` and `KAZ_alan_2` had no visible completion reward in the reviewed section; check events/external effects.

## AHKE
AHKE already exists. Rename `KAZ_create_AHKE` to something like `KAZ_expand_AHKE` and focus on helicopter assembly/MRO, component localization, maintenance and training. Move it to the aviation branch; do not make it mandatory for the infantry capstone.

## Navy
Model a Caspian flotilla: maritime border and port security, patrol, minesweeping, hydrography, anti-sabotage and local shipbuilding at Zenit. Review generic `KAZ_Great_Kazakh_Navy`, incorrect-looking army search filters on naval focuses, and `has_idea = KAZ_naval_bonus` prerequisites.

## High-priority technical QA
1. Validate all technology, idea, event, equipment-variant and MIO IDs.
2. Verify scope and event ID capitalization.
3. Distinguish actual `completion_reward` from `effect_tooltip`.
4. Inspect custom scripted effects such as `two_air_base`, `two_radar_station`, and `one_random_dockyard`.
5. Check treasury costs, random state/building effects, and target-state reachability.
6. Test in-game access, balance, AI behavior and focus-tree pacing.
7. Because the scenario starts on 1 January 2000, events from the 2010s/2020s must be future focuses/decisions, not already-completed starting rewards.

## Public references
- Kazakhstan MOD procurement report (2024): https://www.gov.kz/memleket/entities/mod/press/news/details/911924?lang=ru
- KPE product catalogue: https://kpe.com.kz/eng/produkciya/bronemashiny/
- Paramount Group on Barys 6x6: https://www.paramountgroup.com/media/news/kazakhstan-paramount-engineering-s-kpe-barys-6x6-infantry-combat-vehicle-in-production-for-kazakhstan-armed-forces/
- Airbus in Kazakhstan: https://www.airbus.com/en/about-us/our-worldwide-presence/airbus-in-europe/airbus-in-kazakhstan
- MOD aircraft inventory: https://www.gov.kz/org/mod/press/news/details/604613?lang=ru
- MOD on C-295: https://www.gov.kz/memleket/entities/mod/press/news/details/600880?lang=ru
- MOD on A400M: https://www.gov.kz/memleket/entities/mod/press/news/details/921772?lang=ru
- MOD on Su-30SM: https://www.gov.kz/org/mod/press/news/details/119230?lang=en
- MOD on Kazakhstan-China cooperation: https://www.gov.kz/memleket/entities/mod/press/news/details/362248?lang=ru
- Kazakhstan Navy overview: https://www.gov.kz/org/mod/press/news/details/1275277
