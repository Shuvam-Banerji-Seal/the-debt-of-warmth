#!/usr/bin/env python3
# Dan Marchetti / Corin — engraving, first adult years in Sarn.
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

def wash(d, o, colour=INK):
    return ('<path d="%s" fill="%s" fill-opacity="%.2f" stroke="none"/>' %
            (d, colour, o))

def clippath(name, d):
    return '<clipPath id="%s"><path d="%s"/></clipPath>' % (name, d)

def group(items, clip=None):
    if clip:
        return '<g clip-path="url(#%s)">\n%s\n</g>' % (clip, '\n'.join(items))
    return '<g>\n%s\n</g>' % '\n'.join(items)

# ---------------------------------------------------------------------------
FACE = ('M 210 196 C 210 156 236 122 286 116 C 330 112 366 136 374 178 '
        'C 378 198 378 214 374 226 C 372 234 374 240 376 246 '
        'C 378 251 375 256 370 256 C 363 258 358 266 352 276 '
        'C 346 292 336 306 326 316 C 314 324 304 329 294 330 '
        'C 274 332 254 324 238 310 C 222 296 212 276 208 250 '
        'C 205 228 206 206 210 196 Z')
HAIR = ('M 208 200 C 208 154 236 116 288 110 C 336 106 372 132 380 178 '
        'C 383 194 382 208 378 220 C 372 182 352 158 324 150 '
        'C 306 145 288 143 270 148 C 244 154 222 174 214 202 Z')
STUBBLE = ('M 232 286 C 248 312 272 328 294 330 C 316 328 338 314 352 290 '
           'C 348 312 332 332 308 340 C 288 346 262 338 246 322 '
           'C 238 312 232 298 232 286 Z')
NECK = ('M 242 298 C 242 338 244 368 252 392 L 346 394 '
        'C 342 362 348 332 358 296 C 336 317 266 319 242 298 Z')
TORSO = ('M 252 386 C 216 390 172 408 140 440 C 116 464 102 500 96 550 '
         'L 128 800 L 472 800 L 504 550 C 498 500 484 464 460 440 '
         'C 428 408 384 390 348 386 C 338 404 322 414 300 416 '
         'C 278 414 262 404 252 386 Z')
ARM = ('M 140 440 C 116 464 104 506 108 556 C 110 578 118 592 134 596 '
       'C 152 600 176 596 196 588 L 244 566 L 256 580 '
       'C 234 586 214 584 198 576 C 184 568 180 552 182 534 '
       'C 186 488 202 440 222 406 Z')
FOREARM = ('M 108 546 C 110 574 120 592 136 596 C 156 600 178 594 198 586 '
           'L 248 566 L 256 580 C 232 588 210 584 196 576 '
           'C 180 566 174 550 178 536 C 150 542 128 546 108 546 Z')

# ---------------------------------------------------------------------------
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)

def gauss(x, y, cx, cy, rx, ry):
    return math.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))

def shade(xa, xb, c0, c1, slope, step, w, maxop, sfn, bow=0.0, cross=False):
    out = []
    n = int((c1 - c0) / step) + 1
    for i in range(n):
        c = c0 + i * step
        y0, y1 = c + slope * xa, c + slope * xb
        mx, my = (xa + xb) / 2.0, (y0 + y1) / 2.0
        s = sfn(mx, my)
        if s < 0.06:
            continue
        op = maxop * s
        if bow:
            out.append(quad(xa, y0, mx, my + bow, xb, y1, w, op))
        else:
            out.append(ln(xa, y0, xb, y1, w, op))
        if cross and s > 0.5:
            out.append(quad(xa, y0 - 7, mx, my + 1, xb, y1 - 3, w * 0.8, op * 0.5))
    return out

def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])

def socket_light(x, y):
    s = 0.95 * gauss(x, y, 250, 210, 34, 15)
    s = max(s, 0.95 * gauss(x, y, 330, 214, 30, 15))
    s = max(s, 0.55 * gauss(x, y, 250, 240, 30, 12))
    return min(1.0, s)

