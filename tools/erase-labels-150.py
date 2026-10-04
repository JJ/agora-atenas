"""Erase the printed names from the AD 150 Agora plan and emit label geometry.

Usage: python3 tools/erase-labels-150.py
writes agora-150-dc.webp (map without names) and prints the JSON for the
<script id="places"> block of atenas-150-dc.html.

Each label is given as one or more text centerlines (x0, y0, x1, y1, thickness);
inside them only dark, unsaturated (text) pixels are repainted from the
surrounding background, so coloured building outlines survive.
"""
import json
import math
import random
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

SRC = "Plan-of-the-agora-at-the-height-of-its-development-in-ca-AD-150.webp"
OUT = "agora-150-dc.webp"
SLACK = 6       # extra strip width around each text line
FORCE = True    # erase all ink in the strip (text touching a line)
MAX_LETTER = 120  # largest ink blob (px) still treated as text (letters often touch)

# id: (name, marker point on the building, [text centerlines])
PLACES = {
    1: ("Sacred Gate", (100, 36), [(89, 23, 137, 57, 16)]),
    2: ("Dipylon Gate", (214, 30), [(196, 15, 249, 57, 16)]),
    3: ("Stoa Poikile", (405, 36), [(397, 67, 455, 49, 15)]),
    4: ("Eridanos River", (330, 84), [(371, 97, 448, 90, 15)]),
    5: ("St. Phillip", (512, 118), [(497, 92, 542, 101, 15)]),
    6: ("Entrance", (462, 158), [(502, 161, 546, 163, 14)]),
    7: ("Royal Stoa", (290, 120), [(308, 108, 317, 150, 22, FORCE)]),
    8: ("Well", (393, 174), [(356, 141, 379, 141, 11, FORCE)]),
    9: ("Stoa of Zeus", (262, 190), [(287, 234, 299, 175, 13)]),
    10: ("Apollo Patroos", (246, 280), [(276, 316, 287, 243, 15)]),
    11: ("Altar of the 12 Gods", (382, 190), [(360, 216, 419, 216, 14), (374, 229, 411, 229, 14)]),
    12: ("Temple of Ares", (380, 282), [(343, 322, 418, 322, 14)]),
    13: ("Hephaisteion", (85, 262), [(155, 323, 168, 257, 13)]),
    14: ("Bouleuterion", (180, 385), [(146, 412, 154, 343, 13)]),
    15: ("Metroon", (232, 350), [(278, 401, 286, 360, 14)]),
    16: ("Eponymous Heroes", (300, 412), [(313, 461, 320, 362, 15)]),
    17: ("Tholos", (205, 452), [(188, 471, 222, 471, 14)]),
    18: ("Southwest Temple", (358, 485), [(333, 446, 387, 446, 13), (342, 458, 378, 458, 12)]),
    19: ("Odeion", (468, 445), [(449, 388, 497, 388, 12)]),
    20: ("Panathenaic Way", (590, 430), [(497, 273, 546, 346, 16)]),
    21: ("Lawcourts", (595, 262), [(567, 262, 623, 262, 14)]),
    22: ("Monopteros", (628, 300), [(589, 323, 653, 323, 14)]),
    23: ("Bema", (632, 396), [(621, 420, 651, 420, 13)]),
    24: ("Stoa of Attalos", (705, 385), [(740, 350, 741, 425, 14)]),
    25: ("Vrysakiou Street", (770, 410), [(768, 448, 776, 366, 12, FORCE)]),
    26: ("Hadrian Street", (765, 196), [(730, 189, 799, 203, 15)]),
    27: ("House and Shops", (690, 208), [(746, 236, 775, 252, 15), (733, 251, 782, 267, 16)]),
    28: ("Basilica", (625, 190), [(602, 219, 641, 227, 13)]),
    29: ("Civic Offices", (345, 505), [(334, 512, 397, 512, 11, FORCE)]),
    30: ("Middle Stoa", (430, 552), [(410, 537, 470, 537, 13)]),
    31: ("Aiakeion", (322, 640), [(300, 612, 344, 612, 14)]),
    32: ("South Square", (470, 610), [(409, 632, 478, 633, 15)]),
    33: ("South Stoa II", (420, 662), [(450, 657, 512, 657, 14)]),
    34: ("South Stoa I", (540, 690), [(449, 695, 509, 708, 15)]),
    35: ("Southwest Fountain House", (256, 648),
         [(172, 646, 232, 646, 12), (177, 656, 222, 656, 12), (183, 668, 217, 668, 12)]),
    36: ("Piraeus Gate", (20, 700), [(29, 657, 55, 683, 13), (24, 670, 43, 690, 11)]),
    37: ("To Prison", (24, 746), [(28, 729, 73, 729, 13)]),
    38: ("Shrine", (203, 712), [(192, 730, 226, 730, 13)]),
    39: ("East Building", (612, 600), [(636, 567, 642, 634, 14)]),
    40: ("Library of Pantainos", (740, 600), [(682, 573, 705, 616, 13), (671, 579, 694, 622, 13)]),
    41: ("Nymphaion", (668, 682), [(638, 656, 697, 662, 14)]),
    42: ("Southeast Fountain House", (606, 712),
         [(594, 672, 633, 679, 12), (597, 683, 630, 689, 12), (600, 694, 628, 700, 12)]),
    43: ("Mint", (657, 708), [(643, 720, 668, 722, 13)]),
    44: ("Late Roman Fortification Wall", (785, 700),
         [(738, 669, 769, 730, 11, FORCE), (723, 669, 771, 746, 11, FORCE)]),
    45: ("Acropolis", (765, 752), [(733, 710, 750, 743, 11)]),
}


