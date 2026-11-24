# Portrait guide

Portraits are **SVG ink sketches**, saved as `characters/<slug>.svg`, which the orchestrator converts with `rsvg-convert` and frames on the character's page.

- Root element: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">`.
- Style: an engraving or field-sketch of the character: head and shoulders or three-quarter figure, in pen strokes and hatching, with iron-gall ink `#2b1b0e` and occasional faded red `#7e1f14` or wash colours at low opacity. The background is transparent or a soft vignette. Composition, posture, clothing, scars, tools and props should come from the character sheet and say who they are.
- Use only SVG shapes and paths: `path`, `ellipse`, `circle`, `line`, `polyline`, `polygon`, `rect`, `g`, `defs`, `linearGradient`, `radialGradient`, `pattern` and `clipPath`, plus simple `filter`s (feTurbulence and feDisplacementMap for a rough ink edge are fine).
- Do not use external references, `<image>`, `<foreignObject>`, `<script>` or fonts. A small text caption is allowed only with a generic `font-family="serif"`.
- Keep the file under 300 KB. Draw with many strokes, giving faces character through lines, shadows and hatching; avoid flat cartoon shapes.
