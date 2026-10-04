# agora-atenas
Mapa mudo del ágora de Atenas

Quiz game: name the highlighted building of the Athenian Agora (5th c. BCE).

## Running

`buildings.json` is loaded with `fetch`, so serve the folder over HTTP instead of opening the file directly:

    python3 -m http.server   # then open http://localhost:8000

(GitHub Pages works as well.)

## Translating

All text lives in `buildings.json`: `names` maps each legend number to its name, `ui` holds the interface strings (keep the `{placeholders}`), and `lang` sets the language code used for sorting.

## Credits

Map `agora.png` by Madmedea, [World History Encyclopedia](https://www.worldhistory.org/image/192/agora-of-athens/), CC BY-SA. The building outlines in `index.html` are generated from it by `tools/regions.py`.

## Agora c. AD 150

`atenas-150-dc.html` is the same game on the 2nd-century plan. The map `agora-150-dc.webp` is `Plan-of-the-agora-at-the-height-of-its-development-in-ca-AD-150.webp` with the printed names erased, and the names live in `buildings-150-dc.json` (same format as above). Delete an entry from `names` to leave that place out of the game. Map, marker positions and label positions are regenerated with `python3 tools/erase-labels-150.py` (its output goes into the `<script id="places">` block).
