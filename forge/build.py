#!/usr/bin/env python3
"""Mechanical assembly and typesetting of the chronicle.

Nothing in here writes story text. It turns the author model's files into
LaTeX masters, proof-compiles every piece the author produces, renders the
author's HTML maps and SVG portraits, and builds the volume PDFs.

CLI:
  python3 forge/build.py chapter N        # (re)generate chapter.tex + proof it
  python3 forge/build.py volume V         # build pdf for volume V
  python3 forge/build.py compendium       # characters + atlas + lore
  python3 forge/build.py maps             # render atlas/*/map.html
  python3 forge/build.py cover            # build the cover
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md2tex  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "book" / "chapters"
VOLUMES = ROOT / "book" / "volumes"
BUILD = ROOT / "build"
VOL_SIZE = int(os.environ.get("CHRONICLE_VOL_SIZE", "20"))
CHROME = Path.home() / ".cache/ms-playwright/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell"

ROLE_ORDER = ["protagonist", "past-life", "family", "love-interest", "companion", "mentor",
              "ally", "rival", "antagonist", "villain", "other", "minor"]
PRIVATE_SECTION_WORDS = ("secret", "private", "plan", "future", "author", "hidden", "spoiler")


# --------------------------------------------------------------- helpers
def chdir(n: int) -> Path:
    return CHAPTERS / f"ch-{n:04d}"


def load_json(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def book_meta() -> dict:
    m = load_json(ROOT / "bible" / "book.json", {}) or {}
    m.setdefault("title", "Untitled Chronicle")
    m.setdefault("subtitle", "")
    m.setdefault("byline", "Written by Hy4 Flash")
    return m


def esc(s) -> str:
    return md2tex.inline(str(s or "")).replace("\n", " ")


def volume_of(n: int) -> int:
    return (n - 1) // VOL_SIZE + 1


def is_complete(n: int) -> bool:
    return (chdir(n) / ".complete").exists()


def completed_chapters() -> list[int]:
    out = []
    for d in sorted(CHAPTERS.glob("ch-*")):
        if (d / ".complete").exists():
            try:
                out.append(int(d.name[3:]))
            except ValueError:
                pass
    return out


def scene_files(n: int) -> list[Path]:
    return sorted(chdir(n).glob("scene-[0-9][0-9].tex"))


_CMD = re.compile(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?")


def word_count_tex(text: str) -> int:
    text = re.sub(r"(?m)^\s*%.*$", "", text)
    text = _CMD.sub(" ", text)
    return len(re.findall(r"[A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\u2019-]*", text))


# ------------------------------------------------------- scene hygiene
_STRIP_LINE = re.compile(
    r"^\s*\\(documentclass|usepackage|begin\{document\}|end\{document\}|maketitle|tableofcontents|"
    r"chapter|section|subsection|subsubsection|part|input|include|directlua|write|immediate|openout|"
    r"def|edef|gdef|newcommand|renewcommand|providecommand|let|catcode|makeatletter|makeatother|"
    r"newpage|clearpage|cleardoublepage|pagebreak|newenvironment|title|author|date)\b.*$",
    re.M)


def sanitize_scene(path: Path) -> bool:
    """Normalise a scene file in place. Returns True if it changed."""
    src = path.read_text(encoding="utf-8", errors="replace")
    t = src.replace("\r\n", "\n").replace("\ufeff", "")
    t = re.sub(r"^```[a-zA-Z]*\s*$", "", t, flags=re.M)          # stray code fences
    t = _STRIP_LINE.sub("", t)
    t = re.sub(r"(?m)^\s*%.*\n?", "", t)                           # comment lines
    t = re.sub(r"(?<!\\)%", r"\\%", t)                              # stray percent signs
    t = re.sub(r"(?<!\\)&", r"\\&", t)
    t = re.sub(r"(?<!\\)#", r"\\#", t)
    t = re.sub(r"(?<!\\)\$", r"\\$", t)
    t = re.sub(r"(?<![\\\w])_(?!\w)", r"\\_", t)
    t = re.sub(r"(?<=\w)_(?=\w)", r"\\_", t)
    t = re.sub(r'(^|[\s(\[{\u2014\u2013-])"', "\\1\u201c", t, flags=re.M)
    t = t.replace('"', "\u201d")
    t = re.sub(r"\n{3,}", "\n\n", t).strip() + "\n"
    if t != src:
        path.write_text(t, encoding="utf-8")
        return True
    return False


SAFE_CMDS = {"emph", "textit", "textbf", "textsc", "person", "place", "lore", "dropcap", "scenebreak",
             "memory", "sound", "inscription", "letterhand", "ldots", "dots", "textperiodcentered",
             "begin", "end", "par", "noindent", "enspace", "quad", "smallskip", "medskip", "bigskip",
             "textemdash", "textendash", "S", "P", "&", "%", "$", "#", "_", "{", "}"}
SAFE_ENVS = {"verseblock", "quote", "quotation", "center", "itemize", "enumerate"}


def harden_scene(path: Path) -> None:
    """Last resort after failed repairs: keep the prose, drop unknown markup."""
    t = path.read_text(encoding="utf-8", errors="replace")

    def cmd(m):
        name = m.group(1)
        return m.group(0) if name in SAFE_CMDS else ""
    t = re.sub(r"\\begin\{(\w+\*?)\}", lambda m: m.group(0) if m.group(1) in SAFE_ENVS else "", t)
    t = re.sub(r"\\end\{(\w+\*?)\}", lambda m: m.group(0) if m.group(1) in SAFE_ENVS else "", t)
    t = re.sub(r"\\([a-zA-Z]+)\*?", cmd, t)
    # balance braces crudely
    depth, out = 0, []
    for ch in t:
        if ch == "{":
            depth += 1
        elif ch == "}":
            if depth == 0:
                continue
            depth -= 1
        out.append(ch)
    t = "".join(out) + "}" * depth
    path.write_text(t, encoding="utf-8")


def flatten_scene(path: Path) -> None:
    """Absolute last resort: plain prose, everything escaped."""
    t = path.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"\\(person|place|lore|emph|textit|textsc|textbf|memory|sound|inscription)(\[[^\]]*\])?\{([^{}]*)\}", r"\3", t)
    t = re.sub(r"\\dropcap\{([^{}]*)\}\{([^{}]*)\}", r"\1\2", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)
    paras = [md2tex.escape(p.replace("{", "").replace("}", "").strip()) for p in re.split(r"\n\s*\n", t)]
    path.write_text("\n\n".join(p for p in paras if p) + "\n", encoding="utf-8")


# ------------------------------------------------------------- compile
def _run_lualatex(tex: Path, outdir: Path, halt=True, timeout=1800):
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = ["lualatex", "-interaction=nonstopmode", "-file-line-error"]
    if halt:
        cmd.append("-halt-on-error")
    cmd += [f"-output-directory={outdir}", str(tex.relative_to(ROOT))]
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return p.returncode
    except subprocess.TimeoutExpired:
        return 124


def log_excerpt(log: Path, max_lines=40) -> str:
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return "(no log)"
    out = []
    for i, l in enumerate(lines):
        if l.startswith("!") or re.match(r"^\S+\.tex:\d+:", l):
            out.extend(lines[i:i + 8])
            out.append("...")
            if len(out) > max_lines:
                break
    return "\n".join(out[:max_lines]) or "\n".join(lines[-25:])


def proof(name: str, body: str) -> tuple[bool, str]:
    """Compile a small proof document; return (ok, error excerpt)."""
    meta = book_meta()
    d = BUILD / "proof" / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    tex = d / "proof.tex"
    tex.write_text("\\documentclass{design/chronicle}\n\\BookTitle{" + esc(meta["title"]) + "}\n"
                   "\\begin{document}\\mainmatter\n" + body + "\n\\end{document}\n", encoding="utf-8")
    rc = _run_lualatex(tex, d, timeout=600)
    ok = rc == 0 and (d / "proof.pdf").exists()
    return ok, ("" if ok else log_excerpt(d / "proof.log"))


def proof_scene(n: int, k: int) -> tuple[bool, str]:
    p = chdir(n) / f"scene-{k:02d}.tex"
    return proof(f"ch-{n:04d}-s{k:02d}",
                 f"\\CRchapter{{{n}}}{{Proof}}{{}}{{}}\n\\input{{{p.relative_to(ROOT).as_posix()}}}\n")


def proof_decoration(n: int) -> tuple[bool, str]:
    p = chdir(n) / "decoration.tex"
    return proof(f"ch-{n:04d}-deco",
                 f"\\CRdecoration{{{p.relative_to(ROOT).as_posix()}}}\n\\CRchapter{{{n}}}{{Proof}}{{}}{{}}\nText.\n")


def proof_chapter(n: int) -> tuple[bool, str]:
    write_chapter_tex(n)
    p = chdir(n) / "chapter.tex"
    return proof(f"ch-{n:04d}", f"\\input{{{p.relative_to(ROOT).as_posix()}}}\n")


# --------------------------------------------------------- chapter.tex
def chronicle_from_summary(n: int) -> str:
    p = chdir(n) / "summary.md"
    if not p.exists():
        return ""
    _, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
    for head, text in md2tex.split_sections(body):
        if "chronicle" in head.lower():
            return md2tex.blocks(text)
    secs = md2tex.split_sections(body)
    return md2tex.blocks(secs[0][1]) if secs else ""


def write_chapter_tex(n: int) -> Path:
    d = chdir(n)
    meta = load_json(d / "meta.json", {}) or {}
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731
    title = meta.get("title") or f"Chapter {n}"
    when = meta.get("when", "")
    where = meta.get("where", "")
    epi = meta.get("epigraph") or {}
    if isinstance(epi, str):
        epi = {"text": epi, "attribution": ""}
    lines = ["% Generated by forge/build.py from meta.json and the author's scene files.",
             "% Edit the scene files, not this file."]
    deco = d / "decoration.tex"
    if deco.exists():
        lines.append(f"\\CRdecoration{{{rel(deco)}}}")
    lines.append(f"\\CRchapter{{{n}}}{{{esc(title)}}}{{{esc(when)}}}{{{esc(where)}}}")
    lines.append(f"\\CRepigraph{{{esc(epi.get('text', ''))}}}{{{esc(epi.get('attribution', ''))}}}")
    scenes = scene_files(n)
    for i, s in enumerate(scenes):
        if i:
            lines.append("\\scenebreak")
        lines.append(f"\\input{{{rel(s)}}}")
    chron = chronicle_from_summary(n)
    lines.append("\\CRtailpiece")
    if chron.strip():
        lines += [f"\\begin{{CRchronicle}}{{{n}}}", chron.strip(), "\\end{CRchronicle}"]
    out = d / "chapter.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# --------------------------------------------------------- characters
def characters() -> list[dict]:
    out = []
    for p in sorted((ROOT / "characters").glob("*.md")):
        if p.name.startswith("_"):
            continue
        fm, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
        fm = {str(k).lower(): v for k, v in fm.items()}
        fm["slug"] = p.stem
        fm["_body"] = body
        fm.setdefault("name", p.stem.replace("-", " ").title())
        out.append(fm)

    def key(c):
        role = str(c.get("role", "other")).lower()
        idx = next((i for i, r in enumerate(ROLE_ORDER) if r in role), len(ROLE_ORDER))
        return (idx, str(c.get("name")))
    return sorted(out, key=key)


def character_tex(c: dict) -> str:
    fields = []
    for label, keys in [("Also called", ("aliases", "alias")), ("Role", ("role",)),
                        ("Born", ("born", "birth")), ("Kind", ("species", "race", "kind")),
                        ("Origin", ("origin", "homeland")), ("Allegiance", ("affiliation", "allegiance", "faction")),
                        ("Status", ("status",)), ("First seen", ("first_appearance", "first_seen"))]:
        for k in keys:
            v = c.get(k)
            if v not in (None, "", [], "null"):
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v)
                if k in ("first_appearance", "first_seen") and str(v).isdigit():
                    v = f"Chapter {v}"
                fields.append(f"\\CRfield{{{esc(label)}}}{{{esc(v)}}}")
                break
    body = []
    for head, text in md2tex.split_sections(c["_body"]):
        if not head:
            if text.strip():
                body.append(md2tex.blocks(text, r"\CRsheetheading"))
            continue
        if any(w in head.lower() for w in PRIVATE_SECTION_WORDS):
            continue
        body.append(f"\\CRsheetheading{{{esc(head)}}}\n" + md2tex.blocks(text, r"\subsection*"))
    portrait = BUILD / "portraits" / f"{c['slug']}.pdf"
    ptxt = portrait.relative_to(ROOT).as_posix() if portrait.exists() else ""
    return (f"\\CRcharacter{{{esc(c['name'])}}}{{{esc(c.get('epithet', ''))}}}{{{ptxt}}}"
            f"{{{''.join(fields) or ' '}}}{{{chr(10).join(body)}}}\n")


def render_portraits() -> dict:
    res = {}
    out = BUILD / "portraits"
    out.mkdir(parents=True, exist_ok=True)
    for svg in sorted((ROOT / "characters").glob("*.svg")):
        pdf = out / f"{svg.stem}.pdf"
        if pdf.exists() and pdf.stat().st_mtime >= svg.stat().st_mtime:
            res[svg.stem] = (True, "")
            continue
        p = subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(svg)],
                           capture_output=True, text=True, timeout=120)
        ok = p.returncode == 0 and pdf.exists() and pdf.stat().st_size > 800
        if not ok and pdf.exists():
            pdf.unlink()
        res[svg.stem] = (ok, p.stderr[-800:])
    return res


# ---------------------------------------------------------------- maps
def map_dirs() -> list[Path]:
    return sorted(p.parent for p in (ROOT / "atlas").glob("*/map.html"))


def render_map(d: Path, force=False) -> tuple[bool, str]:
    meta = load_json(d / "meta.json", {}) or {}
    w, h = int(meta.get("width", 2400)), int(meta.get("height", 1600))
    out = BUILD / "atlas" / f"{d.name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    newest = max(f.stat().st_mtime for f in d.iterdir() if f.is_file())
    if out.exists() and not force and out.stat().st_mtime >= newest:
        return True, ""
    if not CHROME.exists():
        return False, f"headless chrome not found at {CHROME}"
    cmd = [str(CHROME), "--no-sandbox", "--hide-scrollbars", "--disable-gpu",
           f"--window-size={w},{h}", "--virtual-time-budget=15000",
           "--allow-file-access-from-files", "--force-device-scale-factor=1",
           f"--screenshot={out}", (d / "map.html").as_uri()]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return False, "map render timed out (does the script loop forever?)"
    if p.returncode != 0 or not out.exists():
        return False, p.stderr[-1200:]
    try:
        from PIL import Image, ImageStat
        im = Image.open(out).convert("L").resize((300, 200))
        st = ImageStat.Stat(im)
        if st.stddev[0] < 6:
            out.unlink()
            return False, "the rendered map is blank or almost uniform (did the drawing code throw an error?)"
    except Exception as e:  # pragma: no cover
        return False, f"could not inspect render: {e}"
    return True, ""


def render_maps(force=False) -> dict:
    return {d.name: render_map(d, force) for d in map_dirs()}


def map_tex(d: Path) -> str:
    png = BUILD / "atlas" / f"{d.name}.png"
    if not png.exists():
        return ""
    meta = load_json(d / "meta.json", {}) or {}
    title = meta.get("title", d.name.replace("-", " ").title())
    cap = meta.get("caption", "")
    try:
        from PIL import Image
        w, h = Image.open(png).size
    except Exception:
        w, h = 3, 2
    star = "*" if w > h * 1.15 else ""
    return f"\\CRmap{star}{{{esc(title)}}}{{{png.relative_to(ROOT).as_posix()}}}{{{esc(cap)}}}\n"


# ------------------------------------------------------------ timeline
_DAY = re.compile(r"^[\s|*-]*Day\s+(\d+)\s*[|:\u2014\u2013-]+\s*(.*)$", re.I)


def timeline_entries() -> list[tuple[int, str]]:
    p = ROOT / "memory" / "timeline.md"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _DAY.match(line)
        if m:
            out.append((int(m.group(1)), m.group(2).strip().strip("|").strip()))
    return out


def timeline_tex(lo: int, hi: int) -> str:
    items = [f"\\CRday{{Day {d}}}{{{md2tex.inline(t.replace('|', ' — '))}}}" for d, t in timeline_entries() if lo <= d <= hi]
    if not items:
        return ""
    return "\\begin{CRtimeline}\n" + "\n".join(items) + "\n\\end{CRtimeline}\n"


# ------------------------------------------------------------- masters
def _front(meta: dict, vol_line: str, vol_title: str) -> list[str]:
    L = ["\\documentclass{design/chronicle}",
         f"\\BookTitle{{{esc(meta['title'])}}}",
         f"\\hypersetup{{pdftitle={{{esc(meta['title'])} -- {esc(vol_line)}}},pdfauthor={{{esc(meta['byline'])}}}}}",
         "\\begin{document}", "\\frontmatter"]
    cover = BUILD / "cover" / "cover.pdf"
    if cover.exists():
        L.append(f"\\includepdf[pages=1,pagecommand={{\\thispagestyle{{empty}}\\CRnobgthispage}}]{{{cover.relative_to(ROOT).as_posix()}}}")
    L.append(f"\\CRtitlepage{{{esc(meta['title'])}}}{{{esc(meta.get('subtitle', ''))}}}"
             f"{{{esc(vol_line)}}}{{{esc(vol_title)}}}{{{esc(meta['byline'])}}}")
    L.append("\\input{design/colophon.tex}")
    L.append("\\tableofcontents")
    return L


def _indices() -> list[str]:
    return ["\\printindex[persons]", "\\printindex[places]", "\\printindex[lore]"]


def volume_master(v: int) -> Path | None:
    meta = book_meta()
    chs = [n for n in completed_chapters() if volume_of(n) == v]
    if not chs:
        return None
    L = _front(meta, f"Volume {v}", f"Chapters {chs[0]}\u2013{chs[-1]}")
    L.append("\\mainmatter")
    last_arc = None
    days_lo, days_hi = 10 ** 9, -1
    cast = set()
    for i, n in enumerate(chs):
        m = load_json(chdir(n) / "meta.json", {}) or {}
        arc = m.get("arc") or {}
        if isinstance(arc, dict):
            key = (arc.get("number"), arc.get("title"))
            if key != last_arc and (arc.get("title") or arc.get("number")):
                sub = arc.get("subtitle", "")
                if i == 0 and n > 1 and is_complete(n - 1):
                    prev = (load_json(chdir(n - 1) / "meta.json", {}) or {}).get("arc") or {}
                    if isinstance(prev, dict) and (prev.get("number"), prev.get("title")) == key:
                        sub = (sub + " (continued)").strip()
                try:
                    num = int(arc.get("number") or 1)
                except (TypeError, ValueError):
                    num = 1
                L.append(f"\\CRarc{{{num}}}{{{esc(arc.get('title', ''))}}}{{{esc(sub)}}}")
                last_arc = key
        L.append(f"\\input{{{(chdir(n) / 'chapter.tex').relative_to(ROOT).as_posix()}}}")
        days = m.get("days") or {}
        try:
            days_lo = min(days_lo, int(days.get("start")))
            days_hi = max(days_hi, int(days.get("end")))
        except (TypeError, ValueError, AttributeError):
            pass
        for s in m.get("characters") or []:
            cast.add(str(s))
    L.append("\\backmatter")
    chars = [c for c in characters() if c["slug"] in cast or "protagonist" in str(c.get("role", "")).lower()]
    if chars:
        L += ["\\chapter*{Dramatis Personae}", "\\markboth{Dramatis Personae}{Dramatis Personae}",
              "\\addcontentsline{toc}{chapter}{Dramatis Personae}"]
        L += [character_tex(c) for c in chars]
    maps = [t for t in (map_tex(d) for d in map_dirs()) if t]
    if maps:
        L += ["\\chapter*{The Atlas}", "\\markboth{The Atlas}{The Atlas}", "\\addcontentsline{toc}{chapter}{The Atlas}"]
        L += maps
    if days_hi >= 0:
        tl = timeline_tex(days_lo, days_hi)
        if tl:
            L += ["\\chapter*{The Reckoning of Days}", "\\markboth{The Reckoning of Days}{The Reckoning of Days}",
                  "\\addcontentsline{toc}{chapter}{The Reckoning of Days}", tl]
    L += _indices()
    L.append("\\end{document}")
    VOLUMES.mkdir(parents=True, exist_ok=True)
    out = VOLUMES / f"vol-{v:03d}.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    return out


LORE_FILES = [("The World", "world.md"), ("Peoples and Tongues", "peoples.md"), ("The Reckoning of Time", "calendar.md"),
              ("Of Power and Its Price", "magic.md"), ("Bestiary", "bestiary.md"), ("Orders, Houses and Factions", "factions.md"),
              ("Glossary", "glossary.md")]


def compendium_master() -> Path:
    meta = book_meta()
    L = _front(meta, "The Compendium", "People, Places and Lore")
    L.append("\\mainmatter")
    chars = characters()
    if chars:
        L += ["\\chapter*{Dramatis Personae}", "\\markboth{Dramatis Personae}{Dramatis Personae}",
              "\\addcontentsline{toc}{chapter}{Dramatis Personae}"]
        L += [character_tex(c) for c in chars]
    maps = [t for t in (map_tex(d) for d in map_dirs()) if t]
    if maps:
        L += ["\\chapter*{The Atlas}", "\\markboth{The Atlas}{The Atlas}", "\\addcontentsline{toc}{chapter}{The Atlas}"]
        L += maps
    for title, fname in LORE_FILES:
        p = ROOT / "bible" / fname
        if p.exists():
            _, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
            L += [f"\\chapter*{{{title}}}", f"\\markboth{{{title}}}{{{title}}}",
                  f"\\addcontentsline{{toc}}{{chapter}}{{{title}}}", md2tex.blocks(body, r"\section*")]
    L.append("\\end{document}")
    out = VOLUMES / "compendium.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    return out


def compile_master(tex: Path, passes: int = 3) -> tuple[bool, Path, str]:
    outdir = BUILD / tex.stem
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("*.ind"):
        f.unlink()
    rc = 0
    for i in range(passes):
        rc = _run_lualatex(tex, outdir, halt=False, timeout=5400)
        if i == 0:
            for idx in outdir.glob("*.idx"):
                subprocess.run(["makeindex", "-q", "-s", str(ROOT / "design" / "chronicle.ist"),
                                "-o", str(idx.with_suffix(".ind")), str(idx)], cwd=outdir,
                               capture_output=True, timeout=600)
    pdf = outdir / f"{tex.stem}.pdf"
    log = outdir / f"{tex.stem}.log"
    errors = [l for l in log.read_text(errors="replace").splitlines() if l.startswith("!")] if log.exists() else ["no log"]
    ok = pdf.exists() and not errors
    return ok, pdf, ("" if ok else log_excerpt(log))


def build_volume(v: int) -> tuple[bool, Path | None, str]:
    tex = volume_master(v)
    if not tex:
        return False, None, "no completed chapters"
    return compile_master(tex)


def build_compendium() -> tuple[bool, Path, str]:
    return compile_master(compendium_master())


def write_meta_tex() -> None:
    meta = book_meta()
    g = BUILD / "gen"
    g.mkdir(parents=True, exist_ok=True)
    (g / "meta.tex").write_text(
        f"\\def\\MetaTitle{{{esc(meta['title'])}}}\n\\def\\MetaSubtitle{{{esc(meta.get('subtitle', ''))}}}\n"
        f"\\def\\MetaTagline{{{esc(meta.get('tagline', ''))}}}\n\\def\\MetaByline{{{esc(meta['byline'])}}}\n",
        encoding="utf-8")


def build_cover() -> tuple[bool, str]:
    write_meta_tex()
    tex = ROOT / "design" / "cover" / "cover.tex"
    if not tex.exists():
        return False, "no cover.tex"
    out = BUILD / "cover"
    rc = _run_lualatex(tex, out, timeout=600)
    return rc == 0, ("" if rc == 0 else log_excerpt(out / "cover.log"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    if a[0] == "chapter":
        ok, err = proof_chapter(int(a[1]))
        print("ok" if ok else err)
    elif a[0] == "volume":
        ok, pdf, err = build_volume(int(a[1]))
        print(pdf if ok else err)
    elif a[0] == "compendium":
        ok, pdf, err = build_compendium()
        print(pdf if ok else err)
    elif a[0] == "maps":
        for k, (ok, msg) in render_maps(force="--force" in a).items():
            print(k, "ok" if ok else msg)
    elif a[0] == "portraits":
        for k, (ok, msg) in render_portraits().items():
            print(k, "ok" if ok else msg)
    elif a[0] == "cover":
        print(build_cover())
