# Chapter decoration guide

Each chapter opens with a headpiece that **you design**: `book/chapters/ch-NNNN/decoration.tex`. It sits above the words "CHAPTER N" and is scaled to fit a slot about **10.5 cm wide and 3.6 cm tall**, so draw on a canvas of roughly that shape (wider than tall).

## Rules
- The file contains exactly **one** `tikzpicture` environment and nothing else. No preamble, no `\usetikzlibrary`, no `\def` or `\newcommand` outside the picture (`\pgfmathsetmacro` and `\foreach` inside it are fine), no external images, and no `\input`.
- Express the chapter's heart as an emblem rather than an illustration of the plot: a motif, object, beast, weather, sigil or wound. Vary the composition from chapter to chapter. Avoid a row of the same ornament every time.
- A short motto is allowed: `\node[font=\FellFont\itshape\small, text=faded] {...};` or `\node[font=\CinzelFont\scriptsize, text=rubric] {...};`.
- Keep it fast. Fewer than about 400 path segments, and a `\foreach` with no more than about 200 iterations.

## Colours (already defined)
`ink` (dark sepia text), `rubric` (manuscript red), `gold`, `ornament` (gold-brown), `faded` (soft brown), `blood`, `moss`, `night` (deep blue-black), `ash` (grey), `vellum` (paper). Mixes such as `rubric!60!ink` and `gold!40` work.

## TikZ libraries (already loaded)
calc, shapes, shapes.geometric, shapes.symbols, decorations.pathmorphing (random steps, snake, coil), decorations.pathreplacing, decorations.markings, decorations.text, patterns, fadings, shadows, arrows.meta, positioning, intersections, backgrounds.

## Vector ornaments (pgfornament)
`\pgfornament[width=2cm, color=ornament]{N}` draws engraved Victorian ornament number N. You can place them inside nodes: `\node at (0,0) {\pgfornament[width=3cm,color=ornament,symmetry=v]{80}};`. The `symmetry` option takes `v` (mirror left-right), `h` (mirror top-bottom) or `c` (both).

Useful numbers:
- **Fleurons and flowers:** 1, 2, 3, 6 (fleur-de-lis), 8 (rose), 9, 10, 11 (small fleuron), 12 (star-flower), 14, 15, 16, 17, 18, 20, 21, 23, 25, 27, 28, 29, 30
- **Corners:** 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 53, 54, 61, 62, 63, 64, 131, 132, 194, 195
- **Headpieces and vignettes:** 43, 44, 45, 46, 52, 55, 56, 57, 58, 59, 60, 65, 66, 68, 69, 70
- **Rules and flourished lines:** 71, 72, 73, 74, 75, 76, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 96, 97, 98, 99, 101
- **Leaves and holly:** 77, 78, 79, 94 (wheat), 188, 189
- **Creatures and objects:** 90 (cockerel), 91 (cow), 95 (eye), 104 (goat), 106 (crossed fish), 108 (hound), 110 (fox), 113 (dove), 117 (wreath), 122 (butterfly), 123 (owl), 126 (clock), 127, 128 (ships), 136, 137 (winged emblems), 147 (crown), 156 (ram), 158 (lion), 159 (crab), 161 (bull), 163 (scales), 190 (bird), 196 (winged rosette)

Do not use 124, 125, 134, 142, 143–146 or 191.

## Example (do not copy it; make your own)
```latex
\begin{tikzpicture}
  \fill[night!85] (0,0) circle (0.9);
  \foreach \a in {0,30,...,330} \draw[gold, line width=0.6pt] (\a:1.0) -- (\a:1.35);
  \node at (0,0) {\pgfornament[width=1.1cm,color=vellum]{95}};
  \node at (-3.3,0) {\pgfornament[width=4cm,color=ornament]{80}};
  \node at ( 3.3,0) {\pgfornament[width=4cm,color=ornament,symmetry=v]{80}};
  \node[font=\FellFont\itshape\scriptsize, text=faded] at (0,-1.6) {what the river keeps};
\end{tikzpicture}
```
