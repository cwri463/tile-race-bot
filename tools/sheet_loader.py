# tools/sheet_loader.py
from __future__ import annotations
import csv, os, tempfile, urllib.request
from pathlib import Path
from typing import Dict, Any

def _download(url: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    return Path(tmp.name)

def _bool(x: str | None) -> bool:
    return str(x).strip().lower() in {"1", "true", "yes"}

def load_from_sheet() -> tuple[dict[str, Any],
                               dict[str, dict[str, Any]],
                               dict[str, dict[str, Any]]]:
    """Return (board_data, tiles, teams) fresh from the CSV URLs."""
    tiles_url  = os.getenv("SHEET_CSV_URL")
    teams_url  = os.getenv("SHEET_TEAMS_CSV_URL")
    if not (tiles_url and teams_url):
        raise RuntimeError("SHEET_CSV_URL / SHEET_TEAMS_CSV_URL not set")

    rows: list[dict[str, str]] = []
    with _download(tiles_url).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    tiles: dict[str, dict[str, Any]] = {}
    for idx, row in enumerate(rows):
        r, c = int(row["row"]), int(row["col"])
        tiles[f"tile{idx}"] = {
            "item-name":    row["item-name"].strip(),
            "item-picture": row["item-picture"].strip(),
            "tile-desc":    row.get("tile-desc", "").strip(),
            "coords":       [r, c],
            "next":        [t.strip() for t in row.get("nextTiles", "").split(',') if t.strip()],
            "points":       int(row.get("points") or 1),
            "must-hit":     _bool(row.get("must-hit")),
        }

    teams: dict[str, dict[str, Any]] = {}
    with _download(teams_url).open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = row["team-name"].strip()
            if not name:
                continue
            teams[name] = {
                "name":      name,
                "members":   row["member-ids"].split(";"),
                "tile":      row["startTile"].strip(),
                "rerolls":   int(row.get("rerolls", "0")),
                "skips":     int(row.get("skips",   "0")),
                "roleId":    row.get("roleId", "").strip(),
            }

    # board-wide config stays inside game-config.json; reuse current
    board_data = {
        "board-width":  board_data.get("board-width", 1600),
        "board-height": board_data.get("board-height", 900),
        "tile-size":    board_data.get("tile-size",  100),
        "player-size":  board_data.get("player-size", 60),
    }
    return board_data, tiles, teams
