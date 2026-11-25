---
status: historical-engineering-review
updated: 2026-11-25
scope: "Selected high-churn Kazakhstan changes in Make-TDF-Great-Again from the first tracked KAZ content (2026-10-28) through 2026-11-24."
limits: "Commit subjects and diffs document what changed; they do not always document why. Unknown motives are labelled as unknown. This is not a runtime verification or a claim that all historical choices remain current."
---

# Kazakhstan: lessons from repeated historical edits

## 1. Scope and reading method

Reviewed the tracked history of the KAZ focus tree, events/Kazakhstan.txt, Kazakhstan_ideas.txt, KAZ MIO definitions, scripted effects/localisation and the English KAZ focus localisation. The oldest KAZ content in the current repository history begins with file additions on **2026-10-28**; the selected high-churn clusters run through **2026-11-24**.

This is a retrospective of selected clusters where code was repeatedly revised, renamed, moved or reverted. Commit subjects and diffs are used as evidence. Where a commit says only “fix” or “revert” and does not explain the design reason, this report does not invent one. Some technical decisions were made against a particular MD/DLC snapshot; re-check the current target build before reusing them.

No game-content files were changed as part of this review.

## 2. Repeated patterns that caused rework

### 2.1. Equipment deals: identify the equipment class before choosing the implementation

The Arlan/Alan/Barys work is the clearest example of how a plausible-looking reward can be built on the wrong equipment path.

