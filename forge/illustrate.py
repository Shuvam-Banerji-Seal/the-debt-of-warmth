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
    "ART DIRECTION (applies to the whole series): a premium JAPANESE LIGHT-NOVEL ILLUSTRATION in true anime style, the "
    "quality of an official colour insert or character-design plate from a published Japanese light novel. Crisp, clean "
    "black-brown LINE ART with tapering strokes; ANIME facial features (large luminous eyes with layered highlights and "
    "defined lashes, small refined nose, delicate mouth, anime hair rendered in clumps with sharp highlights); CEL SHADING "
    "with two or three tones per material, softened by gentle airbrushed gradients and a little painterly texture in "
    "backgrounds. Adults keep adult proportions (no chibi, no super-deformed). Costumes are intricate and believable, "
    "with real fabric weight, seams, patches, wear and grime. The palette is muted and wintry: slate grey, bone-white "
    "clay slip, ash grey, river-ice blue, wet-wool brown, with warm amber and coal-red firelight as the only strong colour; "
    "atmospheric rim light from fire or snow-glare. The fantasy world is a poor, pre-industrial frozen river town of potters "
    "and eel-fishers (clay yards, kilns, turf-and-daub houses, tallow light, frost), with no modern objects in that world. "
    "The tone is melancholy, dignified and quietly dark, never cute or glossy. Absolutely no text, letters, signatures, "
    "watermarks, borders, panels or speech bubbles anywhere in the image."
)


def api_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENAI_API_KEY missing from .env")


def key_out(path: Path, color: str = "#FF00FF") -> None:
    """Turn a flat chroma backdrop into a clean alpha channel, with spill suppression."""
    import numpy as np
    from PIL import Image, ImageFilter
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    k = np.array([int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5)], dtype=np.float32)
    dist = np.sqrt(((im - k) ** 2).sum(axis=2))
    alpha = np.clip((dist - 0.22) / (0.50 - 0.22), 0.0, 1.0)
    # magenta spill on edges: pull R and B back toward G where they both exceed it
    spill = np.clip(np.minimum(im[..., 0], im[..., 2]) - im[..., 1], 0, 1)
    w = (1.0 - alpha * 0.6)[..., None]
    rgb = im.copy()
    rgb[..., 0] -= spill * w[..., 0]
    rgb[..., 2] -= spill * w[..., 0]
    rgb = np.clip(rgb, 0, 1)
    a = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    out = Image.fromarray((rgb * 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(a)
    out.save(path, optimize=True)


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
    raw = out.with_suffix(".png")
    raw.write_bytes(img)
    if spec.get("chroma"):
        key_out(raw, spec["chroma"])
    if out.suffix == ".webp":  # archival copy: high-quality WebP, alpha kept, ~1/8 the size of PNG
        from PIL import Image
        Image.open(raw).save(out, "WEBP", quality=94, method=6)
        raw.unlink()
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
