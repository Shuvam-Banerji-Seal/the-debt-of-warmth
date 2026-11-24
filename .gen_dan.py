#!/usr/bin/env python3
# Dan Marchetti / Corin — an engraving in his first adult years in Sarn.
# Three-quarter view, sloping shoulders, one light from the upper left,
# hatching that follows the form, a surgeon's hand with a clamp, the
# birth-flower and the pale wedding-ring line.
import math

INK = '#2b1b0e'
RED = '#7e1f14'
P = []

def add(s):
    P.append(s)

def path(d, w=1.6, o=1.0, colour=INK):
    return ('<path d="%s" stroke="%s" stroke-width="%.2f" stroke-opacity="%.2f" '
            'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            % (d, colour, w, o))

def ln(x1, y1, x2, y2, w=0.7, o=0.5, colour=INK):
    return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
            'stroke-width="%.2f" stroke-opacity="%.2f" stroke-linecap="round"/>'
            % (x1, y1, x2, y2, colour, w, o))

def quad(x0, y0, cx, cy, x1, y1, w=0.7, o=0.5, colour=INK):
    return path('M %.1f %.1f Q %.1f %.1f %.1f %.1f' % (x0, y0, cx, cy, x1, y1),
                w, o, colour)

def ell(cx, cy, rx, ry, w=1.2, o=1.0, colour=INK):
    return ('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" stroke="%s" '
            'stroke-width="%.2f" stroke-opacity="%.2f" fill="none"/>'
            % (cx, cy, rx, ry, colour, w, o))

def clippath(name, d):
    return '<clipPath id="%s"><path d="%s"/></clipPath>' % (name, d)

def group(items, clip=None):
    body = '\n'.join(items)
    if clip:
        return '<g clip-path="url(#%s)">\n%s\n</g>' % (clip, body)
    return '<g>\n%s\n</g>' % body

# ---------------------------------------------------------------------------
# Silhouettes
# ---------------------------------------------------------------------------
FACE = ('M 212 196 C 212 158 238 124 288 118 C 332 113 372 138 380 180 '
        'C 384 200 385 218 382 232 C 380 244 386 250 388 256 '
        'C 389 261 385 264 379 264 C 372 264 370 269 366 275 '
        'C 361 293 348 309 330 318 C 318 326 308 331 298 332 '
        'C 278 334 258 326 242 312 C 226 298 214 278 210 252 '
        'C 207 230 208 208 212 196 Z')
HAIR = ('M 210 202 C 210 158 238 120 288 114 C 336 110 374 136 382 182 '
        'C 384 196 383 210 378 222 C 370 186 350 160 322 150 '
        'C 306 144 288 142 272 146 C 246 152 224 174 216 204 Z')
NECK = ('M 242 298 C 242 338 244 368 252 392 L 346 394 '
        'C 342 362 348 332 358 296 C 336 317 266 319 242 298 Z')
TORSO = ('M 252 386 C 216 390 174 406 142 438 C 118 462 102 500 96 550 '
         'L 88 800 L 512 800 L 504 550 C 498 500 482 462 458 438 '
         'C 426 406 384 390 348 386 C 338 404 322 414 300 416 '
         'C 278 414 262 404 252 386 Z')
ARM = ('M 142 438 C 118 462 106 500 106 542 C 106 566 114 590 134 606 '
       'C 154 622 188 630 226 636 L 252 628 L 248 606 '
       'C 222 598 202 586 192 566 C 188 548 190 514 198 480 '
       'C 204 450 214 424 222 404 Z')
FOREARM = ('M 110 552 C 108 574 116 594 134 606 C 154 622 188 630 226 636 '
           'L 252 628 L 248 606 C 222 598 202 586 192 566 '
           'C 184 552 168 548 148 548 Z')

# ---------------------------------------------------------------------------
# Shading helpers: strokes fade out with the light, so no rectangular edges
# ---------------------------------------------------------------------------
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)

def gauss(x, y, cx, cy, rx, ry):
    return math.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))

