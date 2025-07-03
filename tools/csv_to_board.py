#!/usr/bin/env python3
"""tools/csv_to_board.py – import Tiles + Teams from Google Sheets.

Requires two repo secrets:
  SHEET_CSV_URL          – CSV export of the Board tab
  SHEET_TEAMS_CSV_URL    – CSV export of the Teams tab
"""

from __future__ import annotations
import csv, json, os, sys, tempfile, urllib.request, pathlib
from typing import Dict, Any, List

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def download(url: str) -> pathlib.Path:
    tmp = tempfile.NamedTemporaryFile(delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    return pathlib.Path(tmp.name)

def parse_bool(val: str | None) -> bool:
    return str(val).strip().lower() in {"true", "1", "yes"}

# --------------------------------------------------------------------------- #
# Environment
# --------------------------------------------------------------------------- #
TILES_URL  = os.getenv("SHEET_CSV_URL")
TEAMS_URL  = os.getenv("SHEET_TEAMS_CSV_URL")
if not (TILES_URL and TEAMS_URL):
    sys.exit("❌  SHEET_CSV_URL and/or SHEET_TEAMS_CSV_URL not set")

ROOT      = pathlib.Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "game-config.json"

# --------------------------------------------------------------------------- #
# 1) Download CSVs
# --------------------------------------------------------------------------- #
tiles_csv  = download(TILES_URL)
teams_csv  = download(TEAMS_URL)

# --------------------------------------------------------------------------- #
# 2) Parse Tiles
# --------------------------------------------------------------------------- #
tiles: Dict[str, Dict[str, Any]] = {}
with tiles_csv.open(newline="", encoding="utf-8") as fh:
    rdr = csv.DictReader(fh)
    for idx, row in enumerate(rdr):
        # Validate required coords
        try:
            r = int(row["row"])
            c = int(row["col"])
        except (ValueError, KeyError):
            raise ValueError(f"Row {idx+2}: invalid row/col values → {row['row']}, {row['col']}")

        tile_id = f"tile{idx}"
        tiles[tile_id] = {
            "item-name":    row["item-name"].strip(),
            "item-picture": row["item-picture"].strip(),
            "tile-desc":    row.get("tile-desc", "").strip(),
            "coords":       [r, c],
            "next":         [t.strip() for t in row.get("nextTiles", "").split(",") if t.strip()],
            "points":       int(row.get("points") or 1),
            "must-hit":     parse_bool(row.get("must-hit")),
        }

print(f"✅  Parsed {len(tiles)} tiles")

# --------------------------------------------------------------------------- #
# 3) Validate next-tile references
# --------------------------------------------------------------------------- #
all_ids = set(tiles.keys())
for tid, t in tiles.items():
    for nxt in t["next"]:
        if nxt not in all_ids:
            raise ValueError(f"❌  Tile '{tid}' references missing ID '{nxt}'")

# --------------------------------------------------------------------------- #
# 4) Parse Teams
# --------------------------------------------------------------------------- #
teams: Dict[str, Dict[str, Any]] = {}
with teams_csv.open(newline="", encoding="utf-8") as fh:
    rdr = csv.DictReader(fh)
    for row in rdr:
        name = row["team-name"].strip()
        if not name:
            continue
        teams[name] = {
             "name":       row["team-name"],
             "members":    row["member-ids"].split(";"),
               "tile":       row["startTile"].strip(),
              "rerolls":    int(row.get("rerolls", "0")),
              "skips":      int(row.get("skips", "0")),     
              "roleId":     row.get("roleId", "").strip(),
                  }
    
print(f"✅  Parsed {len(teams)} teams")

# --------------------------------------------------------------------------- #
# 5) Merge into game-config.json
# --------------------------------------------------------------------------- #
if JSON_PATH.exists():
    cfg = json.loads(JSON_PATH.read_text(encoding="utf-8"))
else:
    cfg = {}

cfg["tiles"] = tiles
cfg["teams"] = teams

new_json = json.dumps(cfg, indent=2, ensure_ascii=False)
if JSON_PATH.exists() and JSON_PATH.read_text(encoding="utf-8") == new_json:
    print("ℹ️  game-config.json unchanged – nothing to update")
else:
    JSON_PATH.write_text(new_json, encoding="utf-8")
    print(f"💾  Wrote {JSON_PATH} ({len(tiles)} tiles, {len(teams)} teams)")
