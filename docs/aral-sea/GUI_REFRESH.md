# Aral Sea GUI refresh

This is a visual-only refresh of the Aral Sea decision-category panel, based on the dark
technical panels and restrained blue edge lighting in the supplied Eastern Conflict reference.

- Added a dark outer plate, compact header plate and separate progress/status plate.
- Restyled the existing picture frame, progress track, positive/pending/negative segments,
  milestone markers and footer banner.
- Kept all original GUI element identifiers, all positions, the 50-segment layout,
  scripted visibility triggers and the `aral_pic_frame` scripted property unchanged.
- No variables, scripted triggers/effects, decisions, events or localisation were changed.

Exact pre-refresh copies of `aral_sea.gui` and `aral_sea.gfx` are in
`backups/aral_sea_gui_v1/`. They are stored under `docs/`, outside the active
`mdredux/interface/` loading path.

Validation is static. The game UI itself still needs an in-game visual check at the target UI scale.
