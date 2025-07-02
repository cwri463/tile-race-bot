#!/usr/bin/env python3
"""
Download the board CSV from Google Sheets and merge it into game-config.json.

• Expects an environment variable SHEET_CSV_URL pointing to a public-CSV export
  like: https://docs.google.com/spreadsheets/d/<ID>/export?format=csv
• Leaves the existing "board-config" and "teams" sections untouched.
• Overwrites the entire "tiles" section.

Run locally with:
    SHEET_CSV_URL=https://... python tools/csv_to_board.py
"""

import csv, json, os, pathlib, urllib.request, tempfile, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "game-config.json"
CSV_URL = os.environ.get("SHEET_CSV_URL")

if not CSV_URL:
    sys.exit("❌ SHEET_CSV_URL env-var not set")

# ------------------------------------------------------------
# 1. download CSV to a temp file
# ------------------------------------------------------------
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    print("⏬  downloading CSV …")
    urllib.request.urlretrieve(CSV_URL, tmp.name)
    csv_path = pathlib.Path(tmp.name)

# ------------------------------------------------------------
# 2. load existing JSON so we keep board-config & teams
# ------------------------------------------------------------
cfg = json.loads(JSON_PATH.read_text(encoding="utf-8"))
cfg.setdefault("tiles", {})

# ------------------------------------------------------------
# 3. build fresh tiles dict
# ------------------------------------------------------------
tiles = {}
with csv_path.open(newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    for idx, row in enumerate(reader):
        tiles[f"tile{idx}"] = {
            "item-name":    row["item-name"].strip(),
            "tile-desc":    row["tile-desc"].strip(),
            "item-picture": row["item-picture"].strip(),
            "points":       int(row.get("points", "1")),
            "must-hit":     str(row.get("must-hit", "")).lower() == "true",
        }

cfg["tiles"] = tiles
JSON_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
print(f"✅ wrote {len(tiles)} tiles → {JSON_PATH}")
