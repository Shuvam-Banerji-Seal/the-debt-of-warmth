"""Small, forgiving Markdown -> LaTeX converter for the author's memory files.

Only the subset the author model is asked to use: headings, paragraphs,
bullet / numbered lists, block quotes, horizontal rules, **bold**, *italic*.
Everything else is escaped so it can never break the build.
"""
from __future__ import annotations

import re

import yaml

_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
    "|": r"\textbar{}",
}


def smart_quotes(s: str) -> str:
    """Straight quotes -> typographic quotes (heuristic, prose-oriented)."""
    s = re.sub(r'(^|[\s(\[{\u2014\u2013-])"', "\\1\u201c", s)
    s = s.replace('"', "\u201d")
    s = re.sub(r"(^|[\s(\[{\u2014\u2013\u201c-])'(?=\w)", "\\1\u2018", s)
    s = s.replace("'", "\u2019")
    return s


def escape(s: str) -> str:
    s = smart_quotes(s)
    return "".join(_SPECIALS.get(c, c) for c in s)


_INLINE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__|\*(?!\s)(.+?)(?<!\s)\*|(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])")


_MACRO_ITALIC = re.compile(r"\\(?:memory|emph|textit|letterhand)\{([^{}]*)\}")
_MACRO_PLAIN = re.compile(r"\\(?:person|place|lore|textsc|sound|inscription|textbf)(?:\[[^\]]*\])?\{([^{}]*)\}")


def unmacro(s: str) -> str:
    """Story macros sometimes leak into the author's Markdown notes: render them."""
    s = _MACRO_ITALIC.sub(lambda m: "*" + m.group(1) + "*", s)
    s = _MACRO_PLAIN.sub(lambda m: m.group(1), s)
    s = re.sub(r"\\dropcap\{([^{}]*)\}\{([^{}]*)\}", r"\1\2", s)
    s = re.sub(r"\\(scenebreak|ldots)\b", lambda m: "…" if m.group(1) == "ldots" else "", s)
    return s


def inline(s: str) -> str:
    s = unmacro(s)
    out, pos = [], 0
    for m in _INLINE.finditer(s):
        out.append(escape(s[pos:m.start()]))
        if m.group(1) or m.group(2):
            out.append(r"\textbf{" + escape(m.group(1) or m.group(2)) + "}")
        else:
            out.append(r"\emph{" + escape(m.group(3) or m.group(4)) + "}")
        pos = m.end()
    out.append(escape(s[pos:]))
    return "".join(out)


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return {}, text
    head = parts[0][3:]
    body = parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
    try:
        data = yaml.safe_load(head) or {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip('"')
    return data, body


def split_sections(body: str, level: int = 2) -> list[tuple[str, str]]:
    """Split on headings of the given level; the preamble has heading ''."""
    marker = "#" * level + " "
    sections, head, buf = [], "", []
    for line in body.splitlines():
        if line.startswith(marker) and not line.startswith(marker + "#"):
            sections.append((head, "\n".join(buf)))
            head, buf = line[len(marker):].strip(), []
        else:
            buf.append(line)
    sections.append((head, "\n".join(buf)))
    return [(h, b) for h, b in sections if h or b.strip()]


def blocks(md: str, heading_cmd: str = r"\CRheading") -> str:
    """Convert a markdown body to LaTeX."""
    lines = md.replace("\r", "").split("\n")
    out: list[str] = []
    para: list[str] = []
    list_kind: str | None = None

    def flush_para():
        nonlocal para
        if para:
            out.append(inline(" ".join(x.strip() for x in para)) + "\n")
            para = []

    def close_list():
        nonlocal list_kind
        if list_kind:
            out.append(r"\end{%s}" % list_kind + "\n")
            list_kind = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            close_list()
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush_para(); close_list()
            out.append(r"\CRrule" + "\n")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para(); close_list()
            out.append(heading_cmd + "{" + inline(m.group(2).strip("# ")) + "}\n")
            continue
        m = re.match(r"^[-*+]\s+(.*)$", stripped)
        n = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if m or n:
            flush_para()
            kind = "itemize" if m else "enumerate"
            if list_kind != kind:
                close_list()
                out.append(r"\begin{%s}[leftmargin=1.4em,itemsep=1pt,topsep=3pt,parsep=0pt]" % kind + "\n")
                list_kind = kind
            out.append(r"\item " + inline((m or n).group(1)) + "\n")
            continue
        if stripped.startswith(">"):
            flush_para(); close_list()
            out.append(r"\begin{quote}\itshape " + inline(stripped.lstrip("> ")) + r"\end{quote}" + "\n")
            continue
        if stripped.startswith("|"):
            flush_para(); close_list()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            out.append(inline(" \u2014 ".join(c for c in cells if c)) + r"\par" + "\n")
            continue
        if list_kind and raw.startswith(("  ", "\t")):
            out[-1] = out[-1].rstrip("\n") + " " + inline(stripped) + "\n"
            continue
        close_list()
        para.append(line)
    flush_para()
    close_list()
    return "\n".join(out)
