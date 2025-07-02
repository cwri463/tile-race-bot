from __future__ import annotations

"""Board rendering helpers for the Tile‑Race bot (branching‑path edition).

This module turns the data‑driven *tiles* dictionary (containing grid
coordinates and outbound neighbours) into a single PNG called
``game_board.png`` and saves it in the bot’s working directory.

Key runtime expectations:
-------------------------
* ``tiles``  – dict produced by ``game-config.json`` where every value has
  • ``coords``  – [row, col] **zero‑based**
  • ``item-picture`` – filename found under ``images/``
  • ``item-name`` – title text shown on the tile
  • ``next`` – list[str] of following tile IDs (may be empty)
* ``board_data`` – typically comes from ``board-config`` section and must
  include ``tile-size`` (square size in px).

The image is laid out on an orthogonal grid with a constant gutter so it
remains readable even with diagonal edges.  All maths stay integer‑only
so Pillow anti‑aliasing isn’t triggered unnecessarily.
"""

from pathlib import Path
import math
from typing import Dict, Tuple, Any, List

from PIL import Image, ImageDraw

from utils.image_processor import ImageProcess

__all__ = ["generate_board"]

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
TILE_GUTTER = 10              # px between tiles
ARROW_WIDTH = 4               # px
ARROW_HEAD_LEN = 12           # px length of arrow‑head sides
ARROW_COLOUR = (255, 255, 255, 255)  # white, fully opaque

IMG_DIR = Path("images")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tile_top_left(row: int, col: int, tile_size: int) -> Tuple[int, int]:
    """Calculate top‑left pixel for a tile at (row, col) in the grid."""
    x = TILE_GUTTER + col * (tile_size + TILE_GUTTER)
    y = TILE_GUTTER + row * (tile_size + TILE_GUTTER)
    return x, y


def _tile_center(row: int, col: int, tile_size: int) -> Tuple[int, int]:
    """Return centre pixel of a tile (used for arrow start/end)."""
    tlx, tly = _tile_top_left(row, col, tile_size)
    cx = tlx + tile_size // 2
    cy = tly + tile_size // 2
    return cx, cy


def _draw_arrow(canvas: Image.Image, x1: int, y1: int, x2: int, y2: int) -> None:
    """Draw an arrow from (x1,y1) to (x2,y2) onto *canvas*.

    Uses a straight line plus a small filled triangle for the arrow head.
    """
    draw = ImageDraw.Draw(canvas)
    draw.line((x1, y1, x2, y2), fill=ARROW_COLOUR, width=ARROW_WIDTH)

    # arrow‑head triangle points
    angle = math.atan2(y2 - y1, x2 - x1)
    left_angle = angle + math.radians(150)  # 30° either side of line
    right_angle = angle - math.radians(150)

    lx = x2 + ARROW_HEAD_LEN * math.cos(left_angle)
    ly = y2 + ARROW_HEAD_LEN * math.sin(left_angle)
    rx = x2 + ARROW_HEAD_LEN * math.cos(right_angle)
    ry = y2 + ARROW_HEAD_LEN * math.sin(right_angle)

    draw.polygon([(x2, y2), (lx, ly), (rx, ry)], fill=ARROW_COLOUR)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_board(tiles: Dict[str, Dict[str, Any]],
                   board_data: Dict[str, Any],
                   teams: Dict[str, Any] | None = None) -> None:
    """Render the entire board to *game_board.png*.

    The *teams* param is currently ignored but kept for future per‑team
    overlays (e.g., player icons on current tile).
    """

    # -------------------- canvas size ------------------------------------ #
    tile_size = int(board_data["tile-size"])
    max_row = max(t["coords"][0] for t in tiles.values())
    max_col = max(t["coords"][1] for t in tiles.values())

    width = (max_col + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER
    height = (max_row + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER

    canvas = Image.new("RGBA", (width, height), (34, 34, 34, 255))

    # -------------------- pass 1: draw tiles ----------------------------- #
    for tid, tdata in tiles.items():
        row, col = map(int, tdata["coords"])
        tlx, tly = _tile_top_left(row, col, tile_size)

        # load + resize tile image
        img_path = IMG_DIR / tdata["item-picture"]
        if not img_path.is_file():
            raise FileNotFoundError(f"Missing tile image: {img_path}")

        tile_img = Image.open(img_path).convert("RGBA")
        tile_img = ImageProcess.image_resizer(tile_img, {"tile-size": tile_size})
        canvas.alpha_composite(tile_img, (tlx, tly))

        # add text centred within the tile square
        crop_box = canvas.crop((tlx, tly, tlx + tile_size, tly + tile_size))
        ImageProcess.add_text_to_image(crop_box, tdata["item-name"])
        canvas.alpha_composite(crop_box, (tlx, tly))

    # -------------------- pass 2: draw arrows ---------------------------- #
    for tid, tdata in tiles.items():
        row, col = tdata["coords"]
        x1, y1 = _tile_center(row, col, tile_size)
        for nxt in tdata.get("next", []):
            nrow, ncol = tiles[nxt]["coords"]
            x2, y2 = _tile_center(nrow, ncol, tile_size)
            _draw_arrow(canvas, x1, y1, x2, y2)
   # -------------------- pass 3: team tokens --------------------------- #
    token_dir   = Path("images/team_tokens")
    player_size = board_data.get("player-size", 40)
    token_radius = player_size // 2

    for idx, (tname, tdata) in enumerate(teams.items()):
        tile_id = tdata["tile"]
        if tile_id not in tiles:
            continue

        # tile centre
        row, col = tiles[tile_id]["coords"]
        cx, cy = _tile_center(row, col, tile_size)

        # if several teams share a tile, fan them diagonally
        offset = idx * (token_radius + 4)
        px = cx - token_radius + offset
        py = cy - token_radius + offset

        sprite_path = token_dir / f"{tname}.png"
        if sprite_path.is_file():
            sprite = Image.open(sprite_path).convert("RGBA")
            sprite = ImageProcess.player_image_resizer(sprite, {"player-size": player_size})
            canvas.alpha_composite(sprite, (px, py))
        else:
            # fallback coloured circle
            colour = tuple((hash(tname + str(i)) & 0x7F) + 64 for i in range(3)) + (255,)
            draw = ImageDraw.Draw(canvas)
            draw.ellipse([(px, py), (px + player_size, py + player_size)],
                         fill=colour, outline=(255, 255, 255, 255), width=2)
            # initial
            ImageProcess.add_text_to_image(
                canvas.crop((px, py, px + player_size, py + player_size)),
                tname[:1].upper(), font_size=player_size // 2
            )
            canvas.alpha_composite(canvas.crop((px, py, px + player_size, py + player_size)), (px, py))
    # -------------------- save result ------------------------------------ #
    output = Path("game_board.png")
    canvas.save(output)
    print(f"[board] saved {output}  ({width}×{height})")