def shade(xa, xb, c0, c1, slope, step, w, maxop, sfn, bow=0.0, cross=False):
    """Parallel (optionally bowed) strokes; opacity follows the light."""
    out = []
    n = int((c1 - c0) / step) + 1
    for i in range(n):
        c = c0 + i * step
        y0, y1 = c + slope * xa, c + slope * xb
        mx, my = (xa + xb) / 2.0, (y0 + y1) / 2.0
        s = sfn(mx, my)
        if s < 0.05:
            continue
        op = maxop * s
        if bow:
            out.append(quad(xa, y0, mx, my + bow, xb, y1, w, op))
        else:
            out.append(ln(xa, y0, xb, y1, w, op))
        if cross and s > 0.55:
            out.append(quad(xa, y0 - 6, mx, my + 2, xb, y1 - 2, w * 0.8,
                            op * 0.55))
    return out

def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
            u**3 * p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])

def face_light(x, y):
    term = 304 + 0.12 * (y - 220)
    s = smooth(term - 8, term + 44, x)
    s = max(s, 0.72 * gauss(x, y, 258, 211, 30, 17))   # near brow socket
    s = max(s, 0.82 * gauss(x, y, 342, 216, 28, 16))   # far brow socket
    s = max(s, 0.92 * gauss(x, y, 362, 270, 26, 15))   # under the nose
    s = max(s, 0.78 * gauss(x, y, 298, 319, 66, 18))   # under the jaw
    s = max(s, 0.35 * gauss(x, y, 254, 288, 22, 24))   # cheek hollow
    s = max(s, 0.30 * gauss(x, y, 332, 300, 24, 16))   # far cheek
    return min(1.0, s)

def torso_light(x, y):
    term = 300 + 12 * math.sin((y - 400) / 190.0)
    s = smooth(term - 6, term + 112, x)
    s = max(s, 0.52 * gauss(x, y, 300, 416, 70, 42))   # under the collar
    for cx, cy, rx, ry, amp in [(252, 500, 16, 90, 0.32),
                                (348, 520, 18, 100, 0.34),
                                (272, 690, 20, 90, 0.28),
                                (342, 700, 22, 90, 0.30),
                                (300, 770, 90, 18, 0.34)]:
        s = max(s, amp * gauss(x, y, cx, cy, rx, ry))
    return min(1.0, s)

def upperarm_light(x, y):
    s = smooth(150, 196, x) * smooth(418, 468, y) * (1 - smooth(548, 578, y))
    s = max(s, 0.45 * gauss(x, y, 130, 512, 18, 42))
    return min(1.0, s)

def forearm_light(x, y):
    axis = 578 + 0.42 * (x - 130)
    s = smooth(2, 22, y - axis) * smooth(120, 190, x)
    return min(1.0, s)

def cylinder_shade(A, B, halfw, steps, w, maxop, sfn):
    """Bowed cross-strokes on a cylinder, shaded toward the far side."""
    ax, ay = A
    bx, by = B
    ux, uy = bx - ax, by - ay
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    out = []
    for i in range(steps):
        t = (i + 0.5) / steps
        cx, cy = ax + t * (bx - ax), ay + t * (by - ay)
        hw = halfw * (0.82 + 0.18 * math.sin(math.pi * t))
        x0, y0 = cx - nx * hw * 0.15, cy - ny * hw * 0.15
        x1, y1 = cx + nx * hw, cy + ny * hw
        mx, my = cx + ux * 3.5, cy + uy * 3.5
        s = sfn((x0 + x1) / 2, (y0 + y1) / 2)
        if s < 0.08:
            continue
        out.append(quad(x0, y0, mx, my, x1, y1, w, maxop * s))
    return out

