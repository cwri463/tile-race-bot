import csv
import json
import os
import requests

SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")
if not SHEET_CSV_URL:
    raise RuntimeError("SHEET_CSV_URL environment variable not set")

response = requests.get(SHEET_CSV_URL)
if response.status_code != 200:
    raise RuntimeError(f"Failed to fetch CSV data: {response.status_code}")

lines = response.text.strip().splitlines()
reader = csv.DictReader(lines)

tiles = {}
for idx, row in enumerate(reader):
    tile_id = f"tile{idx}"
    try:
        coords = [
            int(row["row"].strip()) if row["row"].strip() else 0,
            int(row["col"].strip()) if row["col"].strip() else 0,
        ]
    except (ValueError, KeyError):
        raise RuntimeError(f"Invalid or missing 'row'/'col' in row {idx + 1}")

    try:
        points = int(row.get("points", "1") or 1)
    except ValueError:
        raise RuntimeError(f"Invalid 'points' value in row {idx + 1}: {row.get('points')}")

    tile = {
        "item-name": row["item-name"],
        "item-picture": row["item-picture"],
        "tile-desc": row.get("tile-desc", ""),
        "coords": coords,
        "next": [n.strip() for n in row.get("nextTiles", "").split(",") if n.strip()],
        "points": points,
        "must-hit": row.get("must-hit", "").strip().lower() in ["true", "1", "yes"],
    }

    tiles[tile_id] = tile

# Write the board config
os.makedirs("config", exist_ok=True)
with open("config/game-config.json", "w", encoding="utf-8") as f:
    json.dump({"tiles": tiles}, f, indent=2)

print(f"✅ Wrote config/game-config.json with {len(tiles)} tiles")
