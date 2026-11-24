#!/usr/bin/env python3
"""Generate the two cameo plates in the house style."""
import math

OUT = "/mnt/Expansion/can-llms-write/characters"
INK, PAPER, RED, GOLD, SLATE = "#2b1b0e", "#efe2c4", "#7e1f14", "#9a7432", "#4a5560"
GILT = "url(#gilt)"

# ---------------------------------------------------------------- helpers
def beads(color):
    out = []
    for i in range(96):
        t = -math.pi / 2 + 2 * math.pi * i / 96
        x = 300 + 196 * math.cos(t)
        y = 330 + 235 * math.sin(t)
        r, op = (2.05, "0.50") if i % 2 == 0 else (1.55, "0.85")
        out.append(f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{color}" fill-opacity="{op}"/>')
    return "\n".join(out)

def hatch45(clip, x0, y0, x1, y1, step, op, color=INK, w=0.7, reverse=False):
    """Parallel 45-degree ink strokes inside a clip path."""
    span = y1 - y0
    out, x = [], x0 - span
    while x <= x1:
        if reverse:
            out.append(f'    <line x1="{x:.1f}" y1="{y1:.1f}" x2="{x+span:.1f}" y2="{y0:.1f}" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}"/>')
        else:
            out.append(f'    <line x1="{x:.1f}" y1="{y0:.1f}" x2="{x+span:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}"/>')
        x += step
    return f'  <g clip-path="url(#{clip})">\n' + "\n".join(out) + "\n  </g>"

def med_hatch(reverse=False, op="0.045"):
    out = []
    for i in range(42):
        y = -120 + 10 * i
        x1, y1 = (120, y) if not reverse else (480, y + 540)
        x2, y2 = (480, y + 540) if not reverse else (120, y)
        out.append(f'  <line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" stroke="{INK}" stroke-width="0.55" stroke-opacity="{op}"/>')
        if reverse:
            out.append(f'  <line x1="480" y1="{y:.1f}" x2="120" y2="{y+540:.1f}" stroke="{INK}" stroke-width="0.45" stroke-opacity="0.030"/>')
    return "\n".join(out)

def figure_hatch(op, step, reverse=False):
    out = []
    for i in range(34):
        x = 196 + i * step
        y = 430
        out.append(f'      <line x1="{x:.1f}" y1="{y:.1f}" x2="{x+136:.1f}" y2="{y+136:.1f}" stroke="{PAPER}" stroke-width="0.7" stroke-opacity="{op}"/>')
    if reverse:
        for i in range(24):
            x = 196 + i * 9
            out.append(f'      <line x1="{x:.1f}" y1="566" x2="{x+136:.1f}" y2="430" stroke="{PAPER}" stroke-width="0.55" stroke-opacity="{op*0.7:.3f}"/>')
    return "\n".join(out)

def hair_strokes(kind):
    out = []
    if kind == "combed":
        for i in range(22):
            x = 246 + i * 6.4
            y = 152 + 0.34 * (x - 246)
            out.append(f'      <line x1="{x:.1f}" y1="{y:.1f}" x2="{x+13:.1f}" y2="{y-3.4:.1f}" stroke="{PAPER}" stroke-width="0.9" stroke-opacity="0.30"/>')
        for i in range(14):
            x = 240 + i * 10
            out.append(f'      <line x1="{x:.1f}" y1="176" x2="{x+9:.1f}" y2="187" stroke="{PAPER}" stroke-width="0.75" stroke-opacity="0.20"/>')
    else:
        for i in range(26):
            x = 232 + i * 5.3
            y = 158 + 0.40 * (x - 232)
            out.append(f'      <line x1="{x:.1f}" y1="{y:.1f}" x2="{x-7:.1f}" y2="{y+9:.1f}" stroke="{PAPER}" stroke-width="0.85" stroke-opacity="0.24"/>')
        for i in range(18):
            x = 236 + i * 7.2
            out.append(f'      <line x1="{x:.1f}" y1="182" x2="{x+6:.1f}" y2="198" stroke="{PAPER}" stroke-width="0.7" stroke-opacity="0.18"/>')
    return "\n".join(out)

# ---------------------------------------------------------------- profiles
V_PATH = ("M 300 150 C 326 150 348 156 364 170 C 376 180 384 194 386 208 "
  "C 388 216 387 223 383 228 C 381 231 379 234 381 238 C 386 244 391 252 392 259 "
  "C 393 263 391 266 387 267 C 384 268 382 267 380 265 C 380 269 382 272 381 276 "
  "C 381 281 382 286 381 291 C 381 298 377 305 369 311 C 361 317 351 323 339 327 "
  "C 329 330 320 333 315 339 C 312 345 312 352 314 359 C 316 366 316 374 313 382 "
  "C 310 390 307 398 305 406 C 303 412 303 417 305 422 C 322 426 344 432 362 444 "
  "C 380 456 394 476 400 502 C 404 522 406 544 406 566 L 204 566 "
  "C 206 542 210 518 216 498 C 222 478 232 462 244 450 C 250 444 254 438 254 430 "
  "C 254 422 252 414 251 406 C 250 396 249 386 248 376 C 247 364 244 352 240 342 "
  "C 234 328 228 314 226 296 C 224 280 224 262 226 246 C 228 224 236 200 250 182 "
  "C 262 168 280 154 300 150 Z")

D_PATH = ("M 300 156 C 276 156 254 164 240 180 C 230 191 225 203 223 215 "
  "C 222 221 223 225 226 229 C 228 232 227 235 224 238 C 220 243 214 250 212 257 "
  "C 211 260 213 262 217 262 C 220 262 222 260 223 258 C 222 263 224 266 222 269 "
  "C 220 271 217 272 214 271 C 217 274 221 276 222 279 C 222 284 219 290 213 294 "
  "C 218 303 232 311 250 314 C 266 317 280 314 288 307 C 290 318 290 330 288 342 "
  "C 286 356 284 370 283 384 C 282 392 282 398 283 404 C 266 408 248 414 234 424 "
  "C 218 436 208 454 202 478 C 198 500 196 524 196 566 L 404 566 "
  "C 406 544 408 520 406 498 C 404 478 398 462 390 450 C 384 442 378 434 377 424 "
  "C 376 414 375 402 374 390 C 373 378 372 366 371 354 C 370 340 368 326 364 314 "
  "C 360 300 356 288 352 276 C 348 260 344 242 340 226 C 334 206 322 180 300 156 Z")

V_DETAIL = f'''    <path d="M 354 234 C 358 230 364 230 368 234 C 364 238 358 238 354 234 Z" fill="{PAPER}" fill-opacity="0.92"/>
    <circle cx="362" cy="234" r="1.5" fill="{INK}"/>
    <path d="M 351 225 C 358 221 365 221 371 224" fill="none" stroke="{PAPER}" stroke-width="1.1" stroke-opacity="0.42" stroke-linecap="round"/>
    <path d="M 306 242 C 312 238 317 242 316 248 C 315 254 309 257 304 254" fill="none" stroke="{PAPER}" stroke-width="1.3" stroke-opacity="0.55" stroke-linecap="round"/>
    <path d="M 308 246 C 312 244 313 247 312 250" fill="none" stroke="{PAPER}" stroke-width="0.9" stroke-opacity="0.40" stroke-linecap="round"/>
    <path d="M 383 259 C 387 258 389 260 388 262" fill="none" stroke="{PAPER}" stroke-width="1.1" stroke-opacity="0.62" stroke-linecap="round"/>
    <path d="M 381 279 C 377 277 372 277 369 279 C 367 277 366 276 364 276" fill="none" stroke="{PAPER}" stroke-width="1.4" stroke-opacity="0.88" stroke-linecap="round"/>
    <path d="M 380 288 C 376 291 371 292 367 291" fill="none" stroke="{PAPER}" stroke-width="0.8" stroke-opacity="0.26" stroke-linecap="round"/>
    <path d="M 316 347 C 319 352 319 358 317 363" fill="none" stroke="{PAPER}" stroke-width="0.9" stroke-opacity="0.34" stroke-linecap="round"/>
    <path d="M 305 406 L 320 446 L 343 421" fill="none" stroke="{PAPER}" stroke-width="2.1" stroke-opacity="0.82" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M 305 410 L 316 440 L 306 432" fill="none" stroke="{PAPER}" stroke-width="1.2" stroke-opacity="0.45" stroke-linecap="round"/>
    <path d="M 320 446 C 330 452 340 456 350 458" fill="none" stroke="{PAPER}" stroke-width="1.0" stroke-opacity="0.38" stroke-linecap="round"/>
    <path d="M 314 470 C 330 478 348 482 366 482" fill="none" stroke="{PAPER}" stroke-width="1.1" stroke-opacity="0.46" stroke-linecap="round"/>
    <path d="M 312 478 C 328 486 346 490 364 490" fill="none" stroke="{PAPER}" stroke-width="0.8" stroke-opacity="0.30" stroke-linecap="round"/>'''

D_DETAIL = f'''    <path d="M 233 241 C 237 237 243 237 247 241 C 243 245 237 245 233 241 Z" fill="{PAPER}" fill-opacity="0.92"/>
    <circle cx="240" cy="241" r="1.4" fill="{INK}"/>
    <path d="M 231 232 C 237 229 243 229 248 232" fill="none" stroke="{PAPER}" stroke-width="1.0" stroke-opacity="0.38" stroke-linecap="round"/>
    <path d="M 297 242 C 303 238 308 242 307 248 C 306 253 301 256 296 253" fill="none" stroke="{PAPER}" stroke-width="1.2" stroke-opacity="0.50" stroke-linecap="round"/>
    <path d="M 299 246 C 303 244 304 247 303 250" fill="none" stroke="{PAPER}" stroke-width="0.8" stroke-opacity="0.35" stroke-linecap="round"/>
    <path d="M 215 256 C 212 256 211 258 214 260" fill="none" stroke="{PAPER}" stroke-width="1.0" stroke-opacity="0.55" stroke-linecap="round"/>
    <path d="M 222 271 C 218 270 214 270 211 272" fill="none" stroke="{PAPER}" stroke-width="1.3" stroke-opacity="0.75" stroke-linecap="round"/>
    <path d="M 225 204 C 258 194 306 194 344 208" fill="none" stroke="{PAPER}" stroke-width="2.4" stroke-opacity="0.62" stroke-linecap="round"/>
    <path d="M 227 210 C 260 201 306 201 342 214" fill="none" stroke="{PAPER}" stroke-width="1.0" stroke-opacity="0.32" stroke-linecap="round"/>
    <path d="M 344 208 C 354 212 358 220 354 228" fill="none" stroke="{PAPER}" stroke-width="1.6" stroke-opacity="0.48" stroke-linecap="round"/>
    <path d="M 283 404 C 274 414 266 426 262 440" fill="none" stroke="{PAPER}" stroke-width="1.7" stroke-opacity="0.55" stroke-linecap="round"/>
    <path d="M 283 408 C 292 418 296 430 297 444" fill="none" stroke="{PAPER}" stroke-width="1.2" stroke-opacity="0.38" stroke-linecap="round"/>
    <path d="M 208 470 C 220 478 232 484 244 488" fill="none" stroke="{PAPER}" stroke-width="2.0" stroke-opacity="0.62" stroke-linecap="round"/>
    <path d="M 210 476 C 222 484 234 490 246 494" fill="none" stroke="{PAPER}" stroke-width="0.9" stroke-opacity="0.28" stroke-linecap="round"/>'''

# ---------------------------------------------------------------- build
def plate(path, detail, hair_kind, fig_op, bead_color, med_rev, top, diamond_color,
          seal, emblem_defs, emblem, ribbon_mark, filename):
    s = []
    s.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">
<defs>
  <radialGradient id="vig" cx="48%" cy="38%" r="72%">
    <stop offset="52%" stop-color="{INK}" stop-opacity="0"/>
    <stop offset="100%" stop-color="{INK}" stop-opacity="0.17"/>
  </radialGradient>
  <radialGradient id="medal" cx="46%" cy="36%" r="70%">
    <stop offset="0%" stop-color="#f8eed6"/>
    <stop offset="100%" stop-color="#e6d5ae"/>
  </radialGradient>
  <linearGradient id="gilt" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{GOLD}"/>
    <stop offset="50%" stop-color="#c6a159"/>
    <stop offset="100%" stop-color="{GOLD}"/>
  </linearGradient>
  <clipPath id="medclip"><ellipse cx="300" cy="330" rx="186" ry="224"/></clipPath>
  <clipPath id="figclip"><path d="{path}"/></clipPath>
{emblem_defs}
</defs>
<rect width="600" height="800" fill="{PAPER}"/>
<rect width="600" height="800" fill="url(#vig)"/>
<g fill="none" stroke-linecap="round" stroke-linejoin="round">
  <rect x="24" y="24" width="552" height="752" stroke="{INK}" stroke-width="2.6"/>
  <rect x="32" y="32" width="536" height="736" stroke="{GILT}" stroke-width="1.3"/>
</g>''')
    for x, y, sx, sy in [(44,62,1,1), (44,738,1,-1), (556,62,-1,1), (556,738,-1,-1)]:
        s.append(f'''<g fill="none" stroke="{INK}" stroke-width="1.5" stroke-linecap="round">
  <path d="M {x} {y} C {x+4*sx} {y-14*sy} {x+18*sx} {y-16*sy} {x+26*sx} {y-10*sy}"/>
  <path d="M {x+18*sx} {y-18*sy} C {x+22*sx} {y-10*sy} {x+16*sx} {y-4*sy} {x+10*sx} {y-6*sy}"/>
  <circle cx="{x+8*sx}" cy="{y-10*sy}" r="2.2" fill="{GOLD}" stroke="none"/>
</g>''')
    s.append('<g>')
    s.append(f'  <ellipse cx="300" cy="330" rx="200" ry="240" fill="url(#medal)" stroke="{INK}" stroke-width="3.4"/>')
    s.append(f'  <ellipse cx="300" cy="330" rx="192" ry="231" fill="none" stroke="{GILT}" stroke-width="2.2"/>')
    s.append(beads(bead_color))
    s.append(f'  <ellipse cx="300" cy="330" rx="186" ry="224" fill="none" stroke="{INK}" stroke-width="1.1" stroke-opacity="0.75"/>')
    if bead_color == SLATE:
        s.append(f'  <ellipse cx="300" cy="330" rx="181" ry="219" fill="none" stroke="{SLATE}" stroke-width="0.7" stroke-opacity="0.35"/>')
    s.append('</g>')
    s.append(f'<g clip-path="url(#medclip)">\n  <ellipse cx="300" cy="392" rx="168" ry="150" fill="{SLATE}" fill-opacity="0.045"/>\n</g>')
    s.append(f'<g clip-path="url(#medclip)">\n{med_hatch(med_rev)}\n</g>')
    s.append(f'''<g clip-path="url(#medclip)">
  <g transform="translate(300,330) scale(1.1) translate(-300,-330)">
    <path d="{path}" fill="{INK}"/>
    <g clip-path="url(#figclip)">
{hair_strokes(hair_kind)}
{figure_hatch(fig_op, 6, reverse=(hair_kind=='rough'))}
{detail}
    </g>
  </g>
</g>''')
    s.append(top)
    s.append(f'''<g stroke="{INK}" stroke-width="1.5" fill="{diamond_color}" stroke-linejoin="round">
  <path d="M 300 568 L 307 580 L 300 593 L 293 580 Z"/>
</g>''')
    s.append(emblem)
    s.append(seal)
    s.append(f'''<g stroke="{INK}" stroke-linejoin="round" stroke-linecap="round">
  <path d="M 152 720 L 126 710 L 138 735 L 124 758 L 160 746 Z" fill="{PAPER}" fill-opacity="0.8" stroke-width="1.8"/>
  <path d="M 448 720 L 474 710 L 462 735 L 476 758 L 440 746 Z" fill="{PAPER}" fill-opacity="0.8" stroke-width="1.8"/>
  <path d="M 158 722 C 220 712 380 712 442 722 L 442 748 C 380 738 220 738 158 748 Z" fill="{PAPER}" stroke-width="2.2"/>
  <path d="M 176 728 C 232 721 368 721 424 728" fill="none" stroke="{INK}" stroke-width="0.9" stroke-opacity="0.5"/>
  <path d="M 176 742 C 232 735 368 735 424 742" fill="none" stroke="{INK}" stroke-width="0.9" stroke-opacity="0.4"/>''')
    for i in range(23):
        x = 168 + i * 12
        s.append(f'  <line x1="{x}" y1="738" x2="{x+5}" y2="729" stroke="{INK}" stroke-width="0.6" stroke-opacity="0.22"/>')
    s.append(f'''  <path d="{ribbon_mark}" fill="{RED}" fill-opacity="0.6" stroke-width="1.2"/>
</g>
</svg>''')
    with open(f"{OUT}/{filename}", "w") as f:
        f.write("\n".join(s) + "\n")

# -------------------------------------------------------------- Vesci emblem
V_EMBLEM_DEFS = f'''  <clipPath id="forcepsclip"><path d="M 214 640 C 260 636 330 638 380 650 C 340 660 270 662 214 656 Z"/></clipPath>
  <clipPath id="chartclip"><rect x="278" y="678" width="46" height="28" rx="1.5"/></clipPath>'''

V_TOP = f'''<g stroke="{INK}" stroke-linejoin="round" stroke-linecap="round">
  <path d="M 300 96 C 286 84 266 80 252 86 C 262 92 268 98 268 104 C 278 100 290 100 300 106 C 310 100 322 100 332 104 C 332 98 338 92 348 86 C 334 80 314 84 300 96 Z" fill="{RED}" fill-opacity="0.72" stroke-width="1.8"/>
  <path d="M 300 96 C 292 88 292 76 300 66 C 308 76 308 88 300 96 Z" fill="{GOLD}" stroke-width="1.6"/>
  <circle cx="300" cy="76" r="3.4" fill="{RED}" stroke="none"/>
  <path d="M 288 100 C 292 96 296 95 300 96 C 304 95 308 96 312 100" fill="none" stroke="{GOLD}" stroke-width="1.1"/>
</g>'''

V_EMBLEM = f'''<g transform="rotate(-32 300 650)">
  <path d="M 194 648 C 202 646 210 646 218 648 L 358 648 C 366 647 372 648 378 650 C 372 652 366 653 358 652 L 218 652 C 210 654 202 654 194 648 Z" fill="{PAPER}" stroke="{INK}" stroke-width="1.9"/>
  <ellipse cx="206" cy="641" rx="7" ry="5" fill="none" stroke="{INK}" stroke-width="1.9"/>
  <ellipse cx="206" cy="655" rx="7" ry="5" fill="none" stroke="{INK}" stroke-width="1.9"/>
  <path d="M 212 644 L 226 648 L 226 652 L 212 656" fill="none" stroke="{INK}" stroke-width="1.5"/>
  <path d="M 358 648 L 380 646 L 380 654 L 358 652 Z" fill="{SLATE}" fill-opacity="0.5" stroke="{INK}" stroke-width="1.6"/>
  <path d="M 364 649 L 364 651 M 370 648 L 370 652" stroke="{INK}" stroke-width="0.7"/>
{hatch45("forcepsclip", 218, 646, 358, 654, 6, "0.30", INK, 0.6)}
  <path d="M 226 648 C 270 646 330 647 356 649" fill="none" stroke="{PAPER}" stroke-width="0.9" stroke-opacity="0.75"/>
</g>
<g transform="rotate(32 300 650)">
  <path d="M 278 678 L 316 678 L 324 686 L 324 706 L 278 706 Z" fill="{PAPER}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>
  <path d="M 278 678 L 316 678 L 324 686 L 286 686 Z" fill="{SLATE}" fill-opacity="0.16" stroke="{INK}" stroke-width="1.3"/>
  <path d="M 284 692 L 306 692 M 284 696 L 318 696 M 284 700 L 312 700" fill="none" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.6"/>
  <path d="M 286 700 L 316 700" fill="none" stroke="{RED}" stroke-width="1.7"/>
  <path d="M 286 694 L 298 694" fill="none" stroke="{RED}" stroke-width="1.1"/>
  <path d="M 314 682 L 322 682 L 322 688" fill="none" stroke="{INK}" stroke-width="1"/>
{hatch45("chartclip", 278, 678, 324, 706, 6, "0.16", INK, 0.6)}
</g>
<g>
  <circle cx="300" cy="612" r="14" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>
  <circle cx="300" cy="612" r="10" fill="none" stroke="{GILT}" stroke-width="1.2"/>
  <path d="M 300 604 L 300 612 L 306 615" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>
  <circle cx="300" cy="612" r="1.4" fill="{RED}"/>
  <path d="M 286 610 L 282 610 M 286 614 L 282 614 M 314 610 L 318 610 M 314 614 L 318 614" stroke="{INK}" stroke-width="0.8"/>
</g>'''

V_SEAL = f'''<circle cx="300" cy="650" r="18" fill="{PAPER}" stroke="{INK}" stroke-width="2.2"/>
<circle cx="300" cy="650" r="13.5" fill="none" stroke="{GILT}" stroke-width="1.2"/>
<path d="M 293 644 L 307 644 L 307 656 L 293 656 Z" fill="none" stroke="{RED}" stroke-width="1.3"/>
<path d="M 296 648 L 304 648 M 296 651 L 304 651 M 296 654 L 301 654" stroke="{RED}" stroke-width="0.9"/>'''

V_RIBBON = "M 297 733 L 303 733 L 303 743 L 297 743 Z M 297 735 L 293 733 M 297 738 L 293 736 M 297 741 L 293 739 M 303 735 L 307 733 M 303 738 L 307 736 M 303 741 L 307 739"

# -------------------------------------------------------------- Dessa emblem
D_EMBLEM_DEFS = f'''  <clipPath id="sieveclip"><circle cx="226" cy="648" r="27"/></clipPath>
  <clipPath id="boneclip"><path d="M 348 632 C 366 630 386 632 402 638 C 404 652 402 666 400 674 C 384 668 364 666 348 664 C 344 654 344 642 348 632 Z"/></clipPath>
  <clipPath id="tinclip"><ellipse cx="300" cy="606" rx="17" ry="12"/></clipPath>'''

D_TOP = f'''<g stroke="{INK}" stroke-linejoin="round" stroke-linecap="round">
  <path d="M 300 96 C 288 90 272 90 262 96 C 268 100 272 104 274 110 C 284 104 292 104 300 108 C 308 104 316 104 326 110 C 328 104 332 100 338 96 C 328 90 312 90 300 96 Z" fill="{PAPER}" stroke-width="1.8"/>
  <path d="M 288 92 C 294 84 306 84 312 92" fill="none" stroke="{INK}" stroke-width="1.5"/>
  <path d="M 300 96 C 300 88 296 82 292 78 M 300 96 C 300 88 304 82 308 78" fill="none" stroke="{RED}" stroke-width="1.3"/>
  <circle cx="300" cy="98" r="2.6" fill="{SLATE}"/>
</g>'''

D_EMBLEM = f'''<g transform="rotate(-18 226 648)">
  <circle cx="226" cy="648" r="27" fill="{PAPER}" stroke="{INK}" stroke-width="2.3"/>
  <circle cx="226" cy="648" r="21" fill="none" stroke="{INK}" stroke-width="1.2" stroke-opacity="0.7"/>
{hatch45("sieveclip", 199, 621, 253, 675, 5, "0.40", INK, 0.7)}
{hatch45("sieveclip", 199, 621, 253, 675, 5, "0.26", INK, 0.6, reverse=True)}
  <path d="M 218 630 C 224 638 222 646 230 652 C 236 657 234 665 240 670" fill="none" stroke="{RED}" stroke-width="1.6" stroke-linecap="round"/>
  <path d="M 226 621 L 226 675 M 199 648 L 253 648" fill="none" stroke="{INK}" stroke-width="0.9" stroke-opacity="0.5"/>
</g>
<g transform="rotate(14 376 652)">
  <path d="M 348 632 C 366 630 386 632 402 638 C 404 652 402 666 400 674 C 384 668 364 666 348 664 C 344 654 344 642 348 632 Z" fill="{PAPER}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>
{hatch45("boneclip", 348, 632, 402, 674, 7, "0.20", INK, 0.6)}'''
for i in range(19):
    x = 352 + i * 2.45
    D_EMBLEM += f'\n  <path d="M {x:.1f} 633 L {x+1.5:.1f} 642" stroke="{INK}" stroke-width="1.0" stroke-opacity="0.75"/>'
D_EMBLEM += f'''
  <path d="M 350 660 C 368 662 384 664 398 670" fill="none" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.4"/>
</g>
<g>
  <ellipse cx="300" cy="606" rx="17" ry="12" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>
  <ellipse cx="300" cy="606" rx="13" ry="8.5" fill="none" stroke="{SLATE}" stroke-width="1" stroke-opacity="0.6"/>
  <path d="M 294 600 C 298 596 306 596 310 600 C 308 604 304 606 300 606 C 296 606 294 604 294 600 Z" fill="{RED}" fill-opacity="0.28" stroke="{INK}" stroke-width="1.1"/>
  <path d="M 297 601 C 300 603 304 603 307 601" fill="none" stroke="{INK}" stroke-width="0.8"/>
{hatch45("tinclip", 283, 594, 317, 618, 6, "0.18", INK, 0.55)}
</g>'''

D_SEAL = f'''<circle cx="300" cy="650" r="18" fill="{PAPER}" stroke="{INK}" stroke-width="2.2"/>
<circle cx="300" cy="650" r="13.5" fill="none" stroke="{GILT}" stroke-width="1.2"/>
<path d="M 288 656 C 288 646 292 640 300 640 C 308 640 312 646 312 656" fill="none" stroke="{RED}" stroke-width="1.2"/>
<path d="M 293 644 L 293 653 M 297 642 L 297 654 M 301 642 L 301 654 M 305 643 L 305 653 M 309 646 L 309 652" stroke="{RED}" stroke-width="1.0"/>'''

D_RIBBON = "M 296 734 L 304 734 L 304 742 L 300 746 L 296 742 Z M 297 737 L 301 737 M 297 740 L 301 740 M 299 734 L 299 742"

# ---------------------------------------------------------------- write
plate(V_PATH, V_DETAIL, "combed", "0.13", GOLD, False, V_TOP, GOLD, V_SEAL,
      V_EMBLEM_DEFS, V_EMBLEM, V_RIBBON, "paul-vesci.svg")
plate(D_PATH, D_DETAIL, "rough", "0.16", SLATE, True, D_TOP, SLATE, D_SEAL,
      D_EMBLEM_DEFS, D_EMBLEM, D_RIBBON, "dessa-silt.svg")
print("wrote portraits")