**Arlan and Alan**
- [6ba2a852](https://github.com/minusleto/Make-TDF-Great-Again/commit/6ba2a85252ca6f0948b8ca1b290da1bf630ae907) initially implemented Arlan as util_vehicle_4: SAF had to possess the technology, 100 vehicles were transferred, Kazakhstan paid 4 treasury and SAF received 4.
- [0ad3fffc](https://github.com/minusleto/Make-TDF-Great-Again/commit/0ad3fffc475e20bd76d85114ba8239e68b770679) implemented Alan around util_vehicle_5, with ISR technology gate and 100 vehicles; Alan-2 used util_vehicle_6 and 50 vehicles.
- [365a50e3](https://github.com/minusleto/Make-TDF-Great-Again/commit/365a50e38084f6ce2805f32b91f64f3e92c728d3) later changed Arlan to util_vehicle_5 and explicitly tied it to the equipment name/localisation, while Alan-2 used util_vehicle_6.
- [8a2719ee](https://github.com/minusleto/Make-TDF-Great-Again/commit/8a2719eeda21bd1c96802e0c8b831cb8c6dc389b) removed a three-way Alan role choice implemented with country flags and made the chain a single SandCat licensing path. Its subject and diff identify the approved premise as licensing the real SandCat for Kazakh use, not an independently evidenced three-role prototype programme.

**Barys 6x6 / 8x8**
- [210cbed5](https://github.com/minusleto/Make-TDF-Great-Again/commit/210cbed5229e7d61810bd9817b79a53afac35f16) moved Barys variant creation into SAF reply events and gated on APC_6 / IFV_6 at SAF.
- [b8e72149](https://github.com/minusleto/Make-TDF-Great-Again/commit/b8e72149fc0efc5b3bd89972aa152ebd9eb0b78f) changed the route: use design_team = mio:..., allow_without_tech = yes, and research bonuses for CAT_apc / CAT_ifv; remove the direct set_technology = APC_6/IFV_6 reward and partner technology gate.
- [14863a8f](https://github.com/minusleto/Make-TDF-Great-Again/commit/14863a8ff221cd9685e4ea8e84505757b909e7ad) then added chassis unlock checks using mbt_tech_1/2 on both Kazakhstan and SAF.
- [ccbd1e11](https://github.com/minusleto/Make-TDF-Great-Again/commit/ccbd1e11d071222842088cd51b46b3244af88486) changed those checks to an OR: the required chassis unlock could be present in Kazakhstan **or** in the partner. The current KAZ Barys focus still expresses that OR pattern for mbt_tech_1.

**Safeguard:** first identify the actual equipment type/chassis and inspect the target version's technology unlock. Do not choose the implementation from the product name (“APC”, “IFV”, “armoured car”) alone.

- For util_vehicle_N, verify the exact equipment ID and matching tech, the partner's has_tech condition, producer, quantity and treasury/influence exchange.
- For medium_tank_* chassis variants, verify the chassis unlock path separately from the APC/IFV research category. If using the MIO variant route, check design_team, DLC guards, allow_without_tech, variant name, producer and the intended CAT_apc / CAT_ifv bonus. Do not grant technology merely because a category bonus exists.
- Write the gate as an explicit truth table: KAZ has chassis tech? Partner has chassis tech? Is either sufficient, or are both required? The Barys history shows this decision changed; do not silently pick one.
- Keep equipment type, display name, research category and icon aligned. A plausible-looking name or icon is not proof that the underlying equipment type matches.

### 2.2. Event chains: immediate, option scope and duplicate effects

Several revisions show that the event's current country and the country that should receive a deal reward must be traced carefully.

- [16b8785c](https://github.com/minusleto/Make-TDF-Great-Again/commit/16b8785ca3ed4cafe7a0f35b8c033db823de3661) moved technology, stockpile and treasury effects for kaz_army.37 from immediate into the accepting option. This is a concrete ordering/choice bug: immediate executes when the event fires, before a player chooses; an acceptance-only reward must not run unconditionally.
- [caa82ad7](https://github.com/minusleto/Make-TDF-Great-Again/commit/caa82ad74447ad2b66963c03f2bde9cad9f5b211) removed repeated temp_opinion = 2 / change_the_military_opinion blocks from a large set of Kazakhstan events. The commit labels those effects misplaced; its diff alone does not establish the intended recipient in every case.
- [af02fa39](https://github.com/minusleto/Make-TDF-Great-Again/commit/af02fa399d0b994f81711c624846d1332f800246) renumbered army events by branch and changed the corresponding callers across the KAZ focus tree in the same change.

**Safeguard:** before writing a diplomatic chain, draw the state machine:
KAZ focus → partner proposal event → accept OR decline → KAZ reply event.
For every command, write down its scope:
- who is the current event country (THIS);
- who sent the proposal (FROM);
- who receives the resource, equipment, influence or opinion change;
- which option is selected before the effect runs.

Then verify that every acceptance reward exists in exactly one real effect location. A tooltip preview is not a substitute for the real event option. A refusal must not run the acceptance branch's costs or equipment grants. When renumbering events, update and search all callers, namespace declarations, option keys and localisation; do not renumber by editing only the event definitions.

### 2.3. Narrative events should not disappear during a mechanical refactor

The airborne branch changed direction more than once:
- [51cfb70e](https://github.com/minusleto/Make-TDF-Great-Again/commit/51cfb70e443e70d6242f365d5fd31238b6155885) moved effects into the focus and removed the existing kaz_army.4 narrative event.
- [60089413](https://github.com/minusleto/Make-TDF-Great-Again/commit/60089413d25903d3c1757808556545a6555e70a8) restored a narrative event, added two airmobile brigades, and changed the spirit to paratrooper-specific modifiers. A later change routed the focus through the event again.

**Safeguard:** before deleting or bypassing an existing event, search all callers, replies and localisation and decide whether it is mechanical, narrative or both. Do not remove an established event merely to move code into a focus; preserve it unless the user explicitly asks to remove it or the design review records why it is obsolete.

The same caution appears in the Elbasy chain: [7f1947d9](https://github.com/minusleto/Make-TDF-Great-Again/commit/7f1947d9531acc577b825d398c841a9ef99ed6cc) removed the old KAZ_naz.5 call/event, while [15c0dcf7](https://github.com/minusleto/Make-TDF-Great-Again/commit/15c0dcf7e91c341b86ac1741f277693baba3fabc) added a separate KAZ_naz.7 event for the Elbasy focus. Treat event identity and narrative as part of the design, not disposable plumbing.

### 2.4. Ideas: visibility, helper spirits and IDs are separate decisions

The Alash/Nazarbayev history contains many quick edits on 2026-11-15:
- Alash spirit IDs were renamed in [3dded7ca](https://github.com/minusleto/Make-TDF-Great-Again/commit/3dded7ca2ae92bd36855675902f16ebc1692c2d5), [624c7da5](https://github.com/minusleto/Make-TDF-Great-Again/commit/624c7da546792c6649449bf3ce80b474801decbe), [3161ea06](https://github.com/minusleto/Make-TDF-Great-Again/commit/3161ea0647708d1def50423385fab2bed5d056e0) and [04c6dae5](https://github.com/minusleto/Make-TDF-Great-Again/commit/04c6dae5ed94e40a5d63529b5e70298ffa0d1d1e). Some follow-ups corrected suffixes or references again. This shows why automatic “append _idea” renames are unsafe.
- [bdf0d37d](https://github.com/minusleto/Make-TDF-Great-Again/commit/bdf0d37d44d9c10e5eb3e2aff9b417d4060f1b22) moved illustrated Alash spirits and the legacy hub into visible country ideas. Subsequent commits separated the visible legacy/hub spirits from modifier-only helpers.
- [32bd1949](https://github.com/minusleto/Make-TDF-Great-Again/commit/32bd19496ecd078c9a3ebe1f988f1e6a26a622f7) moved Nazarbayev spirit definitions out of hidden_ideas; [8276090e](https://github.com/minusleto/Make-TDF-Great-Again/commit/8276090e1b2e2a126489d90688b01e1ac6247103) then kept only tooltip-facing spirits visible and moved helper/test spirits back to hidden ideas.

**Safeguard:** for every idea, first classify it as (a) player-visible national spirit, (b) hidden modifier/helper component, or (c) staged replacement. Then choose country or hidden_ideas, name = base_idea, swap_ideas, cancellation conditions and tooltip/hub display. Rename IDs with an explicit old→new map and update every caller in the focus tree, events, scripted effects, scripted localisation and YML. Do not add suffixes by habit.

For defined_text hubs with multiple stages, inspect each trigger and ordering. More advanced stages must be matched before a broader/base-stage condition if the conditions overlap; verify the exact current KAZ pattern rather than relying on a memorised example.

### 2.5. MIO changes must follow focus IDs and DLC availability

- [a94ac0ad](https://github.com/minusleto/Make-TDF-Great-Again/commit/a94ac0ad70e920c42c7ff4307f7731f5b90f803a) corrected KPE MIO visible triggers from the old KAZ_create_kazakhstan_paramount_engineering focus ID to KAZ_create_kpe.
- [ab2c5a1b](https://github.com/minusleto/Make-TDF-Great-Again/commit/ab2c5a1b2c04a66a98027f6d80ad7fdebdf83d48) replaced the old Kazakhstan Engineering manufacturing4 definition with Aselsan electronics, moved MIO unlock/effects to KAZ_army_success and added corresponding localisation.
- AHKE's MIO moved through a generic helicopter template ([210f41c7](https://github.com/minusleto/Make-TDF-Great-Again/commit/210f41c76d9e3a40eec92cec27bf1ff7f68b22c2)), then a specialised helicopter template ([4240436a](https://github.com/minusleto/Make-TDF-Great-Again/commit/4240436aa241c541c850583cf368019a442623eb)), with ID changes ([72c78915](https://github.com/minusleto/Make-TDF-Great-Again/commit/72c789151b26f7e8210bd57982229f44ea589d1a), [f5897405](https://github.com/minusleto/Make-TDF-Great-Again/commit/f5897405bb8643421a0a7f782eb0811177ffe2fb)).

**Safeguard:** a MIO change is not complete after editing its definition. Verify the full tuple: MIO ID, allowed, visible focus, unlock caller, DLC guard, include specialization, design-team references, display-name localisation and any focus/event MIO effects. A focus rename must trigger a search of MIO visibility conditions too.

### 2.6. Historical research must constrain both text and rewards

- [8f837c6d](https://github.com/minusleto/Make-TDF-Great-Again/commit/8f837c6dc696c8c97b9a27ab8e99ae03e73e1765) rewrote the Chinese deal from an aircraft purchase to Wing Loong UAV cooperation: it removed the unsupported MiG-29 stockpile reward and used a drone research bonus instead. The same change removed an unsupported claim of local Skylark assembly.
- [8a2719ee](https://github.com/minusleto/Make-TDF-Great-Again/commit/8a2719eeda21bd1c96802e0c8b831cb8c6dc389b) aligned the Alan text with the SandCat licence premise instead of an unverified multi-role development choice.

**Safeguard:** do not derive an equipment reward from an old focus title, icon or description. Research the actual product/model, licence or service relationship, date, producer and quantity first. If facts support training or technology transfer but not a specific equipment delivery, do not invent a stockpile item.

### 2.7. Start ideas and file-format changes must be complete, not partial

- [73cd5ca0](https://github.com/minusleto/Make-TDF-Great-Again/commit/73cd5ca06c44a4a0203fabf3b9fa4dc6648474d6) added a set of proposed starting economic ideas; [f5316339](https://github.com/minusleto/Make-TDF-Great-Again/commit/f53163397314d233e70cffd8a6941a69f7ffd1f9) reverted their definitions as premature. The diff does not state the full design reason, so this is evidence to avoid treating a definition-only change as a completed start setup—not proof of the exact motive.
- [e1372be9](https://github.com/minusleto/Make-TDF-Great-Again/commit/e1372be9fb2416014546a91431145f6fdba134c4) explicitly preserved CRLF when editing KPE-related focus/event code.
- [8bfd03df](https://github.com/minusleto/Make-TDF-Great-Again/commit/8bfd03df8fb98daa0ba59def8c789706a3ba8f18) and [a0957bb4](https://github.com/minusleto/Make-TDF-Great-Again/commit/a0957bb46c34c98d15e32abdec0367742fe8648d) repeated the KAZ convention of placing treasury deductions last in a reward/event branch.

**Safeguard:** a starting profile is complete only when definitions, history grant, visibility, cancellation, tooltip and localisation are wired together and reviewed as one task. Preserve each file's current BOM and line endings; review diffs for accidental whole-file whitespace churn. Keep the established project ordering of treasury deductions unless the task deliberately changes it.

## 3. Reusable pre-edit checklist

Before implementing a substantial KAZ branch or procurement chain:

1. **Write the object map.** List focus IDs, event IDs, idea IDs/stages, MIO IDs, equipment IDs, technologies, localisation keys, scripted effects/localisation and state/flag/variable dependencies.
2. **Write the mechanics map.** For equipment, classify util_vehicle_N vs medium_tank_* or another class. For diplomacy, identify sender/recipient and each event scope. For spirits, classify visible/hidden/staged. For a branch, express prerequisites as AND/OR.
3. **Check the historical casebook.** Search this report for the same class of content before copying an older KAZ pattern. Confirm whether that earlier implementation was later changed or reverted.
4. **Make one coherent change set.** Change related files together; do not leave stale IDs or half-wired starting ideas. Preserve existing events/tooltips unless explicitly removed by design.
5. **Run the targeted KAZ checks.** Compare every new/changed ID across callers and definitions; inspect actual option effects, tech gates, MIO/DLC guards, localisation and EOL/BOM. Run the KAZ audit and unit tests; use the 12-country workflow when changing common rules.
6. **Review the diff as a user would.** Ensure no accidental changes to unrelated branches, no mass line-ending conversion, no duplicated rewards, no tooltip-only real effects and no unsupported historical claims.

## 4. What this review does not prove

- It does not establish that every historical implementation or later decision is correct in the current HOI4/MD/DLC build.
- It does not resolve all external technology, equipment, MIO or modifier definitions; those must still be checked against the target base mod and DLC.
- It does not prove runtime behavior, UI rendering, AI choice or balance. Static code and commit history are evidence of the repository's design evolution, not an in-game test.
