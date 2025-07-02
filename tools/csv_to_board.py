#!/usr/bin/env python3
"""tools/csv_to_board.py – single-source board + team loader

Reads two Google-Sheet CSV exports (tiles tab and teams tab) and writes a
**game-config.json** file with the *_branching-board_* schema expected by the
new utils/board.py renderer.

Required repo secrets (Settings ▸ Secrets ▸ Actions):
---------------------------------------------------
• SHEET_CSV_URL         – public CSV link for the *Board* tab
• SHEET_TEAMS_CSV_URL   – public CSV link for the *Teams* tab

Both URLs can be obtained from Google Sheets ➜ *File ▸ Share ▸ Publish to
web ▸ CSV* while the desired tab is selected.

The script is idempotent – if the generated JSON is identical to what is
already on disk the subsequent git commit is skipped by the workflow.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import pathlib
import tempfile
import urllib.request
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "game-config.json"

TILES_URL  = os.getenv("SHEET_CSV_URL")
TEAMS_URL  = os.getenv("SHEET_TEAMS_CSV_URL")
if not (TILES_URL and TEAMS_URL):
    sys.exit("❌  SHEET_CSV_URL and/or SHEET_TEAMS_CSV_URL secrets not set")


def _download(url: str) -> pathlib.Path:
    """Download *url* to a NamedTemporaryFile and return its path."""
    tmp = tempfile.NamedTemporaryFile(delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    return pathlib.Path(tmp.name)


def _parse_bool(val: str) -> bool:
    return str(val).strip().lower() in {"true", "yes", "1"}


# ---------------------------------------------------------------------------
# 1) Load existing JSON – keeps board-config or any other top-level keys
# ---------------------------------------------------------------------------
if JSON_PATH.exists():
    cfg: Dict[str, Any] = json.loads(JSON_PATH.read_text(encoding="utf-8"))
else:
    cfg = {}

# ---------------------------------------------------------------------------
# 2) Tiles
# ---------------------------------------------------------------------------

tiles_csv = _download(TILES_URL)
tiles: Dict[str, Dict[str, Any]] = {}

with tiles_csv.open(newline="", encoding="utf-8") as fh:
    rdr = csv.DictReader(fh)
    for idx, row in enumerate(rdr):
        # Required columns check
        if not row.get("row") or not row.get("col"):
            print(f"⚠️  Skipping row {idx} – missing row/col: {row}")
            continue

        tile_id = f"tile{idx}"
        try:
            coords = [int(row["row"].strip()), int(row["col"].strip())]
        except ValueError as exc:
            print(f"⚠️  Invalid coords at row {idx}: {row['row']},{row['col']} -> {exc}")
            continue

        next_list: List[str] = [t.strip() for t in row.get("nextTiles", "").split(",") if t.strip()]

     tile = {
    "item-name":    row["item-name"],
    "item-picture": row["item-picture"],
    "tile-desc":    row.get("tile-desc", ""),
    "coords": [
        int(row["row"].strip()) if row["row"].strip() else 0,
        int(row["col"].strip()) if row["col"].strip() else 0,
    ],
    "next": [n.strip() for n in row.get("nextTiles", "").split(",") if n.strip()],
    "points": int(row.get("points", "1") or 1),
    "must-hit": row.get("must-hit", "").strip().lower() in ["true", "1", "yes"],
}

print(f"✅  Parsed {len(tiles)} tiles from sheet")

# ---------------------------------------------------------------------------
# 3) Teams
# ---------------------------------------------------------------------------

teams_csv = _download(TEAMS_URL)
teams: Dict[str, Dict[str, Any]] = {}

with teams_csv.open(newline="", encoding="utf-8") as fh:
    rdr = csv.DictReader(fh)
    for row in rdr:
        name = row["team-name"].strip()
        if not name:
            continue
        member_ids = [m.strip() for m in row.get("member-ids", "").split(",") if m.strip()]
        teams[name] = {
            "name":      name,
            "members":   member_ids,
            "tile":      row.get("startTile", "tile0").strip(),
            "rerolls":   int(row.get("rerolls") or 0),
            "last_roll": 0,
        }

print(f"✅  Parsed {len(teams)} teams from sheet")

# ---------------------------------------------------------------------------
# 4) Write combined JSON
# ---------------------------------------------------------------------------

cfg["tiles"] = tiles
cfg["teams"] = teams

new_json = json.dumps(cfg, indent=2, ensure_ascii=False)

# Only write if changed – prevents needless git commits
if JSON_PATH.exists() and JSON_PATH.read_text(encoding="utf-8") == new_json:
    print("ℹ️  game-config.json unchanged – nothing to commit")
else:
    JSON_PATH.write_text(new_json, encoding="utf-8")
    print(f"✅  game-config.json updated ({len(tiles)} tiles, {len(teams)} teams)")