def face_light(x, y):
    term = 298 + 0.10 * (y - 220)
    s = smooth(term - 4, term + 30, x)
    s = max(s, 0.74 * gauss(x, y, 250, 212, 28, 16))
    s = max(s, 0.84 * gauss(x, y, 328, 217, 26, 15))
    s = max(s, 0.92 * gauss(x, y, 352, 263, 24, 14))
    s = max(s, 0.76 * gauss(x, y, 292, 318, 60, 17))
    s = max(s, 0.34 * gauss(x, y, 246, 288, 20, 22))
    return min(1.0, s)

def torso_light(x, y):
    term = 304 + 12 * math.sin((y - 400) / 190.0)
    s = smooth(term, term + 94, x)
    s = max(s, 0.48 * gauss(x, y, 300, 416, 66, 40))
    for cx, cy, rx, ry, amp in [(248, 496, 16, 86, 0.32),
                                (348, 516, 18, 96, 0.34),
                                (270, 690, 20, 86, 0.26),
                                (342, 700, 22, 86, 0.28),
                                (300, 770, 86, 16, 0.32)]:
        s = max(s, amp * gauss(x, y, cx, cy, rx, ry))
    return min(1.0, s)

def upperarm_light(x, y):
    s = smooth(146, 192, x) * smooth(420, 470, y) * (1 - smooth(548, 580, y))
    s = max(s, 0.42 * gauss(x, y, 126, 512, 18, 42))
    return min(1.0, s)

def forearm_light(x, y):
    axis = 560 - 0.12 * (x - 130)
    return min(1.0, smooth(4, 24, y - axis) * smooth(116, 190, x))

def cylinder_shade(A, B, halfw, steps, w, maxop, sfn):
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
        x0, y0 = cx - nx * hw * 0.18, cy - ny * hw * 0.18
        x1, y1 = cx + nx * hw, cy + ny * hw
        s = sfn((x0 + x1) / 2, (y0 + y1) / 2)
        if s < 0.08:
            continue
        out.append(quad(x0, y0, cx + ux * 4, cy + uy * 4, x1, y1,
                        w, maxop * s))
    return out

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
for n, d in [('face', FACE), ('hair', HAIR), ('stubble', STUBBLE), ('neck', NECK),
             ('torso', TORSO), ('arm', ARM), ('forearm', FOREARM)]:
    add(clippath(n, d))
add('</defs>')
add('<rect width="600" height="800" fill="url(#paper)"/>')
add('<rect width="600" height="800" fill="url(#vig)"/>')
add('<g filter="url(#rough)">')

# 1. Silhouettes
add(path(TORSO, 2.7))
add(path('M 348 386 C 386 390 426 406 460 440 C 484 464 498 500 504 550 L 500 720', 2.4))
add(path('M 366 404 C 398 412 426 430 446 458', 1.4, 0.8))
add(path('M 242 298 C 242 338 244 368 252 392', 2.2))
add(path('M 358 296 C 348 332 342 362 346 394', 2.2))
add(path('M 252 392 C 274 406 326 408 346 394', 2.0, 0.95))
add(path(ARM, 2.6))
add(path('M 106 544 C 132 536 164 536 190 544', 2.0))
add(path('M 108 552 C 134 544 164 544 188 552', 1.1, 0.8))
add(path('M 196 588 L 244 566', 1.6, 0.9))
add(path(FACE, 2.8))
add(path('M 212 222 C 196 214 187 228 191 248 C 194 266 204 275 217 273', 1.9))
add(path('M 209 230 C 200 228 197 239 201 249 C 204 257 210 262 216 261', 1.1, 0.9))
add(path('M 209 242 C 204 240 203 248 208 252', 0.9, 0.85))
add(path('M 216 266 C 222 260 224 250 221 242', 1.0, 0.7))
add(path('M 374 224 C 382 220 385 230 382 242', 1.1, 0.6))

