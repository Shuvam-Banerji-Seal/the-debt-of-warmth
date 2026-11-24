# An Endless Chronicle

A serial reincarnation saga written chapter by chapter, without end, by the free model **`hy4-flash-free`** (OpenCode Go), and typeset as decorated LaTeX books.

- **The author** (`hy4-flash-free` via `opencode run`) invents and writes everything in the story: the world bible, past life, cast and character sheets, arcs and twists, every scene, the chapter-end chronicles, the HTML/CSS/JS maps, the SVG portraits and the TikZ headpiece above each chapter.
- **The press** (`forge/`, built by Claude) writes no story. It hands the author one task at a time, validates and repairs the results, protects finished chapters, typesets the volumes, commits, pushes and publishes the PDFs, and resumes after any crash.
- **The design** (`design/`, by Claude) covers the 6×9in book class with parchment texture, gilt borders, chapter openers, drop capitals, chronicle boxes, character sheets, the atlas, three indices (persons, places, lore) and the leather-and-gold cover.

> **Content note.** This is dark fiction for adult readers. It may contain violence, gore, slavery, cruelty and other darkness of its invented world.

## Where to read it
| What | Where |
|---|---|
| **The complete book** (every chapter so far, the cast with portraits, the atlas, the lore, the reckoning of days and three indices) | **`The-Brass-Seam.pdf` at the root of this repository**, rebuilt after every chapter |
| The same, plus the volume in progress | the `latest` release |
| Completed volumes (20 chapters each) | `pdf/vol-NNN.pdf` |
| Progress | `STATUS.md` |

The root PDF is committed on every build while it is small, then every (size in MB ÷ 2) chapters as it grows, which keeps the git history manageable. GitHub refuses single files over 100 MB, so once the whole book passes about 95 MB it continues in the `latest` release (which allows files up to 2 GB), while `pdf/` keeps the volumes.

## How the repository is laid out
```
AGENTS.md                 the author's charter (OpenCode loads it automatically)
bible/                    world, history, peoples, calendar, magic, bestiary, factions, glossary, premise, voice
plan/                     the author's private roadmap: arcs, threads ledger, next chapters, wanted maps
memory/                   state of the world now, day-by-day timeline, story so far, gazetteer, digests
characters/               one sheet (.md) and ink portrait (.svg) per character
atlas/<slug>/             hand-made HTML maps, rendered to the Atlas
book/chapters/ch-NNNN/    meta.json, plan.md, scene-NN.tex, summary.md, decoration.tex, chapter.tex
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

## Running the press
```bash
systemctl --user status storyforge      # is it running?
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
