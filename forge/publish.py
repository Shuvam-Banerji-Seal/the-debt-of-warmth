#!/usr/bin/env python3
"""Background publisher: typesets the complete book and ships the PDFs.

Runs beside the orchestrator so the author never waits for LaTeX. Each run
rebuilds the complete book (and optionally one volume), then:
  * hands the complete book to the press (.forge/ready/), which places it at
    the repository root and commits it with the story,
  * uploads the PDFs to the rolling `latest` GitHub release.

If a publish is requested while one is running, it is queued and runs once
more when the current one finishes.

  python3 forge/publish.py [--volume V [--final]]
"""
from __future__ import annotations

import fcntl
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = build.ROOT
FORGE = ROOT / ".forge"
LOCK = FORGE / "publish.lock"
AGAIN = FORGE / "publish-again"
MAX_GIT_BYTES = 95 * 1024 * 1024  # GitHub rejects files over 100 MB


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [publish] {msg}"
    print(line, flush=True)
    with open(FORGE / "orchestrator.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(*args, input_bytes: bytes | None = None, env=None) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, input=input_bytes, capture_output=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode(errors='replace')[:400]}")
    return p.stdout.decode(errors="replace").strip()


def slug_title() -> str:
    t = build.book_meta()["title"]
    return re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-") or "Chronicle"


def release(files: dict[str, Path]) -> None:
    if not files or not shutil.which("gh") or not git("remote"):
        return
    tag = "latest"
    if subprocess.run(["gh", "release", "view", tag], cwd=ROOT, capture_output=True).returncode != 0:
        subprocess.run(["gh", "release", "create", tag, "--title", "The chronicle so far",
                        "--notes", "The complete book as it stands, plus the volume in progress. "
                                   "Rebuilt automatically as the author writes.", "--latest"],
                       cwd=ROOT, capture_output=True)
    staged = FORGE / "release"
    shutil.rmtree(staged, ignore_errors=True)
    staged.mkdir(parents=True)
    paths = []
    for name, path in files.items():
        dst = staged / name
        shutil.copy2(path, dst)
        paths.append(str(dst))
    p = subprocess.run(["gh", "release", "upload", tag, "--clobber", *paths], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        log(f"  release upload failed: {p.stderr.strip()[:300]}")


def publish_once(volume: int | None, final: bool = False) -> None:
    t0 = time.time()
    build.render_maps()
    build.render_portraits()
    cover = build.BUILD / "cover" / "cover.pdf"
    meta_src = ROOT / "bible" / "book.json"
    emblem = ROOT / "design" / "cover" / "emblem.tex"
    newest = max([p.stat().st_mtime for p in (meta_src, emblem, ROOT / "design/cover/cover.tex") if p.exists()] or [0])
    if meta_src.exists() and (not cover.exists() or cover.stat().st_mtime < newest):
        ok, err = build.build_cover()
        log(f"  cover {'rebuilt' if ok else 'failed: ' + err[:200]}")
    files: dict[str, Path] = {}
    title = slug_title()
    ok, pdf, err = build.build_complete()
    if ok:
        files[f"{title}.pdf"] = pdf
    else:
        log(f"  complete book FAILED: {err[:600]}")
    if volume:
        okv, vpdf, verr = build.build_volume(volume)
        if okv and vpdf:
            files[f"{title}-Volume-{volume:03d}.pdf"] = vpdf
            if final:
                (FORGE / "final").mkdir(exist_ok=True)
                shutil.copy2(vpdf, FORGE / "final" / f"vol-{volume:03d}.pdf")
                log(f"  volume {volume} is complete; handed to the press for the main branch")
        elif vpdf is not None:
            log(f"  volume {volume} FAILED: {verr[:400]}")
    if cover.exists():
        files[f"{title}-Cover.pdf"] = cover
    if not files:
        return
    chs = build.completed_chapters()
    msg = f"Book as of chapter {chs[-1]}" if chs else "Book before the first chapter"
    if ok:
        ready = FORGE / "ready"
        ready.mkdir(exist_ok=True)
        tmp = ready / f".{title}.pdf.tmp"
        shutil.copy2(pdf, tmp)
        tmp.replace(ready / f"{title}.pdf")  # the press moves it to the repository root
    release(files)
    pages = ""
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        pages = re.search(r"Pages:\s+(\d+)", out).group(1) + " pages, "
    except Exception:
        pass
    log(f"  published {msg.lower()} ({pages}{time.time() - t0:.0f}s): {', '.join(files)}")


def main() -> None:
    FORGE.mkdir(exist_ok=True)
    volume = None
    final = "--final" in sys.argv
    if "--volume" in sys.argv:
        volume = int(sys.argv[sys.argv.index("--volume") + 1])
    lock = open(LOCK, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        prev = AGAIN.read_text().split() if AGAIN.exists() else []
        fin = final or "F" in prev  # never drop a queued final-volume request
        vol = volume or (int(prev[0]) if prev and prev[0].isdigit() else None)
        AGAIN.write_text(f"{vol or ''} {'F' if fin else ''}")  # queue one more run
        return
    while True:
        AGAIN.unlink(missing_ok=True)
        try:
            publish_once(volume, final)
        except Exception as e:
            log(f"  publish error: {type(e).__name__}: {e}")
        if not AGAIN.exists():
            break
        parts = AGAIN.read_text().split()
        volume = int(parts[0]) if parts and parts[0].isdigit() else volume
        final = "F" in parts


if __name__ == "__main__":
    main()
