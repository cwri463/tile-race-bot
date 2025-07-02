#!/usr/bin/env python3
"""
CSV  ➜  game-config.json   (branching board edition)
    Needs env var: SHEET_CSV_URL
"""
import csv, json, os, pathlib, urllib.request, tempfile, sys, itertools

ROOT      = pathlib.Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "game-config.json"
CSV_URL   = os.environ["SHEET_CSV_URL"]

# download to temp
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    urllib.request.urlretrieve(CSV_URL, tmp.name)
    csv_path = pathlib.Path(tmp.name)

cfg = json.loads(JSON_PATH.read_text())      # keep teams & board-config
tiles = {}

with csv_path.open(newline="", encoding="utf-8") as fh:
    rdr = csv.DictReader(fh)
    for idx, row in enumerate(rdr):
        tile_id = f"tile{idx}"
        tiles[tile_id] = {
            "item-name":    row["item-name"].strip(),
            "tile-desc":    row["tile-desc"].strip(),
            "item-picture": row["item-picture"].strip(),
            "coords":       [int(row["row"]), int(row["col"])],
            "next":         [t.strip() for t in row["nextTiles"].split(",") if t.strip()],
            "points":       int(row.get("points", "1")),
            "must-hit":     str(row.get("must-hit", "")).lower() == "true"
        }

cfg["tiles"] = tiles
JSON_PATH.write_text(json.dumps(cfg, indent=2))
print(f"✅ wrote {len(tiles)} tiles → {JSON_PATH}")
