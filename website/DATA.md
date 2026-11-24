# Website data contract

The press regenerates the data after every chapter. Your frontend (this folder) is copied beside it into `build/site/`, which is published to GitHub Pages. **All paths are relative to the site root.** The site may be served from a sub-path (`/the-debt-of-warmth/`), so never use absolute URLs starting with `/`.

## Files the press provides
| Path | What |
|---|---|
| `data/book.json` | The manifest (below) |
| `data/chapters/ch-NNNN.html` | One chapter's body, an HTML fragment: `<header class="chapter-head">` (`.chap-num`, `.chap-n`, `h1`, `.when`), optional `<blockquote class="epigraph">` (with `p.attr`), then the scenes as `<p>` paragraphs, with these inside: `<div class="daymark" id="day-37-2"><p class="day">— Day 37 —</p><p class="daydate">…</p></div>` at every new day; `<p class="break">❦</p>` scene breaks; `<span class="dropcap">T</span><span class="sc">he stone</span>` (first paragraph `p.first`); `<em class="memory">`, `.sc`, `.inscr`, `blockquote.letter`, `div.verse`; and at the end `<aside class="chronicle"><p class="ctitle">…</p>…</aside>` |
| `data/characters/<slug>.html` | Character sheet sections (`h3` headings with paragraphs and lists) |
| `data/codex/<slug>.html`, `data/lore/<n>.html` | In-world documents and lore, as HTML |
| `data/timeline.json` | `[{"day": 1, "text": "Stone 7, Y.H. 812 | place | what happened"}, …]`, one entry per lived day |
| `images/cover.jpg`, `images/frontispiece.jpg`, `images/parchment.jpg` | Cover, colour frontispiece, paper texture |
| `images/plates/ch-NNNN.jpg` | Full-page colour plate for a chapter (2:3, light-novel style) |
| `images/characters/<slug>.webp` or `.svg` | Character art (transparent WebP) or cameo plate (SVG) |
| `images/maps/<slug>.jpg` | Maps |
| `images/emblem.svg` | The book's cover emblem: the cupped hand holding a coal, a crack through the palm letting the warmth escape as a gold thread, in a gilt ring. It is the saga's sigil. |
| `images/ornaments/<name>.svg` | The **book's own engraved ornaments** in gold (the same ones the printed book uses): `corner`, `corner-grand`, `rule`, `rule-medallion`, `headpiece`, `vignette`, `fleuron`, `tailpiece`, `flourish`, `headband`. Black versions for CSS `mask-image` (so you can recolour them per theme) are in `images/ornaments/mask/`. |
| `images/headpieces/ch-NNNN.svg` | Each chapter's own headpiece: the emblem you designed in TikZ for that chapter, shown above its title in the book |
| `fonts/` | `EBGaramond-Regular.otf`, `EBGaramond-Italic.otf`, `EBGaramond-SemiBold.otf`, `Cinzel-Regular.ttf`, `CinzelDecorative-Regular.ttf`, `CinzelDecorative-Bold.ttf`, `IMFeENrm28P.otf`, `IMFeENit28P.otf` |

## `data/book.json`
```json
{
  "title": "...", "subtitle": "...", "tagline": "...", "byline": "...", "updated": "ISO time",
  "repository": "https://github.com/OWNER/REPO",
  "downloads": {"pdf": "url", "epub": "url", "cover_pdf": "url"},
  "cover": "images/cover.jpg", "frontispiece": "images/frontispiece.jpg", "emblem": "images/emblem.svg",
  "ornaments": {"corner": "images/ornaments/corner.svg", "...": "..."}, "ornament_masks": {"corner": "images/ornaments/mask/corner.svg"},
  "words_total": 116185,
  "arcs": [{"number": 1, "title": "...", "subtitle": "...", "chapters": [1, 2, 3]}],
  "chapters": [{"n": 1, "title": "...", "arc": 1, "when": "...", "where": "...",
                "day_start": 1, "day_end": 1, "days": [{"id": "day-1-0", "label": "Day 1"}],
                "words": 13459, "plate": "images/plates/ch-0001.jpg", "caption": "...", "headpiece": "images/headpieces/ch-0001.svg",
                "html": "data/chapters/ch-0001.html", "pdf": "url of this chapter's PDF"}],
  "characters": [{"slug": "...", "name": "...", "epithet": "...", "role": "...", "status": "...",
                  "first_appearance": 40, "appeared": false, "image": "images/characters/x.webp", "html": "data/characters/x.html"}],
  "maps": [{"slug": "...", "title": "...", "caption": "...", "image": "images/maps/x.jpg"}],
  "codex": [{"slug": "...", "title": "...", "kind": "...", "provenance": "...", "html": "data/codex/x.html"}],
  "lore": [{"title": "...", "html": "data/lore/0.html"}]
}
```
Any field may be null or empty. The book grows to **thousands of chapters**, so never fetch every chapter at once, and keep the table of contents usable at that scale.

## Preview
Run `python3 forge/site.py build` (it copies this folder into `build/site/` beside fresh data), then `cd build/site && python3 -m http.server 8799` and open `http://localhost:8799/`.
