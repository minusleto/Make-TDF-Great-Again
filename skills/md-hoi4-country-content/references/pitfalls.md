# Pitfalls, audit checklist, process lessons
## Bug patterns found in real files
log id != focus id; copy-paste from another country (hungary_economy.4, HUN_ ideas, hungary_* opinion modifiers); focus requires itself in available; effect only inside effect_tooltip; swap_ideas whose remove_idea is already gone; same bonus in proposal AND reply (and in the focus); stock/variant created in both focus and reply; foreign event namespace; MiG-style placeholder pictures; event id case mismatch (KAZ_army.4 vs kaz_army.4); undefined scripted loc referenced from a tooltip; hidden idea never displayed; tooltip numbers != code (promised 40, gave 18); partner that does not exist in reality (Iran/China aircraft), direction reversed (Russia taking aircraft instead of giving); duplicate loc keys; missing _desc; mixed tabs/spaces; unguarded DLC effects; naval proposal sent to wrong tag.
## Audit checklist (run mechanically)
brace balance; tabs; unique loc keys and list of keys to delete when replacing; every event has .t .d and option keys; every option has log; prerequisites exist; ideas used exist; scripted loc keys exist; log == id; length ranges; no forbidden tokens.
## Process lessons
- Verify facts with sources; separate "sourced" from "player intent"; correct earlier mistakes openly (e.g. districts were created in 2000 and became regional commands in 2003).
- Do not rely on memory for syntax; mark unverified items (#TODO) and list them.
- If a wiki/site blocks fetching, say so and ask for the line; do not guess.
- One question per message, only when blocking. Short replies; bulk in files.
## User decisions (examples, adapt per user)
No years in descriptions; real facts first; events only for real choices (flavour decrees allowed); jeeps are util vehicles; founding focuses (company creation) have no partner proposal; tooltip keys may be skipped if the user says they are redundant.
## Unverified in the source project
mio: effect syntax; add_mio_research_bonus; has_mio_size; crypto_strength value; mastery bonus parameters; increase_conscription_effect; tags SPR/SAF; icon/GFX names for event pictures.
