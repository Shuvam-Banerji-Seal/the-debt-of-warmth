#!/usr/bin/env python3
"""The atelier: a second, parallel worker that keeps the author busy.

While the press writes chapters, the atelier spends the author's free tokens
on enrichment that never touches the files the chapter loop writes:
  * cameo-plate portraits for every character that lacks one,
  * new maps for places the story has reached,
  * the Codex: in-world documents (songs, laws, prayers, ledgers, letters...)
    printed in the complete book.
It does not commit; the press commits its work with the next chapter step.

  python3 forge/atelier.py run
"""
from __future__ import annotations

import fcntl
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
import orchestrator as press  # noqa: E402

ROOT = build.ROOT
FORGE = ROOT / ".forge"
CODEX = ROOT / "codex"

# The atelier keeps its own state and protects only the press's own sources,
# never STATUS.md or the root PDF (which the press writes and commits itself).
press.PROGRESS = FORGE / "atelier.json"
press.PROTECTED = ["design", "forge", "fonts", "AGENTS.md", "opencode.json", "README.md", ".gitignore"]
press.PROTECT_ROOT_PDFS = False
_orig_log = press.log


def log(msg: str) -> None:
    _orig_log("[atelier] " + msg.strip())


press.log = log

CODEX_KINDS = [
    "a work song sung in the clay yards or on the river", "a prayer or litany of the Return",
    "an extract from the law or the Court's ordinances, with a clerk's marginal notes",
    "a page from a collector's or assessor's ledger, with figures and terse remarks",
    "a children's counting rhyme or skipping game, with notes on how it is played",
    "a healer's or midwife's book of remedies (native practice, with its errors)",
    "a sermon preached at a shrine", "a letter between two people of Sarn",
    "a market price-list and the tolls of the roads", "a soldier's or hunter's field notes on a beast",
    "a chronicle extract from the world's history, as its own historians tell it",
    "a lullaby, lament or drinking song", "a guild's rules of apprenticeship",
    "a traveller's account of a distant land of Sarn", "proverbs and sayings of one people, with glosses",
    "a riddle-contest or tavern story told in the cold months",
]


def codex_count() -> int:
    return len(list(CODEX.glob("*.md"))) if CODEX.exists() else 0


def characters_md_snapshot() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8", errors="replace") for p in (ROOT / "characters").glob("*.md")}


def guard_characters(before: dict[str, str]) -> None:
    """The atelier never edits character sheets. Undo any change it made,
    unless the press itself is in a step that legitimately edits them."""
    st = build.load_json(ROOT / "progress.json", {}) or {}
    if st.get("step") in ("close_a", "close_b", "publish"):
        return
    for name, old in before.items():
        p = ROOT / "characters" / name
        if p.exists() and p.read_text(encoding="utf-8", errors="replace") != old:
            p.write_text(old, encoding="utf-8")
            log(f"undid an edit to characters/{name}")


def task_portraits(state: dict) -> bool:
    slugs = press.portraitless(2)
    if not slugs:
        return False
    log(f"portraits: {', '.join(slugs)}")
    before = characters_md_snapshot()
    press.run_portraits(slugs, state)
    guard_characters(before)
    return True


def task_map(state: dict) -> bool:
    chapters = len(build.completed_chapters())
    maps = len(build.map_dirs())
    if maps >= 3 + chapters // 4:  # keep the Atlas a little ahead of the story, not runaway
        return False
    before = {p.name for p in (ROOT / "atlas").glob("*")}
    log(f"map: the next one the story needs ({maps} so far, {chapters} chapters)")
    detail = ("Choose the place most needed next, from plan/maps-wanted.md and from places the story has reached "
              "(memory/places.md, the latest chapter summaries), that has no map yet in atlas/. A town, a building, "
              "a road, a valley or a district are all fine. Pick a short lowercase-hyphenated slug for its folder "
              "and use that slug wherever this task says <slug>.")
    snap = characters_md_snapshot()
    press.call_author(press.prompt("genesis-map.md", slug="<slug>", title="the next map the Atlas needs", detail=detail),
                      "atelier map", state)
    guard_characters(snap)
    for d in (ROOT / "atlas").glob("*"):
        if d.name in before or not (d / "map.html").exists():
            continue
        for i in range(3):
            ok, err = build.render_map(d, force=True)
            if ok:
                log(f"map {d.name} rendered")
                break
            press.call_author(press.prompt("fix-map.md", slug=d.name, error=err[-1500:]), f"atelier fix map {d.name}", state)
    return True


