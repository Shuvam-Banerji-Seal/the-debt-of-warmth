#!/usr/bin/env python3
"""Generate the book's page and cover textures (parchment, leather).

Deterministic (fixed seeds) so rebuilds are reproducible.
Run:  python3 forge/make_textures.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "design" / "textures"


def fbm(h, w, rng, octaves=6, base=4, persistence=0.55):
    """Fractal value noise in [0,1] built from upsampled random grids."""
    acc = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = base * (2 ** o)
        grid = rng.random((cells + 1, int(cells * w / h) + 2)).astype(np.float32)
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(img, np.float32) / 255.0)
        total += amp
        amp *= persistence
    acc /= total
    acc -= acc.min()
    acc /= max(acc.max(), 1e-6)
    return acc


def edge_falloff(h, w, width=0.10, power=1.6):
    """1.0 in the body of the page, falling smoothly towards the edges only."""
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    d = np.minimum(np.minimum(x, 1 - x) * (h / w), np.minimum(y, 1 - y))
    t = np.clip(d / width, 0, 1)
    return t ** (1 / power)


def fibres(h, w, rng, n=2200):
    img = Image.new("L", (w, h), 0)
    px = img.load()
    for _ in range(n):
        x, y = rng.integers(0, w), rng.integers(0, h)
        ang = rng.normal(0.25, 0.35)
        ln = int(rng.integers(8, 40))
        dx, dy = np.cos(ang), np.sin(ang)
        for k in range(ln):
            xi, yi = int(x + dx * k), int(y + dy * k)
            if 0 <= xi < w and 0 <= yi < h:
                px[xi, yi] = 255
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    return np.asarray(img, np.float32) / 255.0


def foxing(h, w, rng, n=40):
    img = Image.new("L", (w, h), 0)
    arr = np.zeros((h, w), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(n):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        r = rng.uniform(2, 14)
        if rng.random() < 0.6:  # foxing clusters near edges, as in old paper
            cx = int(rng.choice([rng.integers(0, w // 8), rng.integers(7 * w // 8, w)]))
        m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
        arr = np.maximum(arr, m * rng.uniform(0.3, 1.0))
    return arr


def parchment(w=1350, h=2025, seed=7):
    rng = np.random.default_rng(seed)
    base = np.array([243, 228, 196], np.float32) / 255.0      # warm cream
    stain = np.array([196, 160, 104], np.float32) / 255.0     # tea-brown
    mottle = fbm(h, w, rng, octaves=6, base=3)
    fine = fbm(h, w, rng, octaves=4, base=40)
    fib = fibres(h, w, rng)
    fox = foxing(h, w, rng)
    edge = edge_falloff(h, w, width=0.13)

    stain_amt = 0.10 * mottle + 0.05 * fine + 0.06 * fib + 0.35 * fox
    stain_amt += 0.55 * (1 - edge)                              # browned edges
    stain_amt = np.clip(stain_amt, 0, 1)[..., None]
    rgb = base * (1 - stain_amt) + stain * stain_amt
    rgb *= (0.965 + 0.035 * fine)[..., None]
    img = Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8))
    img.save(OUT / "parchment.jpg", quality=84, optimize=True)


def leather(w=1800, h=2700, seed=11):
    rng = np.random.default_rng(seed)
    base = np.array([92, 38, 24], np.float32) / 255.0          # oxblood
    dark = np.array([30, 12, 8], np.float32) / 255.0
    grain = fbm(h, w, rng, octaves=3, base=180)
    cells = fbm(h, w, rng, octaves=4, base=30)
    mottle = fbm(h, w, rng, octaves=5, base=3)
    edge = edge_falloff(h, w, width=0.22, power=1.3)
    g = np.asarray(Image.fromarray((grain * 255).astype(np.uint8)).filter(ImageFilter.EMBOSS), np.float32) / 255.0
    amt = 0.25 * cells + 0.30 * mottle + 0.55 * (1 - edge)
    amt = np.clip(amt, 0, 1)[..., None]
    rgb = base * (1 - amt) + dark * amt
    rgb *= (0.85 + 0.25 * g)[..., None]
    img = Image.fromarray(np.clip(rgb * 255, 0, 255).astype(np.uint8))
    img.save(OUT / "leather.jpg", quality=86, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    parchment()
    leather()
    print("textures written to", OUT)
