# Portrait guide

Portraits are **SVG engravings**, saved as `characters/<slug>.svg`. The orchestrator converts them with `rsvg-convert` and frames them on the character's page. They should look like a plate from an old illustrated book: a fine-line engraving with expressive contour and disciplined hatching. They must never look like a mannequin or a cartoon.

## Canvas and materials
- Root element: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">`.
- Ink `#2b1b0e` for lines. Optional washes at low opacity (0.08–0.25): faded red `#7e1f14`, ochre `#9a7432`, slate `#4a5560`. A soft oval vignette behind the figure, fading to transparent.
- Use only `path`, `ellipse`, `circle`, `line`, `polyline`, `polygon`, `rect`, `g`, `defs`, gradients, `pattern`, `clipPath` and simple filters (feTurbulence plus feDisplacementMap for a slightly rough ink edge). Do not use `<image>`, `<foreignObject>`, `<script>`, external references or fonts. Keep the file under 300 KB.

## Construction (do it in this order)
1. **Pose.** A head-and-shoulders or half-length figure in **three-quarter view**, turned slightly; never dead-front, and never a symmetrical bell-shaped body. The head is about one-seventh of the visible height in a half-length, larger in a bust. The eyes sit halfway down the head. The shoulders are about three heads wide for a man and slope down from the neck (trapezius), so they are never a dome. The neck has width and tendons.
2. **Silhouette.** Before any detail, block the figure's outline with confident curved paths: the skull, jaw, ear, the neck's two lines, the shoulder slopes, and the arms with elbows bent. Clothing hangs from the shoulders and folds at the elbows and waist.
3. **Face.** Draw it as structure, not symbols: brow ridge, eye sockets with lids (upper lid heavier), the nose built from bridge, tip and wings with a shadow on one side, the philtrum, a mouth with a darker line between the lips, cheekbones and the jaw's turn. Age shows in nasolabial folds, crow's feet and loose skin under the jaw. Hair is drawn as locks and masses following the skull, not as a cap.
4. **Light.** Choose one light source (upper left). Shade the far side of the face, under the brow, under the nose, under the jaw, and in the clothing's folds with **hatching that follows the form** (curved strokes around cylinders, cross-hatching only in the deepest shadow). The lit side stays almost bare. Do not fill the whole body with uniform parallel lines.
5. **Hands and character.** Show one hand if the pose allows, with knuckles, fingers in a natural curl and a thumb. Add one or two objects or marks that say who they are (a tool, a scar, a ring, a wound, a badge), placed where the eye will find them.
6. **Finish.** Use line weight to separate near from far (thicker contours toward the viewer, thin lines inside), add a few loose strokes of background hatching behind the shadow side, and sign a tiny monogram in a corner if you like.

Spend real effort: a good portrait uses hundreds of purposeful paths. Reread the character's Appearance section and make the portrait unmistakably that person: age, build, posture, scars, what they wear and how they carry it.
