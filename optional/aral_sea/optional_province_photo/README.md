# Optional: live sea photo in the state / province view (not active until you finish these steps)

MDC shows a 413x70 "terrain photo" in the state view when the province carries a matching empty static modifier.
This package swaps four photos (dry / shrinking / start / restored) as the sea changes.

1. Copy `gfx/interface/terrain/aral_sea_1..4.dds`, `interface/aral_sea_terrain.gfx` and `common/modifiers/aral_sea_terrain_modifiers.txt` into your mod.
2. Paste the four icons from `countrystateview_ICONS_SNIPPET.txt` into your `countrystateview.gui`.
3. Find the Aralsk province id (Tdebug) and replace `PROVINCE_ID` in `aral_update_photo_BODY.txt`.
4. In `common/scripted_effects/aral_sea_effects.txt` replace the empty `aral_update_photo = { }` with that block.
5. Test: open the province, then use the debug decisions to change the sea; the photo must change at frame 3, 4 and 6.

Notes: the photos are 32-bit (4 x 115 KB). If size matters, tell me and I will convert them to compressed DDS.
Unverified: the exact syntax of `remove_province_modifier` in your version (it mirrors the `add_province_modifier` form MDC uses).