# 2. Hair
hairline = [(214, 202), (268, 144), (330, 145), (378, 220)]
crown = [(236, 126), (288, 108), (330, 110), (362, 134)]
locks = []
for i in range(38):
    t = i / 37.0
    sx, sy = bez(*hairline, t)
    ex, ey = bez(*crown, t)
    op = 0.44 + 0.40 * smooth(0.2, 0.8, t)
    locks.append(quad(sx, sy, (sx + ex) / 2 + 8 * math.sin(math.pi * t),
                      (sy + ey) / 2 - 8, ex, ey,
                      1.45 if i % 3 else 1.8, op))
add(group(locks, 'hair'))
fine = []
for i in range(30):
    t = (i + 0.5) / 30.0
    sx, sy = bez(*hairline, t)
    ex, ey = bez(*crown, t)
    fine.append(quad(sx, sy, (sx + ex) / 2 + 3, (sy + ey) / 2 - 4,
                     ex, ey, 0.65, 0.26))
add(group(fine, 'hair'))
for d, o in [('M 234 154 C 244 144 258 138 272 136', 0.7),
             ('M 246 148 C 258 138 272 134 286 134', 0.55),
             ('M 334 142 C 346 146 356 154 362 164', 0.6),
             ('M 218 192 C 224 172 234 158 248 150', 0.5),
             ('M 366 170 C 372 182 376 196 378 208', 0.45)]:
    add(path(d, 1.0, o))
add(path('M 212 216 C 208 226 208 236 212 244', 1.0, 0.5))
add(path('M 216 224 C 213 232 213 240 216 246', 0.8, 0.4))

# 3. Face
add(path('M 228 205 C 246 194 264 192 276 200', 2.4))
add(path('M 308 198 C 326 193 344 195 358 204', 2.2, 0.95))
add(path('M 232 212 C 248 202 264 201 274 207', 1.0, 0.7))
add(path('M 310 205 C 326 201 342 203 354 210', 1.0, 0.65))
add(path('M 294 194 C 293 202 293 208 295 213', 1.0, 0.65))
add(path('M 301 194 C 301 202 301 208 303 212', 0.9, 0.55))
# near eye — heavy upper lid over a partial iris, not a circle
add(path('M 230 226 C 240 214 262 213 274 225', 2.4))
add(path('M 230 227 C 242 237 262 237 274 226', 1.0, 0.8))
add(path('M 246 226 C 247 219 257 217 261 224', 1.2, 0.9))
add(path('M 246 228 C 249 233 257 233 260 228', 0.9, 0.6))
add(ell(253, 226, 2.2, 2.2, 0.8, 0.9))
add(path('M 251 223 C 253 222 255 223 256 225', 0.7, 0.55))
# far eye — narrow, compressed by the turn
add(path('M 316 224 C 324 216 342 215 352 223', 1.9))
add(path('M 316 225 C 325 231 342 231 351 224', 0.9, 0.7))
add(path('M 328 224 C 329 219 336 219 340 224', 1.0, 0.85))
add(ell(334, 223, 1.8, 1.8, 0.8, 0.9))
add(path('M 232 239 C 244 245 264 245 272 238', 0.9, 0.55))
add(path('M 318 233 C 327 238 341 238 350 232', 0.8, 0.5))
for j in range(3):
    add(ln(276 + j * 1.5, 230 + j * 3, 285 + j * 2, 227 + j * 4, 0.7, 0.5))