# ---------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------
add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800">')
add('<defs>')
add('<radialGradient id="vig" cx="46%" cy="38%" r="70%">')
add('<stop offset="48%" stop-color="#2b1b0e" stop-opacity="0"/>')
add('<stop offset="100%" stop-color="#2b1b0e" stop-opacity="0.12"/>')
add('</radialGradient>')
add('<linearGradient id="paper" x1="0" y1="0" x2="1" y2="1">')
add('<stop offset="0%" stop-color="#fbf7ee"/><stop offset="100%" stop-color="#efe6d5"/>')
add('</linearGradient>')
add('<filter id="rough" x="-6%" y="-6%" width="112%" height="112%">')
add('<feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="19" result="n"/>')
add('<feDisplacementMap in="SourceGraphic" in2="n" scale="1.2" xChannelSelector="R" yChannelSelector="G"/>')
add('</filter>')
add(clippath('face', FACE))
add(clippath('hair', HAIR))
add(clippath('neck', NECK))
add(clippath('torso', TORSO))
add(clippath('arm', ARM))
add(clippath('forearm', FOREARM))
add('</defs>')
add('<rect width="600" height="800" fill="url(#paper)"/>')
add('<rect width="600" height="800" fill="url(#vig)"/>')
add('<g filter="url(#rough)">')

# 1. Silhouettes, drawn before detail
add(path(TORSO, 2.7))
add(path('M 348 386 C 386 390 426 406 458 438 C 482 462 498 500 504 550 L 510 704', 2.4))
add(path('M 366 404 C 398 412 426 430 444 458', 1.4, 0.8))
add(path('M 242 298 C 242 338 244 368 252 392', 2.2))
add(path('M 358 296 C 348 332 342 362 346 394', 2.2))
add(path('M 252 392 C 274 406 326 408 346 394', 2.0, 0.95))
add(path(ARM, 2.6))
add(path('M 110 550 C 136 542 166 542 192 552', 2.0))
add(path('M 112 558 C 138 550 166 550 190 560', 1.1, 0.8))
add(path('M 198 480 C 190 506 186 540 192 566', 1.4, 0.7))
add(path(FACE, 2.8))
# near ear, set well back on the head
add(path('M 214 224 C 198 216 189 230 193 248 C 196 264 205 275 218 273', 1.9))
add(path('M 211 232 C 202 230 199 240 203 250 C 206 258 211 262 217 261', 1.1, 0.9))
add(path('M 210 242 C 205 240 204 248 209 252', 0.9, 0.85))
add(path('M 217 266 C 223 260 225 250 222 242', 1.0, 0.7))
add(path('M 378 226 C 386 222 389 232 386 244', 1.1, 0.6))

# 2. Hair — locks sweeping over the skull, thinning at the temples
outer = [(212, 200), (236, 128), (306, 108), (382, 182)]
inner = [(216, 204), (268, 142), (330, 143), (378, 222)]
locks = []
for i in range(26):
    t = i / 25.0
    ox, oy = bez(*outer, t)
    ix, iy = bez(*inner, t)
    bow = -5 - 7 * math.sin(math.pi * t)
    op = 0.26 + 0.34 * smooth(0.35, 0.9, t)
    locks.append(quad(ox, oy, (ox + ix) / 2 + bow, (oy + iy) / 2 - 5,
                      ix, iy, 0.85 if i % 2 else 1.15, op))
add(group(locks, 'hair'))
# a few loose strands over the forehead
for d, o in [('M 238 156 C 246 146 258 140 272 138', 0.75),
             ('M 252 150 C 264 140 276 136 288 136', 0.6),
             ('M 330 146 C 342 150 352 158 358 168', 0.55),
             ('M 338 144 C 350 148 360 156 366 166', 0.4)]:
    add(path(d, 1.0, o))
# shaved-soft temple
add(path('M 218 196 C 224 176 234 162 248 154', 0.9, 0.45))
add(path('M 364 174 C 372 186 376 198 378 210', 0.9, 0.4))

