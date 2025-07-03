# tools/sheet_loader.py
# ------------------------------------------------------------
# Load Tiles + Teams fresh from the Google-Sheet CSV exports.
# Used by the /syncsheet slash command.
# ------------------------------------------------------------
from __future__ import annotations
import csv, json, os, tempfile, urllib.request
from pathlib import Path
from typing import Dict, Any

# ------------------------------------------------------------
# Helper: download URL → temp file
# ------------------------------------------------------------
def _download(url: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    return Path(tmp.name)

def _bool(x: str | None) -> bool:
    return str(x).strip().lower() in {"1", "true", "yes"}

# ------------------------------------------------------------
# Main loader
# ------------------------------------------------------------
def load_from_sheet() -> tuple[
        Dict[str, Any],                       # board_data
        Dict[str, Dict[str, Any]],            # tiles
        Dict[str, Dict[str, Any]],            # teams
]:
    tiles_url  = os.getenv("SHEET_CSV_URL")
    teams_url  = os.getenv("SHEET_TEAMS_CSV_URL")
    if not (tiles_url and teams_url):
        raise RuntimeError("SHEET_CSV_URL or SHEET_TEAMS_CSV_URL env-vars not set")

    # ---------- 1) Tiles ----------
    with _download(tiles_url).open(newline="", encoding="utf-8") as fh:
        tile_rows = list(csv.DictReader(fh))

    tiles: Dict[str, Dict[str, Any]] = {}
    for idx, row in enumerate(tile_rows):
        try:
            r, c = int(row["row"]), int(row["col"])
        except (KeyError, ValueError):
            raise ValueError(f"Row {idx+2}: invalid row/col → {row.get('row')} / {row.get('col')}")

        tiles[f"tile{idx}"] = {
            "item-name":    row["item-name"].strip(),
            "item-picture": row["item-picture"].strip(),
            "tile-desc":    row.get("tile-desc", "").strip(),
            "coords":       [r, c],
            "next":        [t.strip() for t in row.get("nextTiles", "").split(",") if t.strip()],
            "points":       int(row.get("points", "1") or 1),
            "must-hit":     _bool(row.get("must-hit")),
        }

    # ---------- 2) Teams ----------
    with _download(teams_url).open(newline="", encoding="utf-8") as fh:
        team_rows = list(csv.DictReader(fh))

    teams: Dict[str, Dict[str, Any]] = {}
    for row in team_rows:
        name = row["team-name"].strip()
        if not name:
            continue
        teams[name] = {
            "name":     name,
            "members":  [m.strip() for m in row["member-ids"].split(";") if m.strip()],
            "tile":     row["startTile"].strip(),
            "rerolls":  int(row.get("rerolls", "0") or 0),
            "skips":    int(row.get("skips",   "0") or 0),
            "roleId":   row.get("roleId", "").strip(),
            "last_roll": 0,
        }

    # ---------- 3) Board-wide config ----------
    # Defaults:
    board_data: Dict[str, Any] = {
        "board-width":  1600,
        "board-height": 900,
        "tile-size":    100,
        "player-size":  60,
    }

    # Merge in existing values from game-config.json (if present)
    cfg_path = Path("game-config.json")
    if cfg_path.is_file():
        try:
            existing = json.loads(cfg_path.read_text("utf-8"))
            board_data.update(existing.get("board-config", {}))
        except Exception as e:
            print(f"[WARN] couldn't read board-config from {cfg_path}: {e}")

    return board_data, tiles, teams