def strip(x0, y0, x1, y1, t):
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    px, py = -uy * t / 2, ux * t / 2
    ex, ey = ux * 2, uy * 2  # a little slack at both ends
    return [(x0 - ex + px, y0 - ey + py), (x1 + ex + px, y1 + ey + py),
            (x1 + ex - px, y1 + ey - py), (x0 - ex - px, y0 - ey - py)]


img = np.array(Image.open(SRC).convert("RGB")).astype(int)
H, W, _ = img.shape
area = Image.new("L", (W, H), 0)
draw = ImageDraw.Draw(area)
forced = Image.new("L", (W, H), 0)
fdraw = ImageDraw.Draw(forced)
for _, _, lines in PLACES.values():
    for x0, y0, x1, y1, t, *force in lines:
        if force:
            fdraw.polygon(strip(x0, y0, x1, y1, t), fill=255)
        else:
            draw.polygon(strip(x0, y0, x1, y1, t + SLACK), fill=255)
forced = np.array(forced) > 0
area = (np.array(area) > 0) | forced

lum = img.mean(axis=2)
sat = img.max(axis=2) - img.min(axis=2)
ink = (lum < 200) & (sat < 70)

# Letters are small blobs of ink lying (almost) entirely inside a label
# strip; building lines that cross a strip are long and reach outside it.
target = forced & ink
seen = np.zeros_like(ink)
for sy, sx in np.argwhere(area & ink):
    if seen[sy, sx]:
        continue
    blob, q = [], deque([(sy, sx)])
    seen[sy, sx] = True
    while q:
        y, x = q.popleft()
        blob.append((y, x))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and ink[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
    b = np.array(blob)
    inside = area[b[:, 0], b[:, 1]].mean()
    size = (b.max(axis=0) - b.min(axis=0)).max()
    if inside > 0.9 and size <= MAX_LETTER:
        target[b[:, 0], b[:, 1]] = True

def grow(m, n):
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]
        g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        m = g
    return m


# Take the anti-aliased halo too, and never copy from it.
target = grow(target, 2) & area & (lum < 250)
source = ~grow(target, 2) & (lum > 215)

random.seed(1)
out = img.copy()
ys, xs = np.nonzero(target)
for y, x in zip(ys, xs):
    for r in (3, 5, 8, 12, 18):
        y0, y1, x0, x1 = max(0, y - r), min(H, y + r + 1), max(0, x - r), min(W, x + r + 1)
        cand = np.argwhere(source[y0:y1, x0:x1])
        if len(cand) >= 6:
            cy, cx = cand[random.randrange(len(cand))]
            out[y, x] = img[y0 + cy, x0 + cx]
            break
    else:
        out[y, x] = (255, 255, 255)

Image.fromarray(out.astype(np.uint8)).save(OUT, quality=90, method=6)

places = {}
for pid, (name, point, lines) in PLACES.items():
    labels = []
    for x0, y0, x1, y1, *_ in lines:
        a = math.degrees(math.atan2(y1 - y0, x1 - x0))
        if a > 90: a -= 180
        if a < -90: a += 180
        labels.append([round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1), round(a)])
    places[pid] = {"at": list(point), "label": labels}
print(json.dumps({"width": W, "height": H, "places": places}, separators=(",", ":")))
print(json.dumps({str(k): v[0] for k, v in PLACES.items()}, indent=4, ensure_ascii=False), file=open("/dev/stderr", "w"))