# 3. Face structure
# brow ridge, with a furrow between
add(path('M 228 205 C 246 194 268 192 288 200', 2.4))
add(path('M 314 198 C 332 193 352 195 368 204', 2.2, 0.95))
add(path('M 232 212 C 250 202 270 201 286 207', 1.0, 0.7))
add(path('M 316 205 C 332 201 350 203 364 210', 1.0, 0.65))
add(path('M 298 194 C 297 202 297 208 299 213', 1.0, 0.7))
add(path('M 305 194 C 305 202 305 208 307 212', 0.9, 0.6))
# near eye, fuller
add(path('M 234 228 C 244 215 268 213 282 226 C 270 236 248 237 234 228 Z', 1.8))
add(path('M 234 224 C 248 211 270 210 283 224', 2.5))
add(path('M 235 229 C 248 238 270 238 282 228', 1.2, 0.85))
add(ell(258, 227, 6.6, 6.3, 1.3))
add(ell(258, 227, 2.7, 2.7, 0.9))
add(path('M 256 220 C 259 219 262 221 263 224', 1.2, 0.8))
# far eye, compressed by the turn
add(path('M 322 224 C 330 216 348 215 358 223 C 349 231 331 231 322 224 Z', 1.5))
add(path('M 322 221 C 332 214 348 213 359 221', 2.0))
add(path('M 323 226 C 332 232 348 232 357 225', 1.0, 0.7))
add(ell(341, 223, 4.8, 4.7, 1.0))
add(ell(341, 223, 1.9, 1.9, 0.8))
# socket shade, clipped and fading
add(group(shade(230, 360, -70, 90, 0.46, 3.1, 0.65, 0.40, face_light), 'face'))
add(path('M 236 239 C 248 245 270 245 280 238', 0.9, 0.55))
add(path('M 324 233 C 333 238 347 238 356 232', 0.8, 0.5))
for j in range(3):
    add(ln(284 + j * 1.5, 230 + j * 3, 293 + j * 2, 227 + j * 4, 0.7, 0.5))
# nose, built from bridge / ridge / wings, shadow on the far side
add(path('M 303 205 C 307 223 316 241 325 252', 1.8))
add(path('M 325 252 C 341 257 359 257 376 256', 1.8))
add(path('M 334 255 C 331 264 336 271 345 272', 1.5, 0.9))
add(path('M 345 272 C 357 275 369 272 377 267', 1.5, 0.9))
add(path('M 377 267 C 383 264 385 260 382 255', 1.3, 0.8))
add(path('M 343 268 C 348 265 354 265 358 268', 1.2, 0.8))
add(path('M 364 270 C 368 268 373 268 376 270', 1.2, 0.8))
add(path('M 325 252 C 318 258 311 261 304 261', 1.2, 0.7))
# mouth, shifted toward the turned side
add(path('M 338 276 C 337 282 336 286 337 290', 1.1, 0.8))
add(path('M 350 275 C 350 281 351 285 350 289', 1.0, 0.7))
add(path('M 303 296 C 312 291 320 294 327 295 C 334 291 346 291 359 294', 1.9))
add(path('M 306 299 C 318 301 344 301 357 297', 2.0))
add(path('M 306 301 C 318 308 344 308 355 302', 1.3, 0.85))
add(path('M 303 296 C 300 294 299 297 301 300', 1.0, 0.65))
add(path('M 359 294 C 362 292 363 295 360 299', 1.0, 0.6))
# cheekbone, nasolabial fold, loose jaw
add(path('M 226 258 C 240 249 256 249 268 256', 1.4, 0.6))
add(path('M 268 258 C 276 274 280 288 278 300', 1.4, 0.7))
add(path('M 276 264 C 282 276 284 288 282 296', 0.9, 0.45))
add(path('M 346 272 C 340 285 334 296 330 303', 1.2, 0.6))
add(path('M 360 282 C 358 296 350 308 340 316', 1.1, 0.5))
add(path('M 252 306 C 264 317 278 323 290 325', 1.0, 0.5))
add(path('M 314 326 C 326 322 338 315 346 306', 1.0, 0.45))