# nose — short, with the tip breaking the outline
add(path('M 298 204 C 303 222 310 240 319 250', 1.9))
add(path('M 319 250 C 334 255 351 255 366 253', 1.9))
add(path('M 330 253 C 327 262 332 268 340 269', 1.5, 0.9))
add(path('M 340 269 C 350 271 360 269 366 265', 1.4, 0.9))
add(path('M 338 266 C 343 263 348 263 352 266', 1.2, 0.8))
add(path('M 319 250 C 312 256 305 259 298 259', 1.2, 0.7))
# mouth — a tired seam, not a drawn-on smile
add(path('M 302 296 C 316 293 342 293 356 296', 2.1))
add(path('M 308 302 C 320 305 340 305 352 301', 0.9, 0.55))
add(path('M 302 296 C 299 294 298 297 300 300', 0.8, 0.55))
add(path('M 356 296 C 359 294 360 297 357 300', 0.8, 0.55))
add(path('M 312 309 C 324 312 340 311 350 307', 0.7, 0.35))
add(path('M 326 278 C 325 282 325 285 326 288', 0.8, 0.6))
add(path('M 336 277 C 336 281 337 284 336 287', 0.7, 0.5))
# cheek, folds, jaw
add(path('M 222 258 C 236 249 252 249 264 256', 1.4, 0.6))
add(path('M 264 258 C 272 274 276 288 274 300', 1.4, 0.7))
add(path('M 272 264 C 278 276 280 288 278 296', 0.9, 0.45))
add(path('M 338 270 C 334 280 331 290 328 296', 1.1, 0.55))
add(path('M 248 306 C 260 317 274 323 286 325', 1.0, 0.5))
add(path('M 310 326 C 322 322 334 315 342 306', 1.0, 0.45))
add(group(shade(230, 356, -180, 70, 0.78, 3.4, 0.6, 0.24,
                lambda x, y: 1.0), 'stubble'))

# 4. Light
add(group(shade(206, 382, -166, 132, 0.72, 4.2, 0.7, 0.50,
                face_light, bow=-3, cross=True), 'face'))
add(group(cylinder_shade((258, 326), (262, 390), 20, 15, 0.7, 0.34,
                         lambda x, y: 0.35 + 0.65 * smooth(285, 345, x)), 'neck'))
add(group(cylinder_shade((330, 322), (344, 390), 20, 15, 0.7, 0.46,
                         lambda x, y: 0.5 + 0.5 * smooth(310, 350, x)), 'neck'))
add(path('M 262 332 C 256 356 252 376 250 392', 1.2, 0.6))
add(path('M 336 330 C 340 356 344 376 346 394', 1.2, 0.55))
add(group(shade(310, 508, 350, 800, 0.06, 9.0, 0.68, 0.16,
                torso_light, bow=-6, cross=True), 'torso'))
add(group(shade(96, 320, 440, 800, -0.05, 14, 0.62, 0.13,
                torso_light, bow=4), 'torso'))
add(path('M 252 386 C 266 404 284 414 300 416 C 318 414 332 404 348 386', 2.1))
add(path('M 260 394 C 274 410 286 420 300 422 C 314 420 326 410 340 394', 1.2, 0.6))
add(path('M 256 392 C 232 394 206 402 186 414', 1.2, 0.45))
add(path('M 344 392 C 366 394 390 402 410 414', 1.2, 0.4))
add(path('M 300 422 C 296 468 294 522 296 578', 1.4, 0.55))
add(path('M 266 414 C 256 452 248 500 246 552', 1.2, 0.5))
add(path('M 336 412 C 346 452 352 500 354 550', 1.2, 0.45))
add(group(shade(104, 226, 400, 566, -0.42, 6.8, 0.65, 0.34,
                upperarm_light, bow=-3), 'arm'))
add(group(cylinder_shade((118, 450), (178, 548), 34, 20, 0.7, 0.30,
                         upperarm_light), 'arm'))
add(group(cylinder_shade((116, 566), (246, 574), 18, 20, 0.7, 0.38,
                         forearm_light), 'forearm'))
add(group(cylinder_shade((116, 570), (244, 578), 15, 20, 0.6, 0.18,
                         lambda x, y: forearm_light(x, y - 3)), 'forearm'))

# 5. Hand — gripping the clamp, raised to the chest
add(path('M 240 566 C 250 560 264 558 278 554 C 292 550 306 546 316 542 '
         'C 324 539 330 546 327 554 C 324 562 314 566 304 566 '
         'C 296 566 290 570 292 578 C 294 586 288 590 280 586 '
         'C 272 582 268 576 266 570 C 262 580 254 584 246 578 '
         'C 240 573 238 570 240 566 Z', 2.4))
