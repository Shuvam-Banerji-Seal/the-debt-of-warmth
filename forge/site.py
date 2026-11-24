#!/usr/bin/env python3
"""The website: data export (mechanical) + the author's frontend + GitHub Pages deploy.

The author model designs and writes the site's frontend in website/ (HTML, CSS,
JS). This script exports the book as data the frontend reads, assembles
build/site/, and publishes it to the gh-pages branch as a single orphan commit
(git plumbing with a private index, so main's index and work tree are untouched).

Data contract (documented for the author in website/DATA.md):
  data/book.json             manifest: title, downloads, arcs, chapters, cast, maps, codex, lore
  data/chapters/ch-NNNN.html chapter body fragment (head, epigraph, day marks with ids, scenes, chronicle)
  data/characters/<slug>.html, data/codex/<slug>.html, data/lore/<n>.html, data/timeline.json
  images/{plates,characters,maps}/..., images/cover.jpg, images/frontispiece.jpg, images/parchment.jpg
  fonts/*.otf|ttf

  python3 forge/site.py build|deploy
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import epub  # noqa: E402
import md2tex  # noqa: E402

ROOT = build.ROOT
SITE = build.BUILD / "site"
WEB = ROOT / "website"
FORGE = ROOT / ".forge"


def repo_slug() -> str | None:
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
        return m.group(1) if m else None
    except Exception:
        return None


def _img(src: Path | None, dest: Path, fmt: str, max_px: int) -> str | None:
    if not src or not src.exists():
        return None
    try:
        from PIL import Image
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
            return dest.relative_to(SITE).as_posix()
        im = Image.open(src)
        im.thumbnail((max_px, max_px))
        if fmt == "webp":
            im.convert("RGBA").save(dest, "WEBP", quality=84, method=5)
        else:
            im.convert("RGB").save(dest, "JPEG", quality=84, optimize=True, progressive=True)
        return dest.relative_to(SITE).as_posix()
    except Exception:
        return None


SVG_PRE = r"""\documentclass[border=3pt]{standalone}
\usepackage{fontspec,xcolor,tikz,pgfornament}
\usetikzlibrary{calc,shapes,shapes.geometric,shapes.symbols,decorations.pathmorphing,decorations.pathreplacing,
  decorations.markings,decorations.text,patterns,fadings,shadows,arrows.meta,positioning,intersections,backgrounds}