# 4. Light — face, neck, torso, arms
add(group(shade(210, 392, -160, 130, 0.72, 4.4, 0.7, 0.34,
                face_light, bow=-3, cross=True), 'face'))
add(group(cylinder_shade((258, 326), (262, 390), 20, 15, 0.7, 0.34,
                         lambda x, y: 0.35 + 0.65 * smooth(285, 345, x)), 'neck'))
add(group(cylinder_shade((330, 322), (344, 390), 20, 15, 0.7, 0.46,
                         lambda x, y: 0.5 + 0.5 * smooth(310, 350, x)), 'neck'))
add(path('M 262 332 C 256 356 252 376 250 392', 1.2, 0.6))
add(path('M 336 330 C 340 356 344 376 346 394', 1.2, 0.55))
add(group(shade(92, 512, 360, 800, 0.02, 13, 0.7, 0.24,
                torso_light, bow=-7), 'torso'))
add(group(shade(300, 512, 330, 800, 0.22, 6.4, 0.62, 0.30,
                torso_light, bow=-4, cross=True), 'torso'))
# collar and folds
add(path('M 252 386 C 266 404 284 414 300 416 C 318 414 332 404 348 386', 2.1))
add(path('M 260 394 C 274 410 286 420 300 422 C 314 420 326 410 340 394', 1.2, 0.6))
add(path('M 300 422 C 296 468 294 522 296 578', 1.4, 0.55))
add(path('M 266 414 C 256 452 248 500 246 552', 1.2, 0.5))
add(path('M 336 412 C 346 452 352 500 354 550', 1.2, 0.45))
add(group(shade(106, 226, 400, 566, -0.42, 6.4, 0.65, 0.34,
                upperarm_light, bow=-3), 'arm'))
add(group(cylinder_shade((120, 446), (180, 556), 34, 20, 0.7, 0.30,
                         upperarm_light), 'arm'))
add(group(cylinder_shade((128, 578), (240, 622), 20, 18, 0.7, 0.36,
                         forearm_light), 'forearm'))
add(group(cylinder_shade((128, 582), (236, 626), 17, 18, 0.6, 0.20,
                         lambda x, y: forearm_light(x, y - 3)), 'forearm'))
add(path('M 226 612 C 232 606 240 604 246 608', 1.0, 0.6))
add(path('M 230 618 C 236 612 244 610 250 614', 0.9, 0.45))

# 5. The hand — knuckles, curled fingers, thumb, short steady nails
add(path('M 222 608 C 232 618 244 624 258 629 C 272 634 288 638 298 643 '
         'C 306 647 307 654 302 659 C 297 664 288 662 279 659 '
         'C 272 657 267 660 269 667 C 271 674 266 678 259 675 '
         'C 252 672 248 667 246 660 C 242 669 235 673 228 668 '
         'C 221 663 218 653 218 642 C 218 630 218 616 222 608 Z', 2.3))
add(path('M 244 628 C 251 623 261 626 266 633', 1.1, 0.8))
add(path('M 260 633 C 267 628 277 631 282 638', 1.1, 0.75))
add(path('M 276 638 C 283 633 293 636 298 643', 1.1, 0.7))
add(path('M 269 667 C 265 662 263 657 263 652', 0.9, 0.7))
add(path('M 246 660 C 244 654 244 647 247 642', 0.9, 0.65))
add(path('M 228 668 C 226 660 226 651 229 644', 0.9, 0.6))
add(path('M 222 618 C 229 611 239 611 246 618 C 250 623 250 629 246 634', 1.8))
add(path('M 226 620 C 233 616 240 617 244 622', 0.9, 0.65))
add(path('M 294 645 C 299 644 302 647 301 651', 0.8, 0.6))
add(path('M 261 674 C 264 673 266 675 265 677', 0.7, 0.5))
# pale wedding-ring line on the ring finger
add(path('M 258 631 C 260 638 260 647 258 654', 0.9, 0.55))
add(path('M 263 632 C 265 639 265 648 263 655', 0.9, 0.55))
add(path('M 260 631 C 262 638 262 647 260 654', 0.5, 0.16))