def task_codex(state: dict) -> bool:
    chapters = len(build.completed_chapters())
    n = codex_count()
    if n >= 6 + 2 * chapters:
        return False
    kind = CODEX_KINDS[n % len(CODEX_KINDS)]
    CODEX.mkdir(exist_ok=True)
    existing = ", ".join(sorted(p.stem for p in CODEX.glob("*.md"))) or "none yet"
    task = f"""TASK: THE CODEX. Write one in-world document of Sarn.

Read design/STYLE-REFERENCE.md and bible/voice.md (the voice), then whatever bible files, memory/places.md and recent chapter summaries (book/chapters/*/summary.md) this document touches. Existing codex entries are: {existing}. Do not repeat them.

Write **{kind}** as `codex/<slug>.md`, with a short lowercase-hyphenated slug. It is printed in the complete book as part of "The Codex of Sarn", so write it from *inside* the world: an in-world author, in-world idiom, the texture of real use (stains, marginal notes, a clerk's correction). It must be consistent with all canon. Reveal only what an in-world writer could know: never the secrets in bible/premise.md, plan/ or the private sections of character sheets.

Format: YAML front matter between --- lines with `title:` (in-world), `kind:`, `provenance:` (who wrote it, where, when in Y.H., how it survives) and `relates_to:` (places, people or lore terms), then the document itself in Markdown, 700–2,500 words. Use verse lines for songs, and lists or tables for ledgers and laws. Make it beautiful, specific and strange.

Create only that one file and edit nothing else. Reply with one line: the slug."""
    before = {p.name for p in CODEX.glob("*.md")}
    snap = characters_md_snapshot()
    press.call_author(task, f"atelier codex {n + 1}", state)
    guard_characters(snap)
    new = [p for p in CODEX.glob("*.md") if p.name not in before]
    for p in new:
        fm, body = build.md2tex.parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
        if not fm.get("title") or len(body.split()) < 300:
            log(f"codex {p.name} is malformed or thin; asking for a repair")
            press.call_author(press.prompt("fix-files.md", what=f"codex {p.name}",
                problems=f"- `codex/{p.name}` needs YAML front matter with title, kind, provenance, relates_to, and a body of 700–2,500 words."),
                f"atelier fix codex {p.stem}", state)
        else:
            log(f"codex: {fm.get('title')} ({len(body.split())} words)")
    return bool(new)


TASKS = [task_portraits, task_codex, task_map, task_codex, task_portraits]


def main() -> None:
    FORGE.mkdir(exist_ok=True)
    lock = open(FORGE / "atelier.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("the atelier is already running", file=sys.stderr)
        sys.exit(1)
    state = build.load_json(press.PROGRESS, {}) or {}
    state.setdefault("calls", 0)
    state.setdefault("failures_in_row", 0)
    state.setdefault("turn", 0)
    log("atelier opening")
    while not press.STOP:
        idle = True
        for _ in range(len(TASKS)):
            t = TASKS[state["turn"] % len(TASKS)]
            state["turn"] += 1
            press.save_state(state)
            try:
                if t(state):
                    idle = False
                    break
            except SystemExit:
                raise
            except Exception as e:
                log(f"error in {t.__name__}: {type(e).__name__}: {e}")
                press.sleep_interruptible(60)
        if idle:
            press.sleep_interruptible(600)  # everything is caught up with the story; wait for new chapters
    log("atelier closing")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        main()
    else:
        print(__doc__)
