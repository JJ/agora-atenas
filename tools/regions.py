"""Extract the grey building areas of agora.png as SVG paths (one per legend number).

Usage: python3 tools/regions.py > regions.json
then paste the output into the <script id="regions"> block of index.html.
"""
import json
import sys
from collections import deque

import numpy as np
from PIL import Image

img = np.array(Image.open(sys.argv[1] if len(sys.argv) > 1 else "agora.png"))
H, W = img.shape
grey = (img > 150) & (img < 230)

# A seed pixel inside each building's grey fill (several when the legend
# number covers more than one structure).
SEEDS = {
    1: [(652, 314)], 2: [(656, 654)], 3: [(607, 653)], 4: [(460, 618)],
    5: [(386, 598)], 6: [(212, 489)], 8: [(268, 427)], 10: [(348, 376)],
    11: [(298, 345)], 12: [(230, 359)], 13: [(158, 247)], 14: [(297, 267)],
    15: [(310, 187)], 16: [(423, 185), (418, 211)], 17: [(356, 109)],
    18: [(215, 113)], 19: [(422, 75)], 20: [(551, 127)],
}
# Colonos Agoraios (7) is the hatched hill: every grey pixel in these boxes
# that does not belong to a building.
HILL_BOXES = [(25, 85, 300, 280), (25, 395, 232, 572)]


def flood(x, y):
    seen, q = {(y, x)}, deque([(y, x)])
    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
            if 0 <= ny < H and 0 <= nx < W and grey[ny, nx] and (ny, nx) not in seen:
                seen.add((ny, nx))
                q.append((ny, nx))
    return seen


def to_path(pixels):
    """Horizontal runs, merged vertically when identical, as an SVG path."""
    rows = {}
    for y, x in pixels:
        rows.setdefault(y, []).append(x)
    runs = {}
    for y, xs in rows.items():
        xs.sort()
        r, start = [], xs[0]
        for a, b in zip(xs, xs[1:] + [None]):
            if b != a + 1:
                r.append((start, a + 1))
                start = b
        runs[y] = r
    rects, open_ = [], {}
    for y in range(H + 1):
        cur = set(runs.get(y, []))
        for run in list(open_):
            if run not in cur:
                rects.append((run[0], open_.pop(run), run[1] - run[0], y))
        for run in cur:
            open_.setdefault(run, y)
    return "".join(f"M{x} {y0}h{w}V{y1}h-{w}z" for x, y0, w, y1 in
                   ((x, y0, w, y1) for x, y0, w, y1 in rects))


building_px = {}
for n, seeds in SEEDS.items():
    px = set()
    for x, y in seeds:
        px |= flood(x, y)
    building_px[n] = px
taken = set().union(*building_px.values())


# The hatching is made of thin lines: cover it with a coarse grid of cells
# so the highlight reads as a solid area.
CELL = 6
cells = set()
for x0, y0, x1, y1 in HILL_BOXES:
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grey[y, x] and (y, x) not in taken:
                cells.add((y // CELL, x // CELL))
hill_px = {(cy * CELL + dy, cx * CELL + dx) for cy, cx in cells
           for dy in range(CELL) for dx in range(CELL)}

out = {"width": W, "height": H, "paths": {str(n): to_path(p) for n, p in building_px.items()}}
out["paths"]["7"] = to_path(hill_px)


def digits_box(cx, cy, r=16):
    """Bounding box of the dark legend digits around an approximate position."""
    ys, xs = np.where(img[cy - r:cy + r, cx - r:cx + r] < 100)
    # keep the cluster closest to the guess (ignore outlines nearby)
    d = (xs - r) ** 2 + (ys - r) ** 2
    keep = d < (r * 0.8) ** 2
    xs, ys = xs[keep] + cx - r, ys[keep] + cy - r
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


LABELS = {1: (673, 302), 2: (676, 646), 3: (620, 636), 4: (493, 619), 5: (356, 587),
          6: (199, 496), 7: (122, 423), 8: (260, 437), 9: (333, 455), 10: (363, 384),
          11: (290, 364), 12: (237, 358), 13: (166, 255), 14: (298, 272), 15: (311, 196),
          16: (441, 215), 17: (364, 137), 18: (240, 119), 19: (436, 83), 20: (561, 142)}
out["labels"] = {str(n): digits_box(*p) for n, p in LABELS.items()}
json.dump(out, sys.stdout, separators=(",", ":"))
