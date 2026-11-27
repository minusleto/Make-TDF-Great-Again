# HOI4 scripting review — Aral Sea mechanic

**Reviewed:** 2026-11-27  
**Scope:** active files in aral-sea-mechanic and the target-TDF mechanics documented in the MDC wiki.  
**Status:** static source review. No claim is made that the game was launched or that the GUI was runtime-tested.

This is a working checklist for this mechanic, not a complete list of all HOI4 script commands. A token can exist and still be invalid in the current scope. Review every block in context.

## Source priority

1. **The exact target TDF build** is authoritative for TDF-specific scripted effects, triggers, modifiers, economy hooks, sprites and localisation. Check the actual definition and load order, not just an identifier name.
2. **The MDC wiki** documents the project's available scope notes, triggers, variables, effects and modifiers. It is not proof that a particular effect is valid in every HOI4 scope.
3. **HOI4 modding references** help explain engine semantics such as event sender scopes, tag-specific on_actions, decision costs and dynamic modifiers. Community-maintained wiki mirrors are useful references, not substitutes for validating the target game version.
4. **Static tests and the simulator** prove only the invariants they explicitly model. They do not execute Clausewitz script or render the GUI.

Do not use Millennium Dawn as a source of code, modifiers, effects or assumed mechanics. The Digital Frontier is its own project.

## Scope map for the active mechanic

| File / block | Scope to reason about | Required handling |
|---|---|---|
| common/on_actions/aral_sea_on_actions.txt → on_startup | Global hook; no country ROOT scope | Enter KAZ explicitly before calling update_aral_sea |
| on_monthly_KAZ | KAZ-specific monthly hook | Call aral_monthly_tick directly; do not add original_tag or a second country gate |
| Decision available | Decision country's scope (KAZ for this category) | Require controls_state = 717; focus prerequisites also belong here |
| 717 = { ... } / other numeric state targets | The selected state | Use state-scope checks and variables; do not assume the country variable is the state's variable |
| aral_state_update | State scope after the numeric state target transition | Only refresh while the state is owned by KAZ; read KAZ.aral_deficit explicitly and store modifier input variables on the state |
| country_event | Event recipient is the event's country scope | Trace the effect that fired it to determine FROM |
| aral_sea.4 | Russia receives the request through SOV = { country_event = ... } | The sending KAZ scope becomes FROM in the Russia event; the study option marks KAZ through FROM |

### Scope rules that matter here

- ROOT, FROM, PREV and THIS are contextual scope references, not universal aliases. A scope transition changes the current object; draw the transition chain before deciding which country's or state's variables a command reads.
- The on_monthly hook is evaluated for countries generally. An on_monthly_TAG hook is scoped to the named tag and avoids running the same KAZ logic once per country. The active mechanic uses on_monthly_KAZ.
- The on_startup hook has no country ROOT scope. Explicitly entering KAZ is intentional, not redundant.
- In a country_event, ROOT is the recipient. When an event is fired through an effect, the firing effect's ROOT becomes event FROM. This is why the Russia decision path must be traced from the SOV scope to event option a.
- controls_state = 717 asks whether KAZ controls Kyzylorda. owns_state = 717 asks about legal ownership from country scope; is_owned_by = KAZ is the state-scope ownership check. They answer different questions.


## Decision visibility: do not duplicate one-shot behaviour

