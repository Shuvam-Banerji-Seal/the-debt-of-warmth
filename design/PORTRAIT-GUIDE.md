# Portrait guide: cameo plates

Each character's portrait is a **cameo plate**: a profile silhouette in an oval medallion, in the manner of old cut-paper silhouette portraits, framed like an engraved book plate and set above an emblem of the things that define the person. Save it as `characters/<slug>.svg`. The orchestrator converts it with `rsvg-convert` and frames it on the character's page.

## Canvas and materials
- Root element: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">`.
- Palette: ink `#2b1b0e`, paper `#efe2c4`, faded red `#7e1f14`, ochre or gold `#9a7432`, slate `#4a5560`. Washes at low opacity are fine.
- Use only `path`, `ellipse`, `circle`, `line`, `polyline`, `polygon`, `rect`, `g`, `defs`, gradients, `pattern` and `clipPath`. Do not use `<image>`, `<foreignObject>`, `<script>`, external references or fonts, except an optional tiny caption with `font-family="serif"`. Keep the file under 200 KB.

## Composition
1. **Medallion** (upper two-thirds, centred near (300, 330), about 400 wide and 480 tall): an oval in paper colour, with a double ruled border in ink and gold and a fine bead or rope pattern between the rings. Optionally a ribbon or ornament at the top.
2. **Silhouette** inside the oval: the head and shoulders **in strict profile**, facing left or right, as **one solid ink-filled path**, plus optional thin paper-coloured lines cut into it for an eye glint, an earring or a collar edge. The profile is the portrait, so build it point by point with real anatomy:
   - the back of the skull and the crown, with hair as masses, braids, a topknot, cropped, wild, bald or hooded as the sheet says;
   - the forehead's slope, the brow ridge, and the dip at the bridge of the nose;
   - **the nose's exact shape** (straight, hooked, broken, snub, long) and the nostril;
   - the upper lip, the line of the mouth, the lower lip, the chin (strong, receding, bearded), then the jaw back to the ear;
   - the throat (with an Adam's apple for a grown man) down to the collar;
   - the neck's back line, and shoulders sloping into clothing whose edge says something (a hood, a fur collar, a work smock, armour, a priest's band).
   Age, build and temperament must show in the profile alone: a child's rounded brow and small nose, an old man's sunken mouth, a soldier's thick neck. Use smooth cubic Béziers (`C`) with 30 to 80 points, never zig-zags.
3. **Emblem** (lower third): two to four objects that belong to the character (tools, weapons, a broken thing, a sigil, a plant, an animal), drawn in clean ink line with light hatching and arranged symmetrically or crossed like heraldry, on or above a ribbon scroll.
4. **Finish**: a thin outer frame around the whole plate, small corner ornaments, and a soft vignette behind the medallion.

The plate must read instantly as *that* person, through the shape of the profile and the objects alone. Reread the character's Appearance and History before drawing.
