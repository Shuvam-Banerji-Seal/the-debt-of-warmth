#!/usr/bin/env python3
"""Light-novel illustrations via OpenAI's image models.

Run by Claude (the orchestrator) only, never by the author model or the
services: images cost money, so every prompt is hand-written by Claude and
stored as a spec in art/prompts/<id>.json:

  {"id": "char-dessa-silt", "kind": "character", "out": "art/characters/dessa-silt.png",
   "model": "gpt-image-2.5-sunburst", "size": "1024x1536", "quality": "high",
   "background": "transparent", "prompt": "...", "references": ["art/characters/x.png"],
   "caption": "...", "chapter": 3}

  python3 forge/illustrate.py [ID ...] [--force] [--dry]

The key is read from .env (OPENAI_API_KEY); it is never printed or logged.
Every generation is recorded (without the key) in art/ledger.jsonl.
"""
from __future__ import annotations

import base64
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art"
PROMPTS = ART / "prompts"
LEDGER = ART / "ledger.jsonl"
API = "https://api.openai.com/v1/images"

# Shared art direction, prepended to every prompt so the whole book reads as one artist's work.
STYLE = (
    "ART DIRECTION (applies to the whole series): a premium Japanese light-novel illustration, the quality of an "
    "official colour insert or character-design plate from a published light novel. Clean, confident line art with "
    "tapering ink lines; soft cel shading layered with delicate painterly gradients; expressive, carefully drawn eyes "
    "(realistic proportions for adults, not chibi); intricate, believable costume detail with real fabric weight, "
    "seams, wear and grime. The palette is muted and wintry: slate grey, bone-white clay slip, ash grey, river-ice blue, "
    "wet-wool brown, with warm amber and coal-red firelight as the only strong colour. Atmospheric light with rim "
    "light from fire or snow-glare. The world is a poor, pre-industrial frozen river town of potters and eel-fishers "
    "(clay yards, kilns, turf-and-daub houses, tallow light, frost); no modern objects in that world. The tone is "
    "melancholy, dignified and quietly dark, never cute. Absolutely no text, letters, signatures, watermarks, borders "
    "or speech bubbles anywhere in the image."
)


def api_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENAI_API_KEY missing from .env")


def generate(spec: dict, key: str, force: bool = False, dry: bool = False) -> dict:
    out = ROOT / spec["out"]
    if out.exists() and not force:
        return {"id": spec["id"], "status": "exists"}
    prompt = STYLE + "\n\n" + spec["prompt"].strip()
    fields = {
        "model": spec.get("model", "gpt-image-2.5-sunburst"),
        "prompt": prompt,
        "size": spec.get("size", "1024x1536"),
        "quality": spec.get("quality", "high"),
        "background": spec.get("background", "auto"),
        "output_format": spec.get("output_format", "png"),
        "n": 1,
    }
    if dry:
        return {"id": spec["id"], "status": "dry", "chars": len(prompt)}
    headers = {"Authorization": f"Bearer {key}"}
    refs = [ROOT / r for r in spec.get("references", []) if (ROOT / r).exists()]
    t0 = time.time()
    for attempt in range(4):
        try:
            if refs:
                files = [("image[]", (r.name, open(r, "rb"), "image/png")) for r in refs]
                data = {k: str(v) for k, v in fields.items()}
                r = requests.post(f"{API}/edits", headers=headers, data=data, files=files, timeout=900)
            else:
                r = requests.post(f"{API}/generations", headers=headers, json=fields, timeout=900)
            if r.status_code == 200:
                break
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(20 * (attempt + 1))
                continue
            return {"id": spec["id"], "status": f"HTTP {r.status_code}", "error": r.text[:600]}
        except requests.RequestException as e:
            time.sleep(20 * (attempt + 1))
            err = str(e)
    else:
        return {"id": spec["id"], "status": "failed after retries"}
    payload = r.json()
    img = base64.b64decode(payload["data"][0]["b64_json"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img)
    rec = {"id": spec["id"], "out": spec["out"], "model": fields["model"], "size": fields["size"],
           "quality": fields["quality"], "background": fields["background"], "references": [str(x.relative_to(ROOT)) for x in refs],
           "usage": payload.get("usage"), "seconds": round(time.time() - t0), "at": datetime.now().isoformat(timespec="seconds")}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")
    rec["status"] = "ok"
    return rec


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force, dry = "--force" in sys.argv, "--dry" in sys.argv
    specs = [json.loads(p.read_text()) for p in sorted(PROMPTS.glob("*.json"))]
    if args:
        specs = [s for s in specs if s["id"] in args]
    key = "" if dry else api_key()
    # characters first (scenes may use them as references), then the rest in parallel
    first = [s for s in specs if s["kind"] == "character"]
    rest = [s for s in specs if s["kind"] != "character"]
    for batch in (first, rest):
        with ThreadPoolExecutor(max_workers=4) as ex:
            for res in ex.map(lambda s: generate(s, key, force, dry), batch):
                usage = res.get("usage") or {}
                print(f"{res['id']}: {res['status']} {res.get('seconds', '')}s "
                      f"out_tokens={usage.get('output_tokens', '-')} {res.get('error', '')}", flush=True)


if __name__ == "__main__":
    main()