add(path('M 258 560 C 266 556 276 556 282 562', 1.1, 0.8))
add(path('M 276 556 C 284 551 294 552 300 558', 1.1, 0.75))
add(path('M 294 550 C 302 546 312 546 318 552', 1.1, 0.7))
add(path('M 292 578 C 288 573 287 568 288 564', 0.9, 0.65))
add(path('M 266 570 C 264 565 264 560 266 556', 0.9, 0.6))
add(path('M 242 568 C 248 561 258 560 264 566 C 268 570 267 576 262 579', 1.8))
add(path('M 246 568 C 252 564 258 565 261 569', 0.9, 0.65))
add(path('M 314 545 C 319 544 322 547 321 552', 0.8, 0.6))
# wedding-ring line on the ring finger
add(path('M 290 558 C 292 564 292 572 290 579', 0.9, 0.55))
add(path('M 295 557 C 297 563 297 571 295 578', 0.9, 0.55))
add(path('M 292 557 C 294 563 294 571 292 578', 0.5, 0.16))

# 6. Clamp — jaws rising clear of the hand
add(path('M 302 554 C 296 544 290 532 284 522', 2.0))
add(path('M 316 564 C 308 552 298 536 288 524', 1.8, 0.95))
add(ell(285, 520, 4.4, 3.4, 1.4))
add(path('M 283 517 C 272 500 262 480 250 448', 2.1))
add(path('M 287 521 C 276 504 266 484 256 452', 1.9, 0.95))
add(path('M 250 448 L 242 438 M 256 452 L 248 442', 1.5))
for i in range(6):
    add(ln(246 + i * 1.4, 442 + i * 2.3, 251 + i * 1.4, 440 + i * 2.3, 0.55, 0.75))
add(ell(306, 558, 7.6, 5.2, 1.5))
add(ell(320, 568, 7.0, 4.8, 1.3, 0.95))
add(path('M 300 552 C 298 547 301 544 306 546', 1.0, 0.7))
add(path('M 252 450 C 264 472 274 496 283 516', 0.7, 0.4))

# 7. Birth-flower
main = [(110, 548), (126, 556), (142, 562), (158, 568), (176, 572),
        (194, 574), (212, 572), (230, 568), (246, 566)]
flower = []
for a, b in zip(main[:-1], main[1:]):
    flower.append(quad(a[0], a[1], (a[0] + b[0]) / 2 + 2,
                       (a[1] + b[1]) / 2 - 6, b[0], b[1], 1.9, 0.36, RED))
branches = [
    [(126, 556), (130, 542), (140, 534)],
    [(142, 562), (140, 548), (136, 540)],
    [(158, 568), (162, 554), (172, 548)],
    [(176, 572), (176, 558), (172, 550)],
    [(194, 574), (198, 560), (208, 556)],
    [(212, 572), (216, 558), (224, 554)],
    [(230, 568), (234, 554), (242, 550)],
]
for br in branches:
    for a, b in zip(br[:-1], br[1:]):
        flower.append(quad(a[0], a[1], (a[0] + b[0]) / 2 + 2,
                           (a[1] + b[1]) / 2 - 4, b[0], b[1], 1.1, 0.30, RED))
rib = [(266, 400), (276, 394), (286, 397), (296, 390), (306, 393), (316, 387)]
for a, b in zip(rib[:-1], rib[1:]):
    flower.append(quad(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 6,
                       b[0], b[1], 1.2, 0.20, RED))
add(group(flower, 'forearm'))
add(group([ln(a[0], a[1] + 1, b[0], b[1] + 1, 0.6, 0.5)
           for a, b in zip(main[:-1], main[1:])], 'forearm'))

# 8. Finish
add(path('M 140 440 C 116 464 104 506 108 556 C 110 578 118 592 134 596', 3.0))
add(path('M 210 196 C 210 156 236 122 286 116', 3.0))
add(path('M 240 566 C 250 560 264 558 278 554', 2.5))
add('</g>')
add('</svg>')

out = '\n'.join(P) + '\n'
open('/mnt/Expansion/can-llms-write/.dan-draft.svg', 'w').write(out)
print('elements:', len(P), 'bytes:', len(out))
