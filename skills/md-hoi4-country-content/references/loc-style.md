# Localisation style (recommendations)
## Formats
- yml: UTF-8 with BOM, one leading space, ` key: "text"`, no version number, \" for quotes, \n newline. No duplicate keys. Keys: focus `<id>`, `<id>_desc`; events `<ns>.<n>.t/.d/.a/.b`; idea `<id>`, `<id>_desc`; tooltips `<thing>_tt`; scripted loc `X_loc` with keys `X_loc1..`.
- Use `$modifier$` variables in spirit tooltips instead of hardcoded English (easier translation); fall back to MODIFIER_UPPERCASE form if a key shows raw. Unverified keys: test in game.
- Russian loc breaks `[X.GetAdjective]` and tokens after prepositions/possessives. Use tokens only as nominative sentence subjects; otherwise reword. No hardcoded capital name (it can change).
## Focus description (target 200-280 chars, 2-3 sentences)
1. Real problem or fact (named company, unit, place, number; no year unless a timeless past fact). 2. "We will ..." intent (what THIS focus does). 3. Short consequence, dry irony only if the fact itself is ironic.
- Must match the code (if text says radar, code gives radar; if text says portable AA, the tech categories include it).
- Do not name equipment/projects delivered by later focuses. Neighbouring descs must not open the same way.
- Titles: 2-4 words, <=30 chars; verb+object ("Sign the licence") or the name of the thing ("Zenit Shipyard"). Replace cryptic/anachronistic names (e.g. a company name that only exists since later years).
## Events
- Description 150-380 chars, starts with the sender/situation; "\n\n" only for major events. Proposal text is from the recipient's point of view. Titles unique. Option labels unique, <=35 chars, action-like ("Sign the licence", "Fire the first round").
## Banned / avoid
"strengthen ties", "mutual benefit", "significant", "foothold", "valuable", "comprehensive", "ensuring", "key", "foster", "paving the way"; labels like "Interesting", "Great", "Damn", "Nice", "Decline the proposal", "Excellent!". Encyclopedia-only descs with no intent. Invented jokes; shouting.
## What reference countries taught
- Portugal: good for equipment purchases (what, why better, how acquired: licence/surplus/local manufacturer). Weak: encyclopedia lines for institutions, slogan-heavy ideology branches.
- Syria: good flavour chain with scene, 2nd person, quoted dialogue, unique subtitles; weak generic news options.
- Russia: useful code patterns, weak army loc (median 126 chars).
- Poland: caution - median 170 chars, 5% first person, templated openers, filler (ties 62, strengthen 26).
