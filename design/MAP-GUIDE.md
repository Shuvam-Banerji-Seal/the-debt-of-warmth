# Map-making guide

Maps are hand-made by you as **self-contained HTML/CSS/JavaScript** pages. The orchestrator screenshots them with headless Chromium and binds them into the Atlas. Each map lives in `atlas/<slug>/`:

- `map.html` contains the map, with all code inline.
- `meta.json` holds `{"title": "...", "caption": "...", "width": 2400, "height": 1600, "kind": "world|region|city|dungeon|battle|other"}`. Use width 2400 × height 1600 for landscape maps, or 1600 × 2200 for portrait ones.

## Technical rules
1. **No network.** Do not use CDNs, web fonts from the internet or remote images. You may use local fonts with relative paths: `@font-face { font-family: Fell; src: url('../../fonts/IMFeENrm28P.otf'); }`. Also available are `IMFeENit28P.otf` (italic), `IMFeENsc28P.otf` (small caps), `Cinzel-Regular.ttf`, `CinzelDecorative-Bold.ttf` and `EBGaramond-Regular.otf`. The paper texture is at `../../design/textures/parchment.jpg`.
2. Fix the page at exactly the size in `meta.json`: `html,body{margin:0;width:2400px;height:1600px;overflow:hidden}`. Draw into one full-size `<svg>` or `<canvas>`.
3. **Deterministic.** If you use randomness, write a seeded PRNG (for example mulberry32) so that every render is identical.
4. Drawing must finish within about 5 seconds. Avoid unbounded loops and noise at every pixel of a 2400×1600 canvas in pure JavaScript, unless you use a coarse grid.
5. Wait for fonts before drawing text on a canvas: `document.fonts.ready.then(draw)`. SVG `<text>` is fine.
6. Use no external libraries. Write everything yourself.
7. **Layer order.** Paint in this order: ground and washes, then terrain, then water, then roads and buildings, then frames (cartouche, legend, scale), and **all text last, on top of everything**. Text drawn beneath an opaque cartouche or legend box disappears. A map with an empty legend or an invisible title is broken.

## Look and feel: rustic, hand-inked, old
- Parchment ground (the texture image or a CSS gradient), with sepia and iron-gall ink (`#2b1b0e`), faded red (`#7e1f14`), muted sea blue-green and soft washed colours for regions.
- Coastlines and rivers drawn as jittered, hand-drawn lines; coastal hatching or ripple lines along shores. Rivers taper from source to mouth.
- Mountains as little inked peaks with shaded flanks, hills as small bumps, forests as clusters of tiny tree glyphs, marsh as tufts and reeds, roads as dotted or dashed lines.
- Settlements by importance: capital, city, town, village, ruin, fortress, temple. Explain them in a legend.
- A compass rose, a scale bar in the world's own units, a decorative title cartouche, and optionally sea creatures, wind faces or marginal notes in the cartographer's voice.
- Labels in the Fell or Cinzel fonts, with curved or spaced lettering for regions and seas. **Every named place on the map must exist in `memory/places.md` or the bible.** Keep the map consistent with canon (distances, directions, borders).
- Show what the world's own map-makers would know. Unknown lands can be blank, misdrawn or annotated with rumour.
- **Natural geometry.** Coastlines, lakes, borders and rivers must be irregular, fractal and hand-drawn: build them from many jittered points (midpoint displacement or seeded noise), with bays, headlands, spits and islands. Never use rectangles, rounded rectangles, perfect ellipses or straight-ruled coasts for land or water.
- **Keep labels clear.** Labels must not cross roads, rivers or other labels. Place them deliberately: spaced capitals for regions, small italics for features, and a pale halo behind text where needed.
- **No cartoons or emoji.** Decorations should be engraving-like: sea beasts, wind-heads, ships and cartouches drawn in fine line and hatching, the way an old engraver would cut them.

## Validation
The orchestrator renders the page. If the result is blank or the script throws an error, you will be given the error and asked to fix it.