For ordinary country decisions, \`fire_only_once = yes\` is the engine-level one-use rule. A \`visible\` condition that checks only \`NOT = { has_country_flag = <decision>_done }\` repeats the same restriction and should be removed. Keep the completion flag itself when another project, event or hydrology effect reads it; remove the flag entirely only when it has no other consumer.

Meaningful visibility restrictions stay:
- \`aral_dike\`: hide the temporary dike after the permanent Kokaral dam is completed.
- \`aral_sib_canal\` and \`aral_sib_pipe\`: show the mutually exclusive supply choices only after Russia's study result approves the project.
- \`aral_regional_response\`: show the recovery action only while the regional crisis is active.
- \`aral_sibaral\`: it is repeatable with a cooldown, so terminal outcomes and an approved study can hide further requests.

Do not remove these conditions merely because another decision uses \`fire_only_once\`; they encode separate state/availability rules.

## Mechanic contracts

### Decisions and project timers

- The decision category is restricted to KAZ. Every Aral project decision keeps the coast requirement in available as plain controls_state = 717.
- Focus gates stay in available so locked decisions remain visible with a reason tooltip. They are not moved into visible.
- Losing state 717 after a decision has started must not cancel the active timer. Do not add ownership-based cancel_trigger / cancel_effect logic.
- The project timer's normal finish path is preserved. The start-side payment and finish-side project reward must not be accidentally moved between complete_effect and remove_effect.

### Hydrology and state modifiers

- The monthly tick runs only for KAZ and contains the separate legal-ownership guard for state 717. While KAZ does not own the coast, hydrology and recalculation pause.
- update_aral_sea also guards its recalculation with owns_state = 717. This protects direct calls from project/event effects.
- The six state modifiers are stored on their states. aral_state_update enters each target state, checks is_owned_by = KAZ, copies the KAZ deficit into state variables, then adds/refreshes the state dynamic modifier.
- Do not remove aral_state_modifier on ownership change. If the state changes hands, its last calculated modifier values are meant to stay there. Recalculation resumes when KAZ owns the coast and the relevant state again passes its ownership check.
- Set state variables before attaching the dynamic modifier; call force_update_dynamic_modifier = yes after the assignments so the changed values are refreshed immediately.

### GUI water-level representation

- The satellite picture strip has seven frames: frames 1-3 represent levels below the natural 40 m baseline, frame 4 is the baseline, and frames 5-7 represent recovery above it.
- Keep the negative restoration thresholds mapped to frames 3, 2 and 1 at -0.01, -10.01 and -20.01 respectively; the more negative checks must follow the broader negative check so they override it.
- Keep the positive thresholds mapped to frames 5, 6 and 7 at 9.99, 34.99 and 54.99. The current restoration range extends down to -30, so frames 1-3 must remain reachable; test the mapping alongside the bar's negative segments.

### Treasury and costs

- Native cost = N is the Political Power requirement for a decision.
- custom_cost_text = cost_X_Y points to the shared TDF treasury price label. It is display information; the cash operation is the scripted treasury effect.
- Do not add a second `custom_effect_tooltip` with an `aral_*_cost_tt` key: it repeats the treasury amount; native `cost = N` displays Political Power separately.
- Charge the full cash amount once with a negative treasury_change followed by modify_treasury_effect = yes. TDF's treasury system handles a negative balance through its debt mechanism.
- Do not add a positive-balance treasury gate or a second debt_change / modify_debt_effect transaction. Do not add an empty custom_cost_trigger = { always = yes } placeholder.
- The annual Siberian fee is stored as a negative aral_sib_fee and applied through the monthly KAZ tick's annual branch. English and Russian labels must show the same absolute amount as that variable.

### Trigger/effect separation

A trigger checks state; an effect changes it. Verify every command against the current context:
- available, event trigger and if.limit contain trigger logic.
- complete_effect, remove_effect, event immediate and event options contain effect logic.
- A parser finding balanced braces does not establish that a trigger is valid in a given effect scope, or that an effect is valid in a trigger block.

## Static validation now covered

The CI audit checks:
- KAZ startup and tag-specific monthly hook shape;
- the decision coast-control and focus gates;
- state ownership and state-scoped modifier assignment order;
- persistent-variable initialization;
- treasury-only cash charges and generic price-key matching;
- localised annual Siberian fees against the actual negative fee variables;
- references to Aral country events and the SOV-to-KAZ FROM handoff;
- regional-warning escalation and recovery;
- localisation key parity, event text keys and existing decision invariants.

The test suite and simulator provide additional checks for project costs, project timing and hydrology scenarios. These are source/model checks, not a complete HOI4 runtime test.

## Required in-game verification

Before treating a release as game-verified, test in the target TDF build:

1. Start a new game as KAZ. Confirm startup variables initialise and the Aral category opens.
2. Confirm project decisions remain visible but blocked by incomplete focus or missing control of state 717.
3. Start a project, transfer state 717 away during its timer, and verify the timer still finishes normally.
4. While KAZ does not legally own 717, verify monthly hydrology/recalculation pauses and the state modifiers retain their last values.
5. Return state 717 to KAZ and verify hydrology and recalculation resume without resetting aral_sea_restoration or aral_pending.
6. Trigger the Siberian-water request. Verify Russia receives the event and the KAZ sender flag is set by the event's FROM scope.
7. Check both English and Russian tooltips for the exact yearly canal/pipeline fees; verify treasury changes in the log.
8. Inspect error.log and the decision GUI for missing script tokens, sprite references, or interface errors.

## References

The linked engine references are community-maintained HOI4 wiki mirrors; use them to understand documented patterns, then verify the exact target build.

- [MDC scopes](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/getting-started/scopes.md)
- [MDC triggers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/getting-started/triggers.md) and [basic HOI4 triggers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/triggers/basic.md)
- [MDC economy effects](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/effects/economy.md)
- [MDC regional modifiers](https://github.com/minusleto/MDC/blob/main/src/content/docs/code-resource/modifiers/regional.md)
- [HOI4 on_actions reference](https://github.com/thelight0211/hoi4-wiki/blob/main/On%20actions%20-%20Hearts%20of%20Iron%204%20Wiki.md)
- [HOI4 event modding reference](https://github.com/cpntodd/HOI4-MCP/blob/main/paradox_wiki/Event%20modding%20-%20Hearts%20of%20Iron%204%20Wiki.md)
- [HOI4 decision modding reference](https://github.com/thelight0211/hoi4-wiki/blob/main/Decision%20modding%20-%20Hearts%20of%20Iron%204%20Wiki.md)
- [HOI4 modifiers reference](https://github.com/klimPaskov/Agentic-HOI4-Modding/blob/main/hoi4_wiki/modifiers.md)
- [HOI4 triggers and scope reference](https://github.com/kkkunny/hoi4-mod-skills/blob/master/skills/hoi4-mod/references/Triggers.md)
