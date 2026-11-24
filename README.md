# The Debt of Warmth

*A surgeon's account of Sarn.* A reincarnation isekai written chapter by chapter, without end, by the free model **`hy4-flash-free`** (OpenCode Go), and typeset as decorated LaTeX books. Daniel Marchetti, a Chicago trauma surgeon, dies saving a child from a burning car in a blizzard and wakes as an infant in Sarn. There, magic is a world energy called the Warm, every being is a vessel that holds it, and the dead are collected, taxed and poured back into newborns by an institution that keeps the world alive. He studies it the only way he knows: as a surgeon.

## Who made what
- **The author: `hy4-flash-free`** (OpenCode Go, free tier) writes **every word of the story**. It also invents the world, its history, magic and peoples, the past life and the whole cast with their character sheets, and plans the arcs, threads and twists. It draws the hand-made HTML/JS maps and the cameo portrait plates, writes the Codex of in-world documents, designs the TikZ headpiece above each chapter, and built the **website** and its online e-reader.
- **The orchestrator: Claude** (Anthropic) **writes no word of the story.** It built the press (`forge/`), which hands the author one task at a time, checks and repairs the results, guarantees that every day of the hero's life is on the page, and typesets, commits and publishes. It also designed the book (`design/`: parchment, gilt borders, chapter openers, indices, the leather-and-gold cover), the EPUB builder and the site's data export, and **wrote the prompts for the illustrations**. It steers only through instructions and validation.
- **The illustrations: OpenAI GPT Image** (`gpt-image-2.5-sunburst`) painted the light-novel **character pictures** (full-figure character sketches with transparent backgrounds), the colour plate before each chapter, and the frontispiece. Every prompt was written by Claude from the author's own canon: appearance notes, scars, clothing, and what happens in each chapter. The prompts are in `art/prompts/` and the costs in `art/ledger.jsonl`. Character art is used as reference images for the scene plates, so faces stay consistent.

> **Content note.** This is dark fiction for adult readers. It may contain violence, gore, slavery, cruelty and other darkness of its invented world.

## Where to read it
| What | Where |
|---|---|
| **The complete book, PDF**: every chapter so far, colour plates, the cast with art, the atlas, the Codex, the reckoning of days, three indices | **`The-Debt-of-Warmth.pdf`** at the root, rebuilt after every chapter |
| **The complete book, EPUB 3**: the same content for e-readers, with every day of the hero's life in the table of contents | **`The-Debt-of-Warmth.epub`** at the root |
| **Each chapter as its own PDF** | the `volume-NNN` releases (for example `volume-001` holds chapters 1–20) |
| The rolling complete book, the volume in progress and the cover | the `latest` release |
| Completed volumes (20 chapters each) | `pdf/vol-NNN.pdf` |
| **The website**: an online e-reader with EPUB and PDF downloads | GitHub Pages (`gh-pages` branch), rebuilt after every chapter |
| Progress | `STATUS.md` |

The root files are committed on every build while they are under 10 MB, then every (size in MB ÷ 5) chapters. GitHub refuses files over 100 MB, so beyond that the whole book continues in the `latest` release.

## Making illustrations
Run `python3 forge/illustrate.py`. It reads the prompt specs in `art/prompts/` and needs `OPENAI_API_KEY` in a git-ignored `.env`, which is never committed. The author model can neither read the key nor edit `art/`.

## How the repository is laid out
```
AGENTS.md                 the author's charter (OpenCode loads it automatically)
bible/                    world, history, peoples, calendar, magic, bestiary, factions, glossary, premise, voice
plan/                     the author's private roadmap: arcs, threads ledger, next chapters, wanted maps
memory/                   state of the world now, day-by-day timeline, story so far, gazetteer, digests
characters/               one sheet (.md) and ink portrait (.svg) per character
atlas/<slug>/             hand-made HTML maps, rendered to the Atlas
book/chapters/ch-NNNN/    meta.json, plan.md, scene-NN.tex, summary.md, decoration.tex, chapter.tex
codex/                    in-world documents (songs, laws, ledgers, letters), printed as the Codex of Sarn
art/                      light-novel illustrations (WebP) and the prompts that made them
book/volumes/             generated LaTeX masters, 20 chapters per volume, plus the compendium
design/                   book class, cover, textures, guides and templates for the author
forge/                    the orchestrator, build system, prompts
```

## Each chapter's cycle
1. **Plan:** `meta.json` (title, arc, epigraph, days, scenes) and a beat sheet. Days must follow on with no gaps.
2. **Scenes:** four to eight scene files of 2,200–4,500 words each. Each is sanitised, checked for length (and expanded if short), and proof-compiled; any LaTeX errors go back to the author to fix.
3. **Close:** the reader-facing chronicle and private continuity notes, the state of the world, one timeline line per day, character sheets and logs, the threads ledger, glossary, gazetteer and next steps.
4. **Decorate:** a TikZ headpiece designed for the chapter and proof-compiled.
5. **Publish:** commit and push. A background publisher re-typesets the complete book (and the current volume) without pausing the writing, then places it at the repository root and in the release. Every 10 chapters the author consolidates memory, draws a new map and adds portraits.

## Two workers
- **The press** (`storyforge`) writes chapters: plan, scenes, a check that every day is on the page, close and decorate.
- **The atelier** (`storyforge-atelier`) runs beside it and keeps the author busy on cameo portraits, new maps and the Codex.

## Running the press
```bash
systemctl --user status storyforge storyforge-atelier   # are they running?
journalctl --user -u storyforge -f      # watch it work
tail -f .forge/orchestrator.log         # same, from the repo
systemctl --user stop storyforge        # pause (it resumes exactly where it stopped)
systemctl --user start storyforge
python3 forge/orchestrator.py status    # progress.json
```
The model is set with `CHRONICLE_MODEL` (default `opencode-go/hy4-flash-free`). Per-call logs, including every prompt, are written to `.forge/logs/`.

## Building by hand
```bash
python3 forge/build.py maps             # render atlas/*/map.html with headless Chromium
python3 forge/build.py portraits        # characters/*.svg to PDF
python3 forge/build.py cover
python3 forge/build.py volume 1         # build/vol-001/vol-001.pdf
python3 forge/build.py complete         # build/complete/complete.pdf (the whole book)
python3 forge/build.py compendium
python3 forge/make_textures.py          # regenerate parchment and leather
```
This needs LuaLaTeX (TeX Live with pgfornament, tcolorbox, titlesec, imakeidx, lettrine, adjustbox and fmtcount), `rsvg-convert`, and Playwright's `chrome-headless-shell`. The fonts are bundled in `fonts/` under the SIL Open Font License.

## License
MIT (see `LICENSE`). The bundled fonts keep their SIL Open Font License.