\setmainfont{EBGaramond}[Path=fonts/,Extension=.otf,UprightFont=*-Regular,ItalicFont=*-Italic]
\newfontfamily\CinzelFont{Cinzel}[Path=fonts/,Extension=.ttf,UprightFont=*-Regular,BoldFont=*-Bold]
\newfontfamily\CinzelDeco{CinzelDecorative}[Path=fonts/,Extension=.ttf,UprightFont=*-Regular,BoldFont=*-Bold]
\newfontfamily\FellFont{IMFeEN}[Path=fonts/,Extension=.otf,UprightFont=*rm28P,ItalicFont=*it28P]
\newfontfamily\FellSC{IMFeENsc28P}[Path=fonts/,Extension=.otf]
\definecolor{ink}{HTML}{2B1B0E}\definecolor{rubric}{HTML}{7E1F14}\definecolor{gold}{HTML}{9A7432}
\definecolor{faded}{HTML}{6E5B42}\definecolor{blood}{HTML}{5C0B0B}\definecolor{moss}{HTML}{4A5A2E}
\definecolor{night}{HTML}{1F2A3A}\definecolor{ash}{HTML}{8C857B}\definecolor{vellum}{HTML}{EFE2C4}
\colorlet{ornament}{gold!85!ink}
\definecolor{goldhi}{HTML}{F3DC93}\definecolor{golddk}{HTML}{8A6A28}\definecolor{tooling}{HTML}{1E0905}
\begin{document}
"""

ORNAMENTS = {  # name: (pgfornament number, width cm, symmetry)
    "corner": (61, 3, ""), "corner-grand": (63, 3.5, ""), "rule": (88, 9, ""), "rule-medallion": (84, 9, ""),
    "headpiece": (69, 8, ""), "vignette": (65, 5, ""), "fleuron": (11, 2.2, ""), "tailpiece": (72, 5, ""),
    "flourish": (75, 6, ""), "headband": (46, 7, ""),
}


def tex_svg(body: str, dest: Path, deps: list[Path] = ()) -> str | None:
    """Typeset a TikZ/ornament snippet and convert it to SVG (cached by mtime)."""
    newest = max([p.stat().st_mtime for p in deps if p.exists()] + [Path(__file__).stat().st_mtime])
    if dest.exists() and dest.stat().st_mtime >= newest:
        return dest.relative_to(SITE).as_posix()
    work = build.BUILD / "svgwork" / dest.stem
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    tex = work / "s.tex"
    tex.write_text(SVG_PRE + body + "\n\\end{document}\n", encoding="utf-8")
    r = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={work}",
                        str(tex.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True, timeout=300)
    pdf = work / "s.pdf"
    if r.returncode != 0 or not pdf.exists():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftocairo", "-svg", str(pdf), str(dest)], capture_output=True, timeout=120)
    return dest.relative_to(SITE).as_posix() if dest.exists() else None


def design_assets() -> dict:
    out = {"ornaments": {}, "ornament_masks": {}, "emblem": None}
    for name, (num, w, sym) in ORNAMENTS.items():
        so = f",symmetry={sym}" if sym else ""
        p = tex_svg(f"\\pgfornament[width={w}cm,color=ornament{so}]{{{num}}}", SITE / "images" / "ornaments" / f"{name}.svg")
        m = tex_svg(f"\\pgfornament[width={w}cm,color=black{so}]{{{num}}}", SITE / "images" / "ornaments" / "mask" / f"{name}.svg")
        if p:
            out["ornaments"][name] = p
        if m:
            out["ornament_masks"][name] = m
    em = ROOT / "design" / "cover" / "emblem.tex"
    if em.exists():
        out["emblem"] = tex_svg(
            "\\begin{tikzpicture}[x=1in,y=1in]\n\\fill[tooling] (0,0) circle (1.27);\n"
            "\\draw[gold,line width=1.2pt] (0,0) circle (1.22);\\draw[golddk,line width=0.5pt] (0,0) circle (1.12);\n"
            "\\foreach \\a in {0,7.5,...,352.5}{\\draw[gold,line width=0.45pt] (\\a:1.16) -- (\\a:1.22);}\n"
            "\\input{design/cover/emblem.tex}\n\\end{tikzpicture}", SITE / "images" / "emblem.svg", [em])
    return out


def headpiece(n: int) -> str | None:
    deco = build.chdir(n) / "decoration.tex"
    if not deco.exists():
        return None
    return tex_svg(f"\\input{{{deco.relative_to(ROOT).as_posix()}}}", SITE / "images" / "headpieces" / f"ch-{n:04d}.svg", [deco])


def export() -> dict:
    meta = build.book_meta()
    slug = repo_slug()
    title_slug = re.sub(r"[^A-Za-z0-9]+", "-", meta["title"]).strip("-")
    gh = f"https://github.com/{slug}" if slug else ""
    data_dir = SITE / "data"
    for sub in ("chapters", "characters", "codex", "lore"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)

    book = {
        "title": meta["title"], "subtitle": meta.get("subtitle", ""), "tagline": meta.get("tagline", ""),
        "byline": meta.get("byline", ""), "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "repository": gh,
        "downloads": {
            "pdf": f"{gh}/releases/latest/download/{title_slug}.pdf" if gh else "",
            "epub": f"{gh}/releases/latest/download/{title_slug}.epub" if gh else "",
            "cover_pdf": f"{gh}/releases/latest/download/{title_slug}-Cover.pdf" if gh else "",
        },
        "cover": None, "frontispiece": None, "arcs": [], "chapters": [], "characters": [], "maps": [],
        "codex": [], "lore": [],
    }
    book.update(design_assets())
    cover_pdf = build.BUILD / "cover" / "cover.pdf"
    if cover_pdf.exists():
        (SITE / "images").mkdir(parents=True, exist_ok=True)
        subprocess.run(["magick", "-density", "200", f"{cover_pdf}[0]", "-quality", "86", str(SITE / "images" / "cover.jpg")],
                       capture_output=True)
        book["cover"] = "images/cover.jpg"
    book["frontispiece"] = _img(build._art_source(build.ART / "frontispiece"), SITE / "images" / "frontispiece.jpg", "jpg", 1536)
    shutil.copy2(ROOT / "design" / "textures" / "parchment.jpg", SITE / "images" / "parchment.jpg")

    words_total = 0
    arcs: dict = {}
    for n in build.completed_chapters():
        d = build.chdir(n)
        m = build.load_json(d / "meta.json", {}) or {}
        days: list = []
        parts = []
        epi = m.get("epigraph") or {}
        if isinstance(epi, str):
            epi = {"text": epi}
        when = " · ".join(x for x in (m.get("when", ""), m.get("where", "")) if x)
        parts.append(f"<header class=\"chapter-head\"><p class=\"chap-num\">Chapter</p><p class=\"chap-n\">{n}</p>"
                     f"<h1>{epub.md_inline(m.get('title', f'Chapter {n}'))}</h1><p class=\"when\">{epub.md_inline(when)}</p></header>")
        if epi.get("text"):
            parts.append(f"<blockquote class=\"epigraph\"><p>{epub.md_inline(epi['text'])}</p>"
                         + (f"<p class=\"attr\">— {epub.md_inline(epi.get('attribution', ''))}</p>" if epi.get("attribution") else "")
                         + "</blockquote>")
        for i, sf in enumerate(build.scene_files(n)):
            text = sf.read_text(encoding="utf-8", errors="replace")
            if i and not text.lstrip().startswith("\\daymark"):
                parts.append("<p class=\"break\">❦</p>")
            parts.append(epub.scene_html(sf, days))
        sm = d / "summary.md"
        if sm.exists():
            _, sb = md2tex.parse_front_matter(sm.read_text(encoding="utf-8", errors="replace"))
            chron = next((t for h, t in md2tex.split_sections(sb) if "chronicle" in h.lower()), "")
            if chron.strip():
                parts.append(f"<aside class=\"chronicle\"><p class=\"ctitle\">The Chronicle of Chapter {n}</p>{epub.md_html(chron)}</aside>")
        html = "\n".join(parts).replace(epub.BLOCK, "")
        (data_dir / "chapters" / f"ch-{n:04d}.html").write_text(html, encoding="utf-8")
        wc = sum(build.word_count_tex(f.read_text(encoding="utf-8", errors="replace")) for f in build.scene_files(n))
        words_total += wc
        plate = _img(build._art_source(build.ART / "chapters" / f"ch-{n:04d}"), SITE / "images" / "plates" / f"ch-{n:04d}.jpg", "jpg", 1536)
        arc = m.get("arc") or {}
        akey = f"{arc.get('number', '')}|{arc.get('title', '')}" if isinstance(arc, dict) else "|"
        if akey not in arcs:
            arcs[akey] = {"number": arc.get("number"), "title": arc.get("title", ""), "subtitle": arc.get("subtitle", ""), "chapters": []}
        arcs[akey]["chapters"].append(n)
        dd = m.get("days") or {}
        book["chapters"].append({
            "n": n, "title": m.get("title", ""), "arc": arc.get("number") if isinstance(arc, dict) else None,
            "when": m.get("when", ""), "where": m.get("where", ""),
            "day_start": dd.get("start"), "day_end": dd.get("end"),
            "days": [{"id": did, "label": lab} for did, lab in days],
            "words": wc, "plate": plate, "caption": build.plate_caption(n), "headpiece": headpiece(n),
            "html": f"data/chapters/ch-{n:04d}.html",
            "pdf": f"{gh}/releases/download/volume-{build.volume_of(n):03d}/{title_slug}-Chapter-{n:04d}.pdf" if gh else "",
        })
    book["arcs"] = list(arcs.values())
    book["words_total"] = words_total

    for c in build.characters():
        parts = []
        for head, text in md2tex.split_sections(c["_body"]):
            if head and any(w in head.lower() for w in build.PRIVATE_SECTION_WORDS):
                continue
            if head:
                parts.append(f"<h3>{epub.md_inline(head)}</h3>")
            parts.append(epub.md_html(text, 4))
        (data_dir / "characters" / f"{c['slug']}.html").write_text("\n".join(parts), encoding="utf-8")
        src = build._art_source(build.ART / "characters" / c["slug"])
        image = _img(src, SITE / "images" / "characters" / f"{c['slug']}.webp", "webp", 1100) if src else None
        if not image and (ROOT / "characters" / f"{c['slug']}.svg").exists():
            dest = SITE / "images" / "characters" / f"{c['slug']}.svg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "characters" / f"{c['slug']}.svg", dest)
            image = dest.relative_to(SITE).as_posix()
        first = c.get("first_appearance")
        book["characters"].append({
            "slug": c["slug"], "name": str(c.get("name")), "epithet": str(c.get("epithet", "") or ""),
            "role": str(c.get("role", "") or ""), "status": str(c.get("status", "") or ""),
            "first_appearance": first if isinstance(first, int) else None,
            "appeared": isinstance(first, int) and first <= (book["chapters"][-1]["n"] if book["chapters"] else 0),
            "image": image, "html": f"data/characters/{c['slug']}.html"})

    for d in build.map_dirs():
        mm = build.load_json(d / "meta.json", {}) or {}
        src = build.BUILD / "atlas" / f"{d.name}.jpg"
        img = _img(src if src.exists() else build.BUILD / "atlas" / f"{d.name}.png", SITE / "images" / "maps" / f"{d.name}.jpg", "jpg", 2400)
        if img:
            book["maps"].append({"slug": d.name, "title": mm.get("title", d.name), "caption": mm.get("caption", ""), "image": img})

    for p in sorted((ROOT / "codex").glob("*.md")):
        fm, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
        if fm.get("title") and len(body.split()) >= 200:
            (data_dir / "codex" / f"{p.stem}.html").write_text(epub.md_html(body, 3), encoding="utf-8")
            book["codex"].append({"slug": p.stem, "title": str(fm["title"]), "kind": str(fm.get("kind", "")),
                                  "provenance": str(fm.get("provenance", "")), "html": f"data/codex/{p.stem}.html"})
    for i, (lt, fname) in enumerate(build.LORE_FILES):
        p = ROOT / "bible" / fname
        if p.exists():
            _, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
            (data_dir / "lore" / f"{i}.html").write_text(epub.md_html(body, 2), encoding="utf-8")
            book["lore"].append({"title": lt, "html": f"data/lore/{i}.html"})
    (data_dir / "timeline.json").write_text(json.dumps(
        [{"day": d, "text": t} for d, t in build.timeline_entries()], ensure_ascii=False), encoding="utf-8")
    (data_dir / "book.json").write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return book


def assemble() -> Path:
    SITE.mkdir(parents=True, exist_ok=True)
    export()
    fonts = SITE / "fonts"
    fonts.mkdir(exist_ok=True)
    for f in ("EBGaramond-Regular.otf", "EBGaramond-Italic.otf", "EBGaramond-SemiBold.otf", "Cinzel-Regular.ttf",
              "CinzelDecorative-Regular.ttf", "CinzelDecorative-Bold.ttf", "IMFeENit28P.otf", "IMFeENrm28P.otf"):
        shutil.copy2(ROOT / "fonts" / f, fonts / f)
    if WEB.exists():  # the author's frontend
        for f in WEB.rglob("*"):
            if f.is_file() and f.name != "DATA.md":
                dest = SITE / f.relative_to(WEB)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
    (SITE / ".nojekyll").write_text("")
    return SITE


def deploy(message: str = "Site") -> bool:
    """Publish build/site to the gh-pages branch as one orphan commit."""
    if not SITE.exists():
        return False
    env = dict(os.environ, GIT_INDEX_FILE=str(FORGE / "pages.index"))
    run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, env=env, capture_output=True, text=True)  # noqa: E731
    (FORGE / "pages.index").unlink(missing_ok=True)
    r = run(f"--work-tree={SITE}", "add", "-A", "--force", ".")
    if r.returncode != 0:
        return False
    tree = run("write-tree").stdout.strip()
    commit = run("commit-tree", tree, "-m", message).stdout.strip()
    if not commit:
        return False
    run("update-ref", "refs/heads/gh-pages", commit)
    if run("remote").stdout.strip():
        p = run("push", "-q", "-f", "origin", f"{commit}:refs/heads/gh-pages")
        return p.returncode == 0
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    out = assemble()
    print(out)
    if cmd == "deploy":
        print("deployed" if deploy("Site: manual deploy") else "deploy failed")
