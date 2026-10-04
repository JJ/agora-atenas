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
