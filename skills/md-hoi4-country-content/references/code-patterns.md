# Code patterns (verify against the mod's wiki; syntax marked [?] is unconfirmed)
## Focus
Order: id, icon, x, y, relative_position_id, cost, prerequisite (separate lines = AND; one block with several = OR), search_filters, available, bypass, completion_reward (first line `log = "[GetDateText]: [Root.GetName]: Focus <id>"`), ai_will_do. Tabs only; log text id must equal focus id (copy-paste mismatch is the most common bug).
## Gates for foreign deals
available = { PARTNER = { has_opinion = { target = TAG value > 9 } has_tech = <tech> } NOT = { has_war_with = PARTNER } } bypass = { NOT = { country_exists = PARTNER } }
## Proposal chain
Focus: `PARTNER = { country_event = { id = ns.N days = 1 } }` + `custom_effect_tooltip = X_tt`.
Proposal event (to partner): accept option -> `FROM = { country_event = { id = ns.N+1 days = 1 } }`, opinion modifier, partner gains treasury + influence ONCE (set_temp_variable percent_change/tag_index/influence_target + change_influence_percentage = yes). Decline -> `FROM = { country_event = { id = generic_decline days = 1 } }`, ai_chance base 5 with `modifier = { has_opinion = { target = FROM value > 9 } factor = 0 }`; accept ai_chance 70.
Reply event (to us): real effects (treasury, set_technology, stock, ideas). effect_tooltip is for display only; never apply real effects there.
Event field order: id, title, desc, picture, (major), is_triggered_only, options. Every option has name and log. Namespaces lower-case consistent. Use the same case as the definition when firing events.
## Effects cheat-sheet (from MD scripted effects)
treasury: set_temp_variable treasury_change then modify_treasury_effect = yes. influence: percent_change, tag_index (gains), influence_target (over whom), change_influence_percentage = yes. military opinion: temp_opinion + change_the_military_opinion = yes (also intelligence/oligarchs variants). swap_ideas = { remove_idea add_idea } to replace; hidden removal + tooltip-only add is a bug.
## Techs
add_tech_bonus = { name(optional) bonus uses(default 1) category/technology }. uses = number of techs; bonus 0.25-0.5 typical. set_technology = { tech = 1 } for deals where the partner already has it (no prerequisite check). Pick categories by meaning (CAT_arty towed artillery, CAT_sp_arty, CAT_l_at light AT/ATGM, CAT_l_aa man-portable AA, CAT_inf_wep small arms, CAT_artillery umbrella arty+AA+AT, CAT_support_weapons, CAT_cnc, CAT_heli, CAT_trans_heli) - check the wiki list.
## Equipment
Tank-chassis APC/IFV/SP gun/MLRS use create_equipment_variant (NSB guard; design_team = mio:... needs AAT guard, so write two variants with if/else). Jeeps/trucks are util_vehicle_0..7 by generation (1965..2035): `set_technology = { util_vehicle_N = 1 }` then `add_equipment_to_stockpile = { type = util_vehicle_equipment amount = X producer = TAG }`. Stock counts should be real.
## MIO / DLC [?]
`has_dlc = "No Step Back"` for NSB chassis/variants/stock; `has_dlc = "Arms Against Tyranny"` for mio: effects/tooltips/design_team. `mio:ID = { add_mio_funds = 500 }` and add_mio_research_bonus are from the brief, unconfirmed. Organization visible triggers must match the focus that announces them.
## Ideas
Hidden ideas (hidden_ideas) are invisible: show them through a defined_text (trigger has_idea -> localization_key X_loc1) referenced from one tooltip string, and keep the tooltip list ordered. Staged ideas: `name = <base idea>` so one loc key serves all stages.
## Misc
add_mastery_bonus exists (vanilla) - parameter names (track/folder) must be checked. Scope typo `random_Army_leader` vs `random_army_leader`. Naval/air tags: check the mod's tags (e.g. Spain SPR) from other trees.