# 6. The clamp, held between thumb and forefinger
add(path('M 292 638 C 282 630 272 622 262 615', 1.9))
add(path('M 296 644 C 286 636 276 628 266 621', 1.7, 0.95))
add(ell(269, 618, 4.0, 3.0, 1.3))
add(ell(273, 621, 2.2, 1.7, 0.9, 0.85))
add(path('M 267 615 C 254 605 242 595 228 588', 1.8))
add(path('M 271 619 C 258 609 246 599 232 592', 1.6, 0.95))
add(path('M 228 588 L 219 581 M 232 592 L 223 585', 1.4))
for i in range(5):
    add(ln(224 + i * 2, 584 + i * 2, 220 + i * 2, 589 + i * 2, 0.6, 0.7))
add(ell(300, 655, 7.6, 5.2, 1.4))
add(ell(314, 664, 7.0, 4.8, 1.3, 0.95))
add(path('M 293 650 C 291 645 294 642 299 644', 1.0, 0.7))
add(path('M 307 660 C 305 655 308 652 313 654', 0.9, 0.6))

# 7. Birth-flower — a branching frost-burn down the forearm, a trace at the ribs
main = [(112, 553), (128, 567), (144, 581), (162, 594), (180, 605),
        (198, 614), (216, 620), (236, 626), (250, 629)]
flower = []
for a, b in zip(main[:-1], main[1:]):
    flower.append(quad(a[0], a[1], (a[0] + b[0]) / 2 + 3,
                       (a[1] + b[1]) / 2 - 5, b[0], b[1], 1.8, 0.25, RED))
branches = [
    [(128, 567), (132, 553), (142, 545)],
    [(144, 581), (140, 567), (136, 559)],
    [(162, 594), (168, 580), (178, 574)],
    [(180, 605), (178, 590), (174, 582)],
    [(198, 614), (204, 601), (214, 597)],
    [(216, 620), (220, 607), (228, 601)],
    [(236, 626), (240, 614), (248, 609)],
]
for br in branches:
    for a, b in zip(br[:-1], br[1:]):
        flower.append(quad(a[0], a[1], (a[0] + b[0]) / 2 + 2,
                           (a[1] + b[1]) / 2 - 4, b[0], b[1], 1.1, 0.22, RED))
# a branch across the ribs, at the open collar of the tunic
rib = [(268, 400), (278, 394), (288, 397), (298, 390), (308, 393), (318, 387)]
for a, b in zip(rib[:-1], rib[1:]):
    flower.append(quad(a[0], a[1], (a[0] + b[0]) / 2,
                       (a[1] + b[1]) / 2 - 6, b[0], b[1], 1.2, 0.20, RED))
add(group(flower, 'forearm'))
ink_threads = []
for a, b in zip(main[:-1], main[1:]):
    ink_threads.append(ln(a[0], a[1] + 1, b[0], b[1] + 1, 0.6, 0.5))
add(group(ink_threads, 'forearm'))

# 8. Finish — heavier contours nearest the viewer
add(path('M 142 438 C 118 462 106 500 106 542 C 106 566 114 590 134 606', 3.0))
add(path('M 212 196 C 212 158 238 124 288 118', 3.0))
add(path('M 222 608 C 232 618 244 624 258 629', 2.5))
add('</g>')

# engraver's monogram
add(group([
    path('M 524 752 L 524 774 M 524 752 L 532 752 C 540 752 540 766 532 766 L 524 766', 0.9, 0.6),
    path('M 542 752 L 548 766 L 554 752 M 548 766 L 548 774 M 558 752 L 558 774 M 558 752 L 570 774 M 570 752 L 558 774', 0.9, 0.6),
]))
add('</svg>')

out = '\n'.join(P) + '\n'
open('/mnt/Expansion/can-llms-write/.dan-draft.svg', 'w').write(out)
print('elements:', len(P), 'bytes:', len(out))
