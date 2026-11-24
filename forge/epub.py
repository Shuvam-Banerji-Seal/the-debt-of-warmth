#!/usr/bin/env python3
"""EPUB 3 edition of the chronicle, built straight from the author's sources.

Scene files use a small, known LaTeX vocabulary (design/AUTHOR-API.md), so they
are converted to XHTML directly; memory/lore files are Markdown. The result has
the cover, frontispiece, every chapter with its colour plate and day marks
(navigable), the chronicle boxes, the cast with art, the atlas, the Codex, the
reckoning of days and the lore.

  python3 forge/epub.py            # -> build/epub/<Title>.epub
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import md2tex  # noqa: E402

ROOT = build.ROOT
OUT = build.BUILD / "epub"

# --------------------------------------------------------------- LaTeX -> XHTML
def _esc(s: str) -> str:
    return html.escape(s, quote=False)


INLINE1 = {
    "emph": "<em>{}</em>", "textit": "<em>{}</em>", "memory": "<em class=\"memory\">{}</em>",
    "textbf": "<strong>{}</strong>", "textsc": "<span class=\"sc\">{}</span>", "sound": "<span class=\"sc\">{}</span>",
    "inscription": "<span class=\"inscr\">{}</span>",
}
PLAIN1 = {"person", "place", "lore", "mbox", "text"}
SYMBOLS = {"ldots": "\u2026", "dots": "\u2026", "textperiodcentered": "\u00b7", "textemdash": "\u2014",
           "textendash": "\u2013", "enspace": "\u2002", "quad": "\u2003", "noindent": "", "par": "\n\n",
           "smallskip": "", "medskip": "", "bigskip": "", "S": "\u00a7", "P": "\u00b6", "ignorespaces": ""}
BLOCK = "\x00"  # marks a chunk that is already block-level HTML


class TexHtml:
    def __init__(self, day_ids: list | None = None):
        self.day_ids = day_ids if day_ids is not None else []

    def convert(self, s: str) -> str:
        self.s, self.i = s, 0
        return self._run(stop=None)

    def _arg(self) -> str:
        """Parse a {...} group at the current position (after whitespace) and convert it."""
        while self.i < len(self.s) and self.s[self.i] in " \t\n":
            self.i += 1
        if self.i < len(self.s) and self.s[self.i] == "{":
            self.i += 1
            return self._run(stop="}")
        if self.i < len(self.s):  # single-token argument
            ch = self.s[self.i]
            self.i += 1
            return _esc(ch)
        return ""

    def _opt(self) -> str | None:
        j = self.i
        while j < len(self.s) and self.s[j] in " \t":
            j += 1
        if j < len(self.s) and self.s[j] == "[":
            k = self.s.find("]", j)
            if k != -1:
                self.i = k + 1
                return self.s[j + 1:k]
        return None

    def _run(self, stop: str | None) -> str:
        out = []
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if stop and c == stop:
                self.i += 1
                break
            if c == "\\":
                out.append(self._command())
                continue
            if c == "{":
                self.i += 1
                out.append(self._run(stop="}"))
                continue
            if c == "}":
                self.i += 1
                continue
            if c == "%":
                nl = s.find("\n", self.i)
                self.i = len(s) if nl == -1 else nl
                continue
            if s.startswith("---", self.i):
                out.append("\u2014"); self.i += 3; continue
            if s.startswith("--", self.i):
                out.append("\u2013"); self.i += 2; continue
            if s.startswith("``", self.i):
                out.append("\u201c"); self.i += 2; continue
            if s.startswith("''", self.i):
                out.append("\u201d"); self.i += 2; continue
            if c == "`":
                out.append("\u2018"); self.i += 1; continue
            if c == "'":
                out.append("\u2019"); self.i += 1; continue
            if c == "~":
                out.append("\u00a0"); self.i += 1; continue
            out.append(_esc(c))
            self.i += 1
        return "".join(out)

    def _command(self) -> str:
        s = self.s
        self.i += 1
        if self.i >= len(s):
            return ""
        c = s[self.i]
        if not c.isalpha():
            self.i += 1
            if c == "\\":
                return "<br/>"
            return {"%": "%", "&": "&amp;", "#": "#", "$": "$", "_": "_", "{": "{", "}": "}",
                    " ": " ", ",": "\u2009", "'": "", "-": ""}.get(c, _esc(c))
        m = re.match(r"[A-Za-z@]+\*?", s[self.i:])
        name = m.group(0).rstrip("*")
        self.i += len(m.group(0))
        if name in INLINE1:
            return INLINE1[name].format(self._arg())
        if name in PLAIN1:
            self._opt()
            return self._arg()
        if name in SYMBOLS:
            return SYMBOLS[name]
        if name == "dropcap":
            a, b = self._arg(), self._arg()
            return f"<span class=\"dropcap\">{a}</span><span class=\"sc\">{b}</span>"
        if name == "daymark":
            n, date = self._arg(), self._arg()
            did = f"day-{re.sub(r'[^0-9]', '', n) or 'x'}-{len(self.day_ids)}"
            self.day_ids.append((did, f"Day {n}"))
            date_html = f"<p class=\"daydate\">{date}</p>" if date.strip() else ""
            return (f"\n\n{BLOCK}<div class=\"daymark\" id=\"{did}\"><p class=\"day\">\u2014 Day {n} \u2014</p>"
                    f"{date_html}</div>\n\n")
        if name == "scenebreak":
            return f"\n\n{BLOCK}<p class=\"break\">\u2766</p>\n\n"
        if name == "letterhand":
            return f"\n\n{BLOCK}<blockquote class=\"letter\"><p>{self._arg()}</p></blockquote>\n\n"
        if name == "begin":
            env = self._arg()
            end = f"\\end{{{env}}}"
            j = s.find(end, self.i)
            inner = s[self.i: j if j != -1 else len(s)]
            self.i = len(s) if j == -1 else j + len(end)
            body = TexHtml(self.day_ids).convert(inner)
            if env == "verseblock":
                lines = [ln.strip() for ln in body.replace("\n\n", "<br/>").split("\n")]
                return f"\n\n{BLOCK}<div class=\"verse\"><p>{' '.join(lines)}</p></div>\n\n"
            if env in ("quote", "quotation"):
                return f"\n\n{BLOCK}<blockquote>{paragraphs(body)}</blockquote>\n\n"
            if env == "center":
                return f"\n\n{BLOCK}<div class=\"center\">{paragraphs(body)}</div>\n\n"
            if env in ("itemize", "enumerate"):
                items = [x.strip() for x in re.split(r"\\item\b", inner)[1:]]
                tag = "ul" if env == "itemize" else "ol"
                lis = "".join(f"<li>{TexHtml(self.day_ids).convert(x)}</li>" for x in items)
                return f"\n\n{BLOCK}<{tag}>{lis}</{tag}>\n\n"
            return body
        if name in ("end", "item"):
            return ""
        # unknown command: keep the text of its argument, if any
        self._opt()
        if self.i < len(s) and s[self.i] == "{":
            return self._arg()
        return ""


def paragraphs(text: str, first_class: str | None = None) -> str:
    out = []
    for chunk in re.split(r"\n\s*\n", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith(BLOCK):
            out.append(chunk.replace(BLOCK, ""))
            continue
        chunk = chunk.replace(BLOCK, "")
        cls = ""
        if "class=\"dropcap\"" in chunk:
            cls = " class=\"first\""
        elif first_class and not out:
            cls = f" class=\"{first_class}\""
        out.append(f"<p{cls}>{' '.join(chunk.split())}</p>")
    return "\n".join(out)


def scene_html(path: Path, day_ids: list) -> str:
    return paragraphs(TexHtml(day_ids).convert(path.read_text(encoding="utf-8", errors="replace")))


# ----------------------------------------------------------- Markdown -> XHTML
def md_inline(s: str) -> str:
    s = md2tex.unmacro(s)
    out, pos = [], 0
    for m in md2tex._INLINE.finditer(s):
        out.append(_esc(md2tex.smart_quotes(s[pos:m.start()])))
        if m.group(1) or m.group(2):
            out.append("<strong>" + _esc(md2tex.smart_quotes(m.group(1) or m.group(2))) + "</strong>")
        else:
            out.append("<em>" + _esc(md2tex.smart_quotes(m.group(3) or m.group(4))) + "</em>")
        pos = m.end()
    out.append(_esc(md2tex.smart_quotes(s[pos:])))
    return "".join(out)


def md_html(md: str, h: int = 3) -> str:
    out, para, lst = [], [], None

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + md_inline(" ".join(x.strip() for x in para)) + "</p>")
            para = []

    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None

    for raw in md.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            flush(); close(); continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line):
            flush(); close(); out.append("<p class=\"break\">\u2766</p>"); continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush(); close()
            lvl = min(6, h + max(0, len(m.group(1)) - 2))
            out.append(f"<h{lvl}>{md_inline(m.group(2).strip('# '))}</h{lvl}>"); continue
        m = re.match(r"^[-*+]\s+(.*)$", line)
        n = re.match(r"^\d+[.)]\s+(.*)$", line)
        if m or n:
            flush()
            kind = "ul" if m else "ol"
            if lst != kind:
                close(); out.append(f"<{kind}>"); lst = kind
            out.append(f"<li>{md_inline((m or n).group(1))}</li>"); continue
        if line.startswith(">"):
            flush(); close(); out.append(f"<blockquote><p>{md_inline(line.lstrip('> '))}</p></blockquote>"); continue
        if line.startswith("|"):
            flush(); close()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            out.append("<p class=\"row\">" + " \u2014 ".join(md_inline(c) for c in cells if c) + "</p>"); continue
        close()
        para.append(line)
    flush(); close()
    return "\n".join(out)


# ------------------------------------------------------------------ packaging
CSS = """
@font-face { font-family: "EB Garamond"; src: url(../fonts/EBGaramond-Regular.otf); }
@font-face { font-family: "EB Garamond"; font-style: italic; src: url(../fonts/EBGaramond-Italic.otf); }
@font-face { font-family: "EB Garamond"; font-weight: bold; src: url(../fonts/EBGaramond-SemiBold.otf); }
@font-face { font-family: "Cinzel Decorative"; src: url(../fonts/CinzelDecorative-Regular.ttf); }
@font-face { font-family: "Cinzel"; src: url(../fonts/Cinzel-Regular.ttf); }
body { font-family: "EB Garamond", Garamond, Georgia, serif; line-height: 1.45; color: #2b1b0e; background-color: #f3e7cb; margin: 0 4%; }
p { margin: 0; text-indent: 1.25em; text-align: justify; hyphens: auto; -epub-hyphens: auto; }
p.first, p.noindent, .daymark + p, .break + p, .chapter-head + p { text-indent: 0; }
h1, h2, h3, h4 { font-family: "Cinzel Decorative", "Cinzel", serif; color: #7e1f14; font-weight: normal; text-align: center; page-break-after: avoid; }
h1 { font-size: 1.8em; margin: 1.2em 0 0.4em; } h2 { font-size: 1.5em; margin: 0.4em 0; } h3 { font-size: 1.15em; margin: 1.1em 0 0.4em; } h4 { font-size: 1em; margin: 0.9em 0 0.3em; }
.sc { font-variant: small-caps; letter-spacing: 0.04em; }
.inscr { font-family: "Cinzel", serif; letter-spacing: 0.12em; font-size: 0.9em; }
.dropcap { float: left; font-family: "Cinzel Decorative", serif; color: #7e1f14; font-size: 3.1em; line-height: 0.85; margin: 0.06em 0.08em 0 0; }
.break { text-align: center; text-indent: 0; color: #9a7432; margin: 0.8em 0; font-size: 1.2em; }
.daymark { margin: 1.6em 0 0.8em; text-align: center; page-break-after: avoid; }
.daymark .day { text-indent: 0; text-align: center; font-family: "Cinzel", serif; letter-spacing: 0.25em; color: #7e1f14; font-size: 0.85em; }
.daymark .daydate { text-indent: 0; text-align: center; font-style: italic; color: #6e5b42; font-size: 0.9em; }
.chapter-head { text-align: center; margin: 1.5em 0 1.2em; page-break-before: always; }
.chap-num { text-indent: 0; text-align: center; font-family: "Cinzel", serif; letter-spacing: 0.3em; color: #6e5b42; font-size: 0.8em; }
.chap-n { text-indent: 0; text-align: center; color: #7e1f14; font-size: 2em; }
.when { text-indent: 0; text-align: center; font-style: italic; color: #6e5b42; font-size: 0.85em; margin-top: 0.3em; }
.epigraph { margin: 1.2em 12% 1.5em; text-align: center; }
.epigraph p { text-indent: 0; text-align: center; font-style: italic; }
.epigraph .attr { font-style: normal; font-variant: small-caps; color: #6e5b42; font-size: 0.85em; margin-top: 0.3em; }
.verse { margin: 1em 10%; font-style: italic; text-align: center; } .verse p { text-indent: 0; text-align: center; }
blockquote { margin: 1em 6%; font-style: italic; } blockquote p { text-indent: 0; }
.chronicle { border: 1px solid #9a7432; background-color: #ecdcb8; padding: 0.8em 1em; margin: 2em 0 1em; page-break-inside: avoid; }
.chronicle .ctitle { text-indent: 0; text-align: center; font-family: "Cinzel", serif; letter-spacing: 0.15em; color: #7e1f14; font-size: 0.8em; margin-bottom: 0.5em; }
.chronicle p { font-size: 0.92em; }
.plate { page-break-before: always; page-break-after: always; text-align: center; margin: 0; }
.plate img { max-width: 100%; max-height: 95vh; }
.plate .caption { text-indent: 0; text-align: center; font-style: italic; color: #6e5b42; font-size: 0.85em; margin-top: 0.4em; }
.portrait { text-align: center; margin: 0.5em 0 1em; } .portrait img { max-width: 70%; max-height: 60vh; }
.field { text-indent: 0; font-size: 0.92em; } .field .k { font-family: "Cinzel", serif; color: #7e1f14; font-size: 0.8em; letter-spacing: 0.1em; }
.epithet, .subtitle { text-indent: 0; text-align: center; font-style: italic; color: #6e5b42; }
.titlepage { text-align: center; margin-top: 25%; } .titlepage p { text-indent: 0; text-align: center; }
.center p, .center { text-align: center; text-indent: 0; }
.mapfig { text-align: center; page-break-before: always; } .mapfig img { max-width: 100%; }
.row { text-indent: 0; }
"""


def xhtml(title: str, body: str, etype: str = "bodymatter") -> str:
    return ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<!DOCTYPE html>\n"
            "<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\" lang=\"en\" xml:lang=\"en\">\n"
            f"<head><meta charset=\"utf-8\"/><title>{_esc(title)}</title>"
            "<link rel=\"stylesheet\" type=\"text/css\" href=\"../css/book.css\"/></head>\n"
            f"<body epub:type=\"{etype}\">\n{body}\n</body>\n</html>\n")


class Book:
    def __init__(self):
        self.files: dict[str, bytes] = {}   # path inside OEBPS -> bytes
        self.spine: list[str] = []
        self.nav: list[tuple[str, str, list]] = []  # (label, href, children)

    def add(self, path: str, data, spine=False):
        self.files[path] = data.encode("utf-8") if isinstance(data, str) else data
        if spine:
            self.spine.append(path)

    def image(self, src: Path, name: str, fmt: str | None = None, max_h: int = 1600) -> str | None:
        """Add an image (converted for e-readers); returns its path relative to text/."""
        try:
            from PIL import Image
            if src.suffix == ".svg":
                self.add(f"images/{name}.svg", src.read_bytes())
                return f"../images/{name}.svg"
            im = Image.open(src)
            im.thumbnail((max_h * 2, max_h))
            from io import BytesIO
            buf = BytesIO()
            if (fmt or ("webp" if im.mode in ("RGBA", "LA", "P") else "jpeg")) == "webp":
                im.convert("RGBA").save(buf, "WEBP", quality=86, method=5)
                ext = "webp"
            else:
                im.convert("RGB").save(buf, "JPEG", quality=86, optimize=True, progressive=True)
                ext = "jpg"
            self.add(f"images/{name}.{ext}", buf.getvalue())
            return f"../images/{name}.{ext}"
        except Exception:
            return None


MEDIA = {".xhtml": "application/xhtml+xml", ".css": "text/css", ".jpg": "image/jpeg", ".png": "image/png",
         ".webp": "image/webp", ".svg": "image/svg+xml", ".otf": "font/otf", ".ttf": "font/ttf",
         ".ncx": "application/x-dtbncx+xml"}


def make_epub() -> Path:
    meta = build.book_meta()
    title = meta["title"]
    B = Book()
    B.add("css/book.css", CSS)
    for f in ("EBGaramond-Regular.otf", "EBGaramond-Italic.otf", "EBGaramond-SemiBold.otf",
              "CinzelDecorative-Regular.ttf", "Cinzel-Regular.ttf"):
        B.add(f"fonts/{f}", (ROOT / "fonts" / f).read_bytes())

    # cover
    cover_pdf = build.BUILD / "cover" / "cover.pdf"
    cover_img = None
    if cover_pdf.exists():
        tmp = OUT / "cover.jpg"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["magick", "-density", "260", f"{cover_pdf}[0]", "-quality", "88", str(tmp)], capture_output=True)
        if tmp.exists():
            B.add("images/cover.jpg", tmp.read_bytes())
            cover_img = "images/cover.jpg"
            B.add("text/cover.xhtml", xhtml("Cover", f"<div class=\"plate\"><img src=\"../{cover_img}\" alt=\"{_esc(title)}\"/></div>", "cover"), spine=True)
    # frontispiece
    fsrc = build._art_source(build.ART / "frontispiece")
    if fsrc:
        img = B.image(fsrc, "frontispiece", "jpeg")
        if img:
            B.add("text/frontispiece.xhtml", xhtml("Frontispiece", f"<div class=\"plate\"><img src=\"{img}\" alt=\"Frontispiece\"/></div>", "frontmatter"), spine=True)
    # title page + colophon
    chs = build.completed_chapters()
    B.add("text/title.xhtml", xhtml(title,
        f"<div class=\"titlepage\"><h1>{_esc(title)}</h1><p class=\"subtitle\">{md_inline(meta.get('subtitle', ''))}</p>"
        f"<p class=\"break\">\u2766</p><p class=\"subtitle\">The Complete Chronicle</p>"
        f"<p class=\"subtitle\">{'Chapters 1\u2013' + str(chs[-1]) if chs else ''} \u00b7 as set on {datetime.now():%-d %B %Y}</p>"
        f"<p class=\"break\">\u2766</p><p class=\"sc\">{_esc(meta.get('byline', ''))}</p></div>", "titlepage"), spine=True)
    B.add("text/colophon.xhtml", xhtml("Colophon",
        "<div class=\"center\"><p><em>This chronicle is written, chapter by chapter and without end, by the language model "
        "hy4-flash-free, working through OpenCode. The world, its people, its maps, the Codex and every chapter ornament are its own.</em></p>"
        "<p class=\"break\">\u2766</p><p><em>The book design, cover and press were made by Claude, which also wrote the prompts for the "
        "light-novel illustrations (painted by an OpenAI image model) but writes no word of the story.</em></p>"
        "<p class=\"break\">\u2766</p><p>A work of fiction for adult readers. It contains violence, cruelty, slavery and other darkness of its invented world.</p></div>",
        "colophon"), spine=True)
    B.nav.append(("Title", "text/title.xhtml", []))

    # chapters
    last_arc = None
    arc_nav = None
    for n in chs:
        d = build.chdir(n)
        m = build.load_json(d / "meta.json", {}) or {}
        arc = m.get("arc") or {}
        key = (arc.get("number"), arc.get("title")) if isinstance(arc, dict) else None
        if key and key != last_arc:
            ahref = f"text/arc-{n:04d}.xhtml"
            B.add(ahref, xhtml(arc.get("title", ""),
                f"<div class=\"titlepage\"><p class=\"chap-num\">The {_esc(str(arc.get('number', '')))} Arc</p>"
                f"<h1>{md_inline(str(arc.get('title', '')))}</h1><p class=\"subtitle\">{md_inline(str(arc.get('subtitle', '')))}</p></div>", "part"), spine=True)
            arc_nav = (f"Arc {arc.get('number', '')}: {arc.get('title', '')}", ahref, [])
            B.nav.append(arc_nav)
            last_arc = key
        body = []
        psrc = build._art_source(build.ART / "chapters" / f"ch-{n:04d}")
        if psrc:
            img = B.image(psrc, f"plate-ch-{n:04d}", "jpeg")
            cap = build.plate_caption(n)
            if img:
                body.append(f"<div class=\"plate\"><img src=\"{img}\" alt=\"{_esc(cap or 'Illustration')}\"/>"
                            + (f"<p class=\"caption\">{_esc(cap)}</p>" if cap else "") + "</div>")
        epi = m.get("epigraph") or {}
        if isinstance(epi, str):
            epi = {"text": epi}
        when = " \u00b7 ".join(x for x in (m.get("when", ""), m.get("where", "")) if x)
        body.append(f"<div class=\"chapter-head\" id=\"ch-{n}\"><p class=\"chap-num\">Chapter</p><p class=\"chap-n\">{n}</p>"
                    f"<h2>{md_inline(m.get('title', f'Chapter {n}'))}</h2><p class=\"when\">{md_inline(when)}</p></div>")
        if epi.get("text"):
            body.append(f"<div class=\"epigraph\"><p>{md_inline(epi['text'])}</p>"
                        + (f"<p class=\"attr\">\u2014 {md_inline(epi.get('attribution', ''))}</p>" if epi.get("attribution") else "") + "</div>")
        days: list = []
        for i, sf in enumerate(build.scene_files(n)):
            text = sf.read_text(encoding="utf-8", errors="replace")
            if i and not text.lstrip().startswith("\\daymark"):
                body.append("<p class=\"break\">\u2766</p>")
            body.append(scene_html(sf, days))
        body.append("<p class=\"break\">\u2766 \u2766 \u2766</p>")
        sm = d / "summary.md"
        if sm.exists():
            _, sb = md2tex.parse_front_matter(sm.read_text(encoding="utf-8", errors="replace"))
            chron = next((t for h, t in md2tex.split_sections(sb) if "chronicle" in h.lower()), "")
            if chron.strip():
                body.append(f"<aside class=\"chronicle\" epub:type=\"aside\"><p class=\"ctitle\">The Chronicle of Chapter {n}</p>{md_html(chron)}</aside>")
        href = f"text/ch-{n:04d}.xhtml"
        B.add(href, xhtml(f"Chapter {n}: {m.get('title', '')}", "\n".join(body)), spine=True)
        entry = (f"{n}. {m.get('title', '')}", f"{href}#ch-{n}", [(lab, f"{href}#{did}", []) for did, lab in days])
        (arc_nav[2] if arc_nav else B.nav).append(entry)

    # back matter
    chars = build.characters()
    if chars:
        parts = ["<h1>Dramatis Personae</h1>"]
        sub = []
        for c in chars:
            cid = f"c-{c['slug']}"
            parts.append(f"<section id=\"{cid}\" class=\"character\"><h2>{_esc(str(c['name']))}</h2>")
            if c.get("epithet"):
                parts.append(f"<p class=\"epithet\">{md_inline(str(c['epithet']))}</p>")
            src = build._art_source(build.ART / "characters" / c["slug"]) or (
                ROOT / "characters" / f"{c['slug']}.svg" if (ROOT / "characters" / f"{c['slug']}.svg").exists() else None)
            if src:
                img = B.image(src, f"char-{c['slug']}", "webp" if src.suffix != ".svg" else None, max_h=1400)
                if img:
                    parts.append(f"<div class=\"portrait\"><img src=\"{img}\" alt=\"{_esc(str(c['name']))}\"/></div>")
            for label, keys in [("Also called", ("aliases",)), ("Role", ("role",)), ("Born", ("born",)),
                                ("Origin", ("origin",)), ("Allegiance", ("affiliation",)), ("Status", ("status",))]:
                v = next((c.get(k) for k in keys if c.get(k)), None)
                if v:
                    v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
                    parts.append(f"<p class=\"field\"><span class=\"k\">{label.upper()}</span> {md_inline(v)}</p>")
            for head, text in md2tex.split_sections(c["_body"]):
                if head and any(w in head.lower() for w in build.PRIVATE_SECTION_WORDS):
                    continue
                if head:
                    parts.append(f"<h3>{md_inline(head)}</h3>")
                parts.append(md_html(text, 4))
            parts.append("</section>")
            sub.append((str(c["name"]), f"text/personae.xhtml#{cid}", []))
        B.add("text/personae.xhtml", xhtml("Dramatis Personae", "\n".join(parts), "backmatter"), spine=True)
        B.nav.append(("Dramatis Personae", "text/personae.xhtml", sub))
    maps = []
    for d in build.map_dirs():
        jpg = build.BUILD / "atlas" / f"{d.name}.jpg"
        png = build.BUILD / "atlas" / f"{d.name}.png"
        src = jpg if jpg.exists() else png if png.exists() else None
        if not src:
            continue
        mm = build.load_json(d / "meta.json", {}) or {}
        img = B.image(src, f"map-{d.name}", "jpeg", max_h=2000)
        if img:
            maps.append(f"<div class=\"mapfig\" id=\"m-{d.name}\"><h2>{md_inline(mm.get('title', d.name))}</h2><img src=\"{img}\" alt=\"{_esc(mm.get('title', d.name))}\"/>"
                        f"<p class=\"when\">{md_inline(mm.get('caption', ''))}</p></div>")
    if maps:
        B.add("text/atlas.xhtml", xhtml("The Atlas", "<h1>The Atlas</h1>" + "\n".join(maps), "backmatter"), spine=True)
        B.nav.append(("The Atlas", "text/atlas.xhtml", []))
    codex = []
    for p in sorted((ROOT / "codex").glob("*.md")):
        fm, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
        if fm.get("title") and len(body.split()) >= 200:
            prov = " \u00b7 ".join(str(x) for x in (fm.get("kind", ""), fm.get("provenance", "")) if x)
            codex.append(f"<section id=\"x-{p.stem}\"><h2>{md_inline(str(fm['title']))}</h2><p class=\"when\">{md_inline(prov)}</p>{md_html(body, 3)}</section>")
    if codex:
        B.add("text/codex.xhtml", xhtml("The Codex of Sarn", "<h1>The Codex of Sarn</h1>" + "\n".join(codex), "backmatter"), spine=True)
        B.nav.append(("The Codex of Sarn", "text/codex.xhtml", []))
    tl = build.timeline_entries()
    if tl and chs:
        rows = "".join(f"<p class=\"field\"><span class=\"k\">DAY {d}</span> {md_inline(t.replace('|', ' \u2014 '))}</p>" for d, t in tl)
        B.add("text/days.xhtml", xhtml("The Reckoning of Days", "<h1>The Reckoning of Days</h1>" + rows, "backmatter"), spine=True)
        B.nav.append(("The Reckoning of Days", "text/days.xhtml", []))
    for i, (lt, fname) in enumerate(build.LORE_FILES):
        p = ROOT / "bible" / fname
        if p.exists():
            _, body = md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
            href = f"text/lore-{i}.xhtml"
            B.add(href, xhtml(lt, f"<h1>{_esc(lt)}</h1>" + md_html(body, 2), "backmatter"), spine=True)
            B.nav.append((lt, href, []))

    # navigation
    def ol(items):
        return "<ol>" + "".join(
            f"<li><a href=\"{h.replace('text/', '')}\">{_esc(lab)}</a>{ol(ch) if ch else ''}</li>" for lab, h, ch in items) + "</ol>"
    B.add("text/nav.xhtml", xhtml("Contents", f"<nav epub:type=\"toc\" id=\"toc\"><h1>Contents</h1>{ol(B.nav)}</nav>", "frontmatter"))
    ident = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "chronicle:" + title))
    pts, k = [], 0
    def ncx(items):
        nonlocal k
        out = []
        for lab, h, ch in items:
            k += 1
            out.append(f"<navPoint id=\"np{k}\" playOrder=\"{k}\"><navLabel><text>{_esc(lab)}</text></navLabel>"
                       f"<content src=\"{h}\"/>{ncx(ch)}</navPoint>")
        return "".join(out)
    B.add("toc.ncx", f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<ncx xmlns=\"http://www.daisy.org/z3986/2005/ncx/\" version=\"2005-1\">"
          f"<head><meta name=\"dtb:uid\" content=\"{ident}\"/></head><docTitle><text>{_esc(title)}</text></docTitle>"
          f"<navMap>{ncx(B.nav)}</navMap></ncx>")

    # validate well-formedness of every XML document before packaging
    for path, data in B.files.items():
        if path.endswith((".xhtml", ".ncx")):
            ElementTree.fromstring(data)

    manifest, ids = [], {}
    for i, path in enumerate(sorted(B.files)):
        iid = f"i{i}"
        ids[path] = iid
        props = []
        if path == "text/nav.xhtml":
            props.append("nav")
        if path == cover_img:
            props.append("cover-image")
        pa = f" properties=\"{' '.join(props)}\"" if props else ""
        manifest.append(f"<item id=\"{iid}\" href=\"{path}\" media-type=\"{MEDIA[Path(path).suffix]}\"{pa}/>")
    spine = "".join(f"<itemref idref=\"{ids[p]}\"/>" for p in B.spine)
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    opf = (f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<package xmlns=\"http://www.idpf.org/2007/opf\" version=\"3.0\" unique-identifier=\"bookid\">"
           f"<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\"><dc:identifier id=\"bookid\">{ident}</dc:identifier>"
           f"<dc:title>{_esc(title)}</dc:title><dc:creator>{_esc(meta.get('byline', 'Hy4 Flash').replace('Written by ', ''))}</dc:creator>"
           f"<dc:language>en</dc:language><dc:description>{_esc(meta.get('tagline', ''))}</dc:description>"
           f"<meta property=\"dcterms:modified\">{modified}</meta>"
           + (f"<meta name=\"cover\" content=\"{ids[cover_img]}\"/>" if cover_img else "") +
           f"</metadata><manifest>{''.join(manifest)}</manifest><spine toc=\"{ids['toc.ncx']}\">{spine}</spine></package>")
    ElementTree.fromstring(opf.encode())

    OUT.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")
    out = OUT / f"{slug}.epub"
    tmp = out.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   "<?xml version=\"1.0\"?><container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">"
                   "<rootfiles><rootfile full-path=\"OEBPS/content.opf\" media-type=\"application/oebps-package+xml\"/></rootfiles></container>",
                   compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        for path, data in B.files.items():
            z.writestr(f"OEBPS/{path}", data, compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(out)
    return out


if __name__ == "__main__":
    print(make_epub())
