#!/usr/bin/env python3
"""The press: drives the author model (OpenCode, hy4-flash-free) forever.

The orchestrator never writes story text. It:
  * hands the author one well-scoped task at a time (genesis, plan, scene,
    close, decoration, consolidation, maps, portraits),
  * validates every result and asks the author to repair what is broken,
  * protects finished chapters and the book design from accidental edits,
  * typesets, commits, pushes and publishes the PDFs,
  * resumes exactly where it stopped after a crash, reboot or rate limit.

Usage:
  python3 forge/orchestrator.py run            # the endless loop
  python3 forge/orchestrator.py status         # print progress
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = build.ROOT
FORGE = ROOT / ".forge"
LOGS = FORGE / "logs"
PROGRESS = ROOT / "progress.json"
PROMPTS = ROOT / "forge" / "prompts"
MODEL = os.environ.get("CHRONICLE_MODEL", "opencode-go/hy4-flash-free")
OPENCODE = shutil.which("opencode") or "/usr/bin/opencode"
CALL_TIMEOUT = int(os.environ.get("CHRONICLE_CALL_TIMEOUT", "5400"))
BUILD_EVERY = int(os.environ.get("CHRONICLE_BUILD_EVERY", "5"))
CONSOLIDATE_EVERY = 10
PROTECTED = ["design", "forge", "fonts", "AGENTS.md", "opencode.json", "README.md", ".gitignore",
             "pdf", "STATUS.md"]
TRANSIENT = re.compile(r"rate.?limit|too many requests|\b429\b|quota|overloaded|temporarily unavailable|"
                       r"\b50[234]\b|bad gateway|service unavailable|ECONNRESET|ETIMEDOUT|socket hang up|"
                       r"database is locked|concurrent requests|insufficient|credit", re.I)

STOP = False


def _sig(*_):
    global STOP
    STOP = True
    log("signal received: finishing current call, then stopping")


signal.signal(signal.SIGTERM, _sig)
signal.signal(signal.SIGINT, _sig)


# ------------------------------------------------------------------ utils
def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    FORGE.mkdir(exist_ok=True)
    with open(FORGE / "orchestrator.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(*args, check=False) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr}")
    return p.stdout


def words(path: Path) -> int:
    try:
        t = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return 0
    if path.suffix == ".tex":
        return build.word_count_tex(t)
    return len(t.split())


def prompt(name: str, **kw) -> str:
    return Template((PROMPTS / name).read_text(encoding="utf-8")).safe_substitute(**kw)


def sleep_interruptible(seconds: float) -> None:
    end = time.time() + seconds
    while time.time() < end and not STOP:
        time.sleep(min(5, end - time.time()))


# ------------------------------------------------------------------ state
DEFAULT_STATE = {"genesis_done": [], "chapter": 1, "step": "plan", "scene": 1,
                 "consolidated_through": 0, "built": {}, "calls": 0, "failures_in_row": 0,
                 "started": None, "words_total": 0}


def load_state() -> dict:
    s = build.load_json(PROGRESS, None) or {}
    out = dict(DEFAULT_STATE)
    out.update(s)
    return out


def save_state(s: dict) -> None:
    tmp = PROGRESS.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=2), encoding="utf-8")
    tmp.replace(PROGRESS)


# ------------------------------------------------------- file protection
def restore_protected(allowed: set[str] | None = None, current_chapter: int | None = None) -> None:
    """Undo any edit the author made outside its remit."""
    allowed = allowed or set()
    paths = list(PROTECTED) + [p.name for p in ROOT.glob("*.pdf")]
    status = git("status", "--porcelain", "--untracked-files=all", "--", *paths, "book/chapters")
    for line in status.splitlines():
        code, path = line[:2], line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path in allowed:
            continue
        frozen = any(path == p or path.startswith(p + "/") for p in paths)
        m = re.match(r"book/chapters/ch-(\d{4})/(.+)$", path)
        if m and current_chapter is not None:
            n, fname = int(m.group(1)), m.group(2)
            if n < current_chapter and (ROOT / "book/chapters" / f"ch-{n:04d}" / ".complete").exists():
                frozen = True
            elif n == current_chapter and fname.startswith("scene-") and code.strip() != "??":
                frozen = True  # accepted (committed) scenes of the current chapter
        if not frozen:
            continue
        if code.strip() == "??":
            p = ROOT / path
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.exists():
                p.unlink()
            log(f"  removed stray file {path}")
        else:
            git("checkout", "HEAD", "--", path)
            log(f"  restored protected {path}")


ROOT_PDF_MARK = FORGE / "root-pdf-chapter"


def place_root_pdf() -> None:
    """Move the publisher's newest complete-book PDF to the repository root.

    Small books are updated on every build. As the PDF grows, it is committed
    every (size in MB / 2) chapters so the git history stays manageable; GitHub
    refuses files over 100 MB, so beyond ~95 MB only the release is updated.
    """
    ready = sorted((FORGE / "ready").glob("*.pdf")) if (FORGE / "ready").exists() else []
    for pdf in ready:
        size_mb = pdf.stat().st_size / 2 ** 20
        done = len(build.completed_chapters())
        try:
            last = int(ROOT_PDF_MARK.read_text())
        except (FileNotFoundError, ValueError):
            last = -1
        dest = ROOT / pdf.name
        if size_mb > 95:
            log(f"  complete book is {size_mb:.0f} MB, over GitHub's file limit: kept in the release only")
            pdf.unlink()
            continue
        if size_mb < 5 or not dest.exists() or done - last >= max(1, int(size_mb / 2)):
            for old in ROOT.glob("*.pdf"):
                if old.name != pdf.name:
                    old.unlink()  # the title changed; keep a single root PDF
            pdf.replace(dest)
            ROOT_PDF_MARK.write_text(str(done))
        else:
            pdf.unlink()  # a newer build will come; the release already has this one


def commit(msg: str) -> None:
    place_root_pdf()
    git("add", "-A")
    if git("status", "--porcelain").strip():
        git("commit", "-q", "-m", msg)


def push() -> None:
    if not git("remote").strip():
        return
    p = subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        log(f"  push failed: {p.stderr.strip()[:300]}")


# ------------------------------------------------------------ the author
def digest_events(raw: str) -> tuple[str, list[str], int, int, bool, int]:
    """Parse `opencode run --format json` events: text, sessions, tokens, errors."""
    texts, tools, sessions = [], [], []
    tok_in = tok_out = n = 0
    errored = False
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            if TRANSIENT.search(line):
                errored = True
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        n += 1
        sid = ev.get("sessionID")
        if sid and sid not in sessions:
            sessions.append(sid)
        part = ev.get("part") or {}
        t = ev.get("type")
        if t == "text" and part.get("text"):
            texts.append(part["text"])
        elif t in ("tool_use", "tool") or part.get("type") == "tool":
            tools.append(str(part.get("tool") or part.get("name") or "tool"))
        elif t == "step_finish":
            tk = part.get("tokens") or {}
            tok_in += int(tk.get("input") or 0)
            tok_out += int(tk.get("output") or 0) + int(tk.get("reasoning") or 0)
        elif t == "error":
            errored = True
            texts.append("ERROR: " + json.dumps(ev.get("error") or ev)[:600])
    summary = f"[{len(tools)} tool calls: {', '.join(sorted(set(tools)))[:300]}]\n" if tools else ""
    return summary + "\n".join(texts), sessions, tok_in, tok_out, errored, n


def call_author(task: str, title: str, state: dict, allowed: set[str] | None = None,
                current_chapter: int | None = None) -> str:
    """Run one OpenCode task. Retries transient failures with back-off forever."""
    backoff = 60
    while not STOP:
        LOGS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        logfile = LOGS / f"{stamp}-{re.sub(r'[^a-z0-9]+', '-', title.lower())[:60]}.log"
        with open(logfile, "w", encoding="utf-8") as lf:
            lf.write(f"# model: {MODEL}\n# title: {title}\n\n## TASK\n{task}\n\n## OUTPUT\n")
            lf.flush()
            t0 = time.time()
            try:
                p = subprocess.Popen([OPENCODE, "run", "--archived", "--auto", "--agent", "build",
                                      "--format", "json", "-m", MODEL, "--title", f"chronicle: {title}", task],
                                     cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, text=True,
                                     start_new_session=True)
                try:
                    rc = p.wait(timeout=CALL_TIMEOUT)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGTERM)
                    time.sleep(5)
                    if p.poll() is None:
                        os.killpg(p.pid, signal.SIGKILL)
                    rc = 124
            except Exception as e:  # pragma: no cover
                lf.write(f"\n[orchestrator] failed to launch: {e}\n")
                rc = 127
            dt = time.time() - t0
        raw = logfile.read_text(encoding="utf-8", errors="replace").split("## OUTPUT\n", 1)[-1]
        out, sessions, tok_in, tok_out, errored, n_events = digest_events(raw)
        with open(logfile, "a", encoding="utf-8") as lf:
            lf.write(f"\n## DIGEST\nrc={rc} {dt:.0f}s tokens in={tok_in} out={tok_out} errors={errored}\n{out[-4000:]}\n")
        for sid in sessions:  # the log keeps everything; free OpenCode's database
            subprocess.run([OPENCODE, "session", "delete", sid], cwd=ROOT, capture_output=True, timeout=120)
        state["tokens_in"] = state.get("tokens_in", 0) + tok_in
        state["tokens_out"] = state.get("tokens_out", 0) + tok_out
        state["calls"] += 1
        restore_protected(allowed, current_chapter)
        save_state(state)
        tail = (out.strip() or raw.strip())[-400:]
        transient = ((rc != 0 and (TRANSIENT.search(raw[-3000:]) or rc in (124, 127) or dt < 60))
                     or n_events == 0 or (errored and tok_out == 0))
        if transient:
            state["failures_in_row"] += 1
            save_state(state)
            log(f"  author call '{title}' failed (rc={rc}, {dt:.0f}s): {tail[-200:]!r}; retry in {backoff}s")
            if state["failures_in_row"] >= 6:
                (FORGE / "ALERT").write_text(f"{datetime.now()}: {state['failures_in_row']} failed calls in a row. Last: {tail}\n")
            sleep_interruptible(backoff)
            backoff = min(backoff * 2, 1800)
            continue
        state["failures_in_row"] = 0
        (FORGE / "ALERT").unlink(missing_ok=True)
        save_state(state)
        log(f"  author '{title}' done in {dt:.0f}s (rc={rc})")
        return out
    raise SystemExit(0)


def repair_loop(what: str, check, state: dict, attempts: int = 2, **kw) -> list[str]:
    """Run check(); while problems remain ask the author to fix them."""
    problems = check()
    for i in range(attempts):
        if not problems or STOP:
            break
        log(f"  validation problems for {what}: {problems}")
        call_author(prompt("fix-files.md", what=what, problems="\n".join(f"- {p}" for p in problems)),
                    f"repair {what} #{i + 1}", state, **kw)
        problems = check()
    return problems


# ---------------------------------------------------------------- genesis
def need(files: dict[str, int]):
    """Build a checker: each file must exist with at least N words."""
    def check():
        probs = []
        for f, n in files.items():
            p = ROOT / f
            if not p.exists():
                probs.append(f"`{f}` does not exist; create it.")
            elif words(p) < n:
                probs.append(f"`{f}` has only {words(p)} words; it needs at least {n}. Expand it richly.")
        return probs
    return check


def check_book_json():
    probs = need({"bible/book.json": 10})()
    d = build.load_json(ROOT / "bible/book.json", None)
    if d is None:
        probs.append("`bible/book.json` is not valid JSON.")
    else:
        for k in ("title", "subtitle", "tagline", "byline", "cover_motif"):
            if not str(d.get(k, "")).strip():
                probs.append(f"`bible/book.json` lacks a non-empty \"{k}\".")
    return probs


def check_characters(min_count: int, role_word: str | None = None):
    def check():
        sheets = list((ROOT / "characters").glob("*.md"))
        sheets = [s for s in sheets if not s.name.startswith("_")]
        probs = []
        if len(sheets) < min_count:
            probs.append(f"There are only {len(sheets)} character sheets in characters/; at least {min_count} are needed by now.")
        for s in sheets:
            fm, _ = build.md2tex.parse_front_matter(s.read_text(encoding="utf-8", errors="replace"))
            if not fm.get("name"):
                probs.append(f"`characters/{s.name}` has no YAML front matter with a `name:` (see design/templates/character.md).")
            if words(s) < 350:
                probs.append(f"`characters/{s.name}` is thin ({words(s)} words); deepen it to 500+ words.")
        if role_word and not any(role_word in str(build.md2tex.parse_front_matter(s.read_text(errors='replace'))[0].get("role", "")).lower() for s in sheets):
            probs.append(f"No character sheet has role `{role_word}`.")
        return probs[:12]
    return check


GENESIS = [
    ("concept", "genesis-1-concept.md", {}, lambda: check_book_json() + need(
        {"bible/premise.md": 900, "bible/past-life.md": 1500, "bible/voice.md": 600})()),
    ("world", "genesis-2-world.md", {}, need({"bible/world.md": 1500, "bible/history.md": 900, "bible/peoples.md": 900,
                                              "bible/calendar.md": 300, "memory/places.md": 250})),
    ("power", "genesis-3-power.md", {}, need({"bible/magic.md": 1200, "bible/bestiary.md": 900,
                                              "bible/factions.md": 1200, "bible/glossary.md": 200})),
    ("cast-1", "genesis-4-cast.md", {"part": "4", "count": "4",
        "focus": "the protagonist and the people of the past life",
        "extra": "Focus: the PROTAGONIST (role: protagonist, first_appearance: 1). Give this sheet extraordinary depth, 1,500+ words, covering both lives, the double consciousness, and the long arc you imagine. Then at least 3 people from the past life (role: past-life) whose shadows will reach into the new world: perhaps literally, perhaps as memory, guilt or mystery."},
     check_characters(4, "protagonist")),
    ("cast-2", "genesis-4-cast.md", {"part": "5", "count": "6",
        "focus": "family and birthplace",
        "extra": "Focus: the protagonist's new family and the people of the place of birth: parents, siblings, kin, neighbours, a local power, someone who will die early, someone who will become dangerous. Make the household feel lived-in: work, debts, faith, quarrels, tenderness."},
     check_characters(10)),
    ("cast-3", "genesis-4-cast.md", {"part": "6", "count": "8",
        "focus": "the wider world",
        "extra": "Focus: the wider world the protagonist will meet over the first arcs. Include mentors (each with a price), rivals, at least two antagonists of different scales, **a hidden enemy disguised as a friend who will betray**, several potential romantic interests (who may meet the protagonist young but whose romance can only begin in adulthood), a morally grey power-broker, and someone who knows a truth about the reincarnation."},
     check_characters(18)),
    ("arcs", "genesis-7-arcs.md", {}, need({"plan/arcs.md": 2500, "plan/threads.md": 900, "plan/next.md": 400,
                                            "memory/state.md": 150, "memory/timeline.md": 1,
                                            "memory/story-so-far.md": 1, "plan/maps-wanted.md": 30})),
    ("map-world", "genesis-map.md", {"slug": "world", "title": "The Known World",
        "detail": "This is the map of the whole known world: continents, seas, nations and borders, great ranges and rivers, the major cities, wastes, and the edges where knowledge fails. Landscape, 2400×1600."},
     None),
    ("map-region", "genesis-map.md", {"slug": "home-region", "title": "The Region of the Protagonist's Birth",
        "detail": "This is a regional map of the land around the protagonist's birthplace, out to a few days' travel: villages, roads, rivers, forests, hills, mills, shrines, ruins, dangers and the nearest town or city. The slug is `home-region`; give it a fitting in-world title in meta.json. Landscape, 2400×1600."},
     None),
    ("map-home", "genesis-map.md", {"slug": "home-settlement", "title": "The Protagonist's Home Settlement",
        "detail": "This is a detailed plan of the settlement where the protagonist is born: every house or holding of note (label the family homes from the character sheets), fields, wells, the shrine or temple, the smithy, the mill, the paths, the river, the graveyard and the edge of the wild. The slug is `home-settlement`; give it its in-world name in meta.json. Choose portrait (1600×2200) or landscape."},
     None),
    ("portraits", None, {}, None),
]


def run_map_task(slug: str, task: str, title: str, state: dict) -> None:
    call_author(task, title, state)
    for i in range(3):
        if not (ROOT / "atlas" / slug / "map.html").exists():
            call_author(prompt("fix-files.md", what=f"map {slug}",
                               problems=f"- `atlas/{slug}/map.html` does not exist; create it following design/MAP-GUIDE.md."),
                        f"repair map {slug}", state)
            continue
        ok, err = build.render_map(ROOT / "atlas" / slug, force=True)
        if ok:
            log(f"  map {slug} rendered")
            return
        log(f"  map {slug} failed to render: {err[:200]}")
        call_author(prompt("fix-map.md", slug=slug, error=err[-1500:]), f"fix map {slug} #{i + 1}", state)
    ok, err = build.render_map(ROOT / "atlas" / slug, force=True)
    log(f"  map {slug}: {'ok' if ok else 'still failing, left out of the Atlas for now'}")


def run_portraits(slugs: list[str], state: dict) -> None:
    if not slugs:
        return
    call_author(prompt("portraits.md", slugs=", ".join(slugs)), f"portraits {', '.join(slugs)[:40]}", state)
    res = build.render_portraits()
    bad = [s for s in slugs if s in res and not res[s][0]]
    missing = [s for s in slugs if not (ROOT / "characters" / f"{s}.svg").exists()]
    if bad or missing:
        probs = [f"`characters/{s}.svg` does not convert: {res[s][1][:300]}" for s in bad]
        probs += [f"`characters/{s}.svg` was not created." for s in missing]
        call_author(prompt("fix-files.md", what="portraits", problems="\n".join(f"- {p}" for p in probs)),
                    "repair portraits", state)
        build.render_portraits()


def portraitless(limit: int) -> list[str]:
    chars = build.characters()
    return [c["slug"] for c in chars if not (ROOT / "characters" / f"{c['slug']}.svg").exists()][:limit]


def genesis(state: dict) -> None:
    for gid, pfile, kw, check in GENESIS:
        if gid in state["genesis_done"] or STOP:
            continue
        log(f"GENESIS step {gid}")
        if gid.startswith("map-"):
            run_map_task(kw["slug"], prompt(pfile, **kw), f"genesis {gid}", state)
        elif gid == "portraits":
            run_portraits(portraitless(4), state)
        else:
            for cycle in range(3):
                call_author(prompt(pfile, **kw), f"genesis {gid}", state)
                left = repair_loop(f"genesis {gid}", check, state)
                if not left:
                    break
                log(f"  genesis {gid}: still {len(left)} problems after repair; redoing (cycle {cycle + 1})")
            if gid == "concept":
                ok, err = build.build_cover()
                log(f"  cover: {'built' if ok else 'failed: ' + err[:300]}")
        state["genesis_done"].append(gid)
        save_state(state)
        commit(f"genesis: {gid}")
        push()
        trigger_publish()
    if not STOP:
        log("GENESIS complete")


# --------------------------------------------------------------- chapters
def chpath(n: int) -> Path:
    return build.chdir(n)


def prev_end_day(n: int) -> int | None:
    if n <= 1:
        return None
    m = build.load_json(chpath(n - 1) / "meta.json", {}) or {}
    try:
        return int((m.get("days") or {}).get("end"))
    except (TypeError, ValueError):
        return None


def check_meta(n: int):
    def check():
        p = chpath(n) / "meta.json"
        probs = []
        m = build.load_json(p, None)
        if m is None:
            return [f"`{p.relative_to(ROOT)}` is missing or not valid JSON (see design/templates/chapter-meta.json)."]
        if m.get("number") != n:
            m["number"] = n
            p.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
        for k in ("title", "arc", "epigraph", "days", "when", "where", "characters", "scenes"):
            if not m.get(k):
                probs.append(f"meta.json lacks \"{k}\".")
        scenes = m.get("scenes") or []
        if not (3 <= len(scenes) <= 10):
            probs.append(f"meta.json must plan 4 to 8 scenes (it has {len(scenes)}).")
        try:
            a, b = int(m["days"]["start"]), int(m["days"]["end"])
            pe = prev_end_day(n)
            if n == 1 and a != 1:
                probs.append("Chapter 1 must start on Day 1 (past-life material goes in flashback scenes).")
            if pe is not None and not (pe <= a <= pe + 1):
                probs.append(f"days.start is {a} but the previous chapter ended on Day {pe}: it must be {pe} or {pe + 1}. Never skip days between chapters.")
            passage = str(m.get("mode", "normal")).lower() == "passage"
            max_span = 30 if passage else 3
            if b < a or b - a > max_span:
                probs.append(f"days {a}..{b} is not allowed for mode '{m.get('mode', 'normal')}' (normal: a chapter covers at most 3 new days; passage: at most 30, with every day dated).")
        except (KeyError, TypeError, ValueError):
            probs.append("meta.json \"days\" must be {\"start\": int, \"end\": int}.")
        if words(chpath(n) / "plan.md") < 350:
            probs.append(f"`{(chpath(n) / 'plan.md').relative_to(ROOT)}` is missing or too thin; write a detailed beat sheet (500+ words).")
        return probs
    return check


def scene_plan(n: int) -> list[dict]:
    m = build.load_json(chpath(n) / "meta.json", {}) or {}
    return [s if isinstance(s, dict) else {"title": str(s)} for s in (m.get("scenes") or [])]


def ensure_compiles(n: int, k: int, state: dict) -> None:
    f = chpath(n) / f"scene-{k:02d}.tex"
    rel = f.relative_to(ROOT).as_posix()
    for i in range(3):
        build.sanitize_scene(f)
        ok, err = build.proof_scene(n, k)
        if ok:
            return
        log(f"  scene {k} does not compile: {err.splitlines()[0] if err else '?'}")
        call_author(prompt("fix-latex.md", file=rel, error=err[-2500:]), f"fix latex ch{n} s{k} #{i + 1}",
                    state, allowed={rel}, current_chapter=n)
    for fallback in (build.harden_scene, build.flatten_scene):
        fallback(f)
        if build.proof_scene(n, k)[0]:
            log(f"  scene {k}: compiled after {fallback.__name__}")
            return
    log(f"  scene {k}: could not be made to compile (should not happen)")


def write_scene(n: int, k: int, state: dict) -> None:
    plan = scene_plan(n)
    total = len(plan)
    sp = plan[k - 1] if k - 1 < len(plan) else {}
    try:
        target = int(sp.get("target_words", 3000))
    except (TypeError, ValueError):
        target = 3000
    target = max(2200, min(target, 6000))
    min_words = max(1800, int(target * 0.7))
    d = chpath(n)
    rel = (d / f"scene-{k:02d}.tex").relative_to(ROOT).as_posix()
    if k > 1:
        prev = f"book/chapters/{d.name}/scene-{k - 1:02d}.tex (read ALL of it; your scene continues from its last line)"
    elif n > 1:
        last = build.scene_files(n - 1)
        prev = (f"the last scene of the previous chapter, {last[-1].relative_to(ROOT).as_posix()} (read at least its final 120 lines), "
                f"and book/chapters/{build.chdir(n - 1).name}/summary.md") if last else "plan/next.md"
    else:
        prev = "bible/past-life.md (especially the death) and plan/next.md, because this is the very first scene of the saga"
    opening = ("This is the first scene of the chapter: begin with a drop capital, e.g. \\dropcap{T}{he frost} had..."
               if k == 1 else "Do not use \\dropcap in this scene.")
    task = prompt("chapter-scene.md", n=n, k=k, kk=f"{k:02d}", total=total, chdir=d.name,
                  scene_title=sp.get("title", f"scene {k}"), prev_text=prev, min_words=min_words,
                  target=target, opening=opening)
    allowed = {rel}
    call_author(task, f"ch{n} scene {k}", state, allowed=allowed, current_chapter=n)
    f = d / f"scene-{k:02d}.tex"
    for i in range(2):
        if f.exists() and words(f) > 50:
            break
        call_author(task, f"ch{n} scene {k} retry {i + 1}", state, allowed=allowed, current_chapter=n)
    if not f.exists():
        log(f"  scene {k} was never written; will retry the step")
        sleep_interruptible(120)
        return
    build.sanitize_scene(f)
    for i in range(2):
        w = words(f)
        if w >= min_words:
            break
        log(f"  scene {k} short ({w} < {min_words}); expanding")
        call_author(prompt("chapter-expand.md", n=n, k=k, kk=f"{k:02d}", chdir=d.name, words=w,
                           min_words=min_words), f"ch{n} expand scene {k}", state,
                    allowed=allowed, current_chapter=n)
        build.sanitize_scene(f)
    ensure_compiles(n, k, state)
    state["words_total"] = state.get("words_total", 0) + words(f)
    state["scene"] = k + 1
    save_state(state)
    commit(f"ch {n}: scene {k} ({words(f)} words)")
    log(f"  scene {k}/{total} accepted: {words(f)} words")


def check_close_a(n: int):
    def check():
        probs = []
        d = chpath(n)
        s = d / "summary.md"
        if not s.exists():
            return [f"`{s.relative_to(ROOT)}` does not exist."]
        txt = s.read_text(encoding="utf-8", errors="replace")
        secs = {h.lower(): b for h, b in build.md2tex.split_sections(txt)}
        chron = next((b for h, b in secs.items() if "chronicle" in h), "")
        cont = next((b for h, b in secs.items() if "continuity" in h), "")
        if len(chron.split()) < 150:
            probs.append("summary.md needs a `## Chronicle` section of 250–500 words.")
        if len(cont.split()) < 80:
            probs.append("summary.md needs a thorough `## Continuity` section.")
        m = build.load_json(d / "meta.json", {}) or {}
        try:
            a, b = int(m["days"]["start"]), int(m["days"]["end"])
            have = {day for day, _ in build.timeline_entries()}
            missing = [x for x in range(a, b + 1) if x not in have]
            if missing:
                probs.append(f"memory/timeline.md has no line for Day(s) {missing}. Add one line per day: `Day N | date | place | what happened`.")
        except Exception:
            pass
        return probs
    return check


def check_close_b(n: int):
    def check():
        m = build.load_json(chpath(n) / "meta.json", {}) or {}
        probs = []
        minor = (ROOT / "characters" / "_minor.md")
        minor_txt = minor.read_text(errors="replace").lower() if minor.exists() else ""
        for slug in m.get("characters") or []:
            slug = str(slug)
            sheet = ROOT / "characters" / f"{slug}.md"
            if sheet.exists():
                if f"ch {n}" not in sheet.read_text(errors="replace").lower():
                    probs.append(f"`characters/{slug}.md` has no `- Ch {n}:` line in its Chapter Log.")
            elif slug.replace("-", " ") not in minor_txt and slug not in minor_txt:
                probs.append(f"meta.json lists `{slug}` but there is no characters/{slug}.md sheet and no entry in characters/_minor.md. Create the sheet (or the minor entry and remove the slug from meta.json).")
        return probs[:15]
    return check


def decorate(n: int, state: dict) -> None:
    d = chpath(n)
    recent = [build.chdir(i) / "decoration.tex" for i in range(max(1, n - 3), n)]
    recent = ", ".join(p.relative_to(ROOT).as_posix() for p in recent if p.exists()) or "none yet"
    rel = (d / "decoration.tex").relative_to(ROOT).as_posix()
    call_author(prompt("chapter-decoration.md", n=n, chdir=d.name, recent_decos=recent),
                f"ch{n} decoration", state, allowed={rel}, current_chapter=n)
    f = d / "decoration.tex"
    for i in range(3):
        if not f.exists():
            break
        ok, err = build.proof_decoration(n)
        if ok:
            log("  decoration compiles")
            return
        if i == 2:
            break
        call_author(prompt("fix-latex.md", file=rel, error=err[-2500:]), f"fix decoration ch{n} #{i + 1}",
                    state, allowed={rel}, current_chapter=n)
    if f.exists():
        f.rename(d / "decoration.rejected.tex")
    log("  decoration rejected; the default headpiece will be used")


def periodic(n: int, state: dict) -> None:
    if n % CONSOLIDATE_EVERY == 0 and state.get("consolidated_through", 0) < n:
        lo, hi = n - CONSOLIDATE_EVERY + 1, n
        log(f"CONSOLIDATE memory for chapters {lo}-{hi}")
        (ROOT / "memory" / "digests").mkdir(parents=True, exist_ok=True)
        call_author(prompt("periodic-compress.md", n=n, range=f"{lo}–{hi}", lo=f"{lo:04d}", hi=f"{hi:04d}"),
                    f"consolidate {lo}-{hi}", state, current_chapter=n + 1)
        wanted = ROOT / "plan" / "maps-wanted.md"
        if wanted.exists():
            slug_task = ("Choose the most needed map from plan/maps-wanted.md that does not yet exist in atlas/ "
                         "(or substantially revise an existing one if the story has outgrown it). Pick a short "
                         "lowercase-hyphenated slug for its folder, e.g. atlas/<slug>/.")
            before = {p.name for p in (ROOT / "atlas").glob("*")}
            call_author(prompt("genesis-map.md", slug="<slug>", title="the next map the Atlas needs", detail=slug_task),
                        f"map after ch{n}", state, current_chapter=n + 1)
            for d in (ROOT / "atlas").glob("*"):
                if d.name not in before and (d / "map.html").exists():
                    ok, err = build.render_map(d, force=True)
                    if not ok:
                        call_author(prompt("fix-map.md", slug=d.name, error=err[-1500:]), f"fix map {d.name}",
                                    state, current_chapter=n + 1)
                        build.render_map(d, force=True)
        run_portraits(portraitless(3), state)
        state["consolidated_through"] = n
        save_state(state)
        commit(f"memory: consolidated through chapter {n}")


def trigger_publish(volume: int | None = None, final: bool = False) -> None:
    """Ask the background publisher to typeset and ship the book (never blocks)."""
    args = [sys.executable, str(ROOT / "forge" / "publish.py")]
    if volume:
        args += ["--volume", str(volume)]
    if final:
        args.append("--final")
    with open(FORGE / "publish.out", "a") as out:
        subprocess.Popen(args, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)


def collect_final_volumes() -> None:
    """Commit finished volume PDFs that the publisher has handed over."""
    fin = FORGE / "final"
    if not fin.exists():
        return
    for pdf in sorted(fin.glob("vol-*.pdf")):
        dest = ROOT / "pdf" / pdf.name
        dest.parent.mkdir(exist_ok=True)
        if pdf.stat().st_size <= 95 * 1024 * 1024:
            shutil.copy2(pdf, dest)
            log(f"  committed finished {pdf.name} to pdf/")
        pdf.unlink()
    commit("pdf: finished volume")
    push()


def publish(n: int, state: dict) -> None:
    v = build.volume_of(n)
    collect_final_volumes()
    trigger_publish(volume=v, final=(n % build.VOL_SIZE == 0))
    state.setdefault("built", {})[str(v)] = n
    save_state(state)


def write_status(state: dict) -> None:
    done = build.completed_chapters()
    meta = build.book_meta()
    last = build.load_json(chpath(done[-1]) / "meta.json", {}) if done else {}
    total_words = sum(words(f) for n in done for f in build.scene_files(n)) if len(done) < 400 else state.get("words_total", 0)
    lines = [f"# {meta['title']}: press status", "",
             f"- Chapters complete: **{len(done)}**",
             f"- Words of story: **{total_words:,}**",
             f"- Current chapter: {state['chapter']} (step: {state['step']}, scene {state['scene']})",
             f"- Last chapter: {last.get('title', '-') if last else '-'} ({last.get('when', '') if last else ''})",
             f"- Author calls so far: {state['calls']} (tokens in {state.get('tokens_in', 0):,}, out {state.get('tokens_out', 0):,})",
             f"- Updated: {datetime.now():%Y-%m-%d %H:%M}", "",
             f"**The complete book PDF** is at the repository root: `{re.sub(r'[^A-Za-z0-9]+', '-', meta['title']).strip('-')}.pdf`",
             "(every chapter so far, the cast, atlas, lore and indices). It is rebuilt after every chapter and also",
             "attached to the `latest` release. Finished volumes are committed to `pdf/`."]
    (ROOT / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def chapter(state: dict) -> None:
    n = state["chapter"]
    d = chpath(n)
    d.mkdir(parents=True, exist_ok=True)
    if state["step"] == "plan":
        log(f"CHAPTER {n}: plan")
        prev_summaries = ", ".join(
            (build.chdir(i) / "summary.md").relative_to(ROOT).as_posix()
            for i in range(max(1, n - 3), n) if (build.chdir(i) / "summary.md").exists()) or "none yet (this is the beginning)"
        last = build.scene_files(n - 1) if n > 1 else []
        last_scene = last[-1].relative_to(ROOT).as_posix() + " (read at least its final 120 lines)" if last else "none: this is the first chapter of the saga"
        pe = prev_end_day(n)
        rule = "1 (the first day of the new life)" if n == 1 else (f"{pe} or {pe + 1} (the previous chapter ended on Day {pe})" if pe is not None else "the day after the previous chapter")
        for cycle in range(3):
            call_author(prompt("chapter-plan.md", n=n, chdir=d.name, prev_summaries=prev_summaries,
                               last_scene=last_scene, day_rule=rule), f"ch{n} plan", state, current_chapter=n)
            if not repair_loop(f"chapter {n} plan", check_meta(n), state, current_chapter=n):
                break
        for old in d.glob("scene-*.tex"):
            old.unlink()  # a re-plan invalidates scenes from an earlier attempt
        state.update(step="scene", scene=1)
        save_state(state)
        commit(f"ch {n}: plan")
    if state["step"] == "scene" and not STOP:
        total = len(scene_plan(n))
        while state["scene"] <= total and not STOP:
            write_scene(n, state["scene"], state)
        if state["scene"] > total:
            state["step"] = "close_a"
            save_state(state)
    if state["step"] == "close_a" and not STOP:
        log(f"CHAPTER {n}: close (summary, state, timeline)")
        m = build.load_json(d / "meta.json", {}) or {}
        days = m.get("days") or {}
        call_author(prompt("chapter-close-a.md", n=n, chdir=d.name, day_start=days.get("start", "?"),
                           day_end=days.get("end", "?")), f"ch{n} close-a", state, current_chapter=n)
        repair_loop(f"chapter {n} close part 1", check_close_a(n), state, current_chapter=n)
        state["step"] = "close_b"
        save_state(state)
        commit(f"ch {n}: summary, state, timeline")
    if state["step"] == "close_b" and not STOP:
        log(f"CHAPTER {n}: close (people, threads, lore)")
        call_author(prompt("chapter-close-b.md", n=n, chdir=d.name, next=n + 1), f"ch{n} close-b", state,
                    current_chapter=n)
        repair_loop(f"chapter {n} close part 2", check_close_b(n), state, current_chapter=n)
        state["step"] = "decorate"
        save_state(state)
        commit(f"ch {n}: characters, threads, lore")
    if state["step"] == "decorate" and not STOP:
        log(f"CHAPTER {n}: decoration")
        decorate(n, state)
        state["step"] = "finish"
        save_state(state)
    if state["step"] == "finish" and not STOP:
        ok, err = build.proof_chapter(n)
        if not ok:
            log(f"  chapter {n} proof failed: {err[:400]}")
            deco = d / "decoration.tex"
            if deco.exists():
                deco.rename(d / "decoration.rejected.tex")
            for k in range(1, len(build.scene_files(n)) + 1):
                ensure_compiles(n, k, state)
            ok, err = build.proof_chapter(n)
        (d / ".complete").write_text(datetime.now().isoformat() + "\n")
        wc = sum(words(f) for f in build.scene_files(n))
        meta = build.load_json(d / "meta.json", {}) or {}
        log(f"CHAPTER {n} complete: “{meta.get('title', '')}”, {wc} words")
        state.update(step="publish")
        save_state(state)
        write_status(state)
        commit(f"ch {n} complete: {meta.get('title', '')} ({wc} words)")
        push()
    if state["step"] == "publish" and not STOP:
        periodic(n, state)
        publish(n, state)
        state.update(chapter=n + 1, step="plan", scene=1)
        save_state(state)
        write_status(state)
        commit(f"press: on to chapter {n + 1}")
        push()


def main() -> None:
    FORGE.mkdir(exist_ok=True)
    lock = open(FORGE / "lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another orchestrator is already running", file=sys.stderr)
        sys.exit(1)
    state = load_state()
    if not state.get("started"):
        state["started"] = datetime.now().isoformat()
        save_state(state)
    log(f"press starting: model={MODEL}, chapter={state['chapter']}, step={state['step']}")
    genesis(state)
    while not STOP:
        try:
            chapter(state)
        except SystemExit:
            raise
        except Exception as e:  # keep the press alive whatever happens
            log(f"ERROR in chapter loop: {type(e).__name__}: {e}")
            import traceback
            (FORGE / "last-error.txt").write_text(traceback.format_exc())
            sleep_interruptible(120)
    log("press stopped")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        s = load_state()
        print(json.dumps(s, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        main()
    else:
        print(__doc__)
