#!/usr/bin/env python3
"""
Download two CSVs from Google Sheets (tiles & teams) and merge them into
game-config.json.  Requires two repo secrets:

    SHEET_CSV_URL          – tiles tab (Board)
    SHEET_TEAMS_CSV_URL    – teams tab (Teams)
"""
import csv, json, os, pathlib, tempfile, urllib.request, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "game-config.json"

TILES_URL  = os.getenv("SHEET_CSV_URL")
TEAMS_URL  = os.getenv("SHEET_TEAMS_CSV_URL")
if not (TILES_URL and TEAMS_URL):
    sys.exit("❌ Missing SHEET_CSV_URL or SHEET_TEAMS_CSV_URL")

def grab(url: str) -> pathlib.Path:
    tmp = tempfile.NamedTemporaryFile(delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    return pathlib.Path(tmp.name)

tiles_csv  = grab(TILES_URL)
teams_csv  = grab(TEAMS_URL)

# ---------------- load existing json so we keep board-config --------------
cfg = json.loads(JSON_PATH.read_text(encoding="utf-8"))

# ---------------- tiles ---------------------------------------------------
tiles = {}
with tiles_csv.open(newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    for idx, row in enumerate(reader):
        tiles[f"tile{idx}"] = {
            "item-name":    row["item-name"].strip(),
            "tile-desc":    row["tile-desc"].strip(),
            "item-picture": row["item-picture"].strip(),
            "coords":       [int(row["row"]), int(row["col"])],
            "next":         [t.strip() for t in row["nextTiles"].split(",") if t.strip()],
            "points":       int(row.get("points", "1")),
            "must-hit":     str(row.get("must-hit", "")).lower() == "true",
        }

# ---------------- teams ---------------------------------------------------
teams = {}
with teams_csv.open(newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        name = row["team-name"].strip()
        teams[name] = {
            "name":     name,
            "members":  [m.strip() for m in row["member-ids"].split(",") if m.strip()],
            "tile":     row["startTile"].strip(),
            "rerolls":  int(row.get("rerolls", "0")),
            "last_roll": 0,
        }

# ---------------- write back ---------------------------------------------
cfg["tiles"] = tiles
cfg["teams"] = teams
JSON_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
print(f"✅ wrote {len(tiles)} tiles and {len(teams)} teams → {JSON_PATH}")
