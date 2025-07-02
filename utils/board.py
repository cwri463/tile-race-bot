from __future__ import annotations
"""
utils/board.py – branching-path board renderer
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List
import math

from PIL import Image, ImageDraw, ImageOps

from utils.image_processor import ImageProcess

# --------------------------------------------------------------------------- #
# Tunables
# --------------------------------------------------------------------------- #
TILE_GUTTER = 10  # px between squares
ARROW_WIDTH = 4
TOKEN_DIR = Path("images/team_tokens")

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _tile_top_left(row: int, col: int, tile_size: int) -> Tuple[int, int]:
    x = TILE_GUTTER + col * (tile_size + TILE_GUTTER)
    y = TILE_GUTTER + row * (tile_size + TILE_GUTTER)
    return x, y

def _tile_center(row: int, col: int, tile_size: int) -> Tuple[int, int]:
    tlx, tly = _tile_top_left(row, col, tile_size)
    return tlx + tile_size // 2, tly + tile_size // 2

def _draw_arrow(canvas: Image.Image, x1: int, y1: int, x2: int, y2: int):
    ImageProcess.draw_arrow(canvas, x1, y1, x2, y2, width=ARROW_WIDTH)

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def generate_board(tiles: Dict[str, Dict[str, Any]],
                   board_data: Dict[str, Any],
                   teams: Dict[str, Dict[str, Any]] | None = None) -> None:
    tile_size = int(board_data["tile-size"])
    max_row = max(t["coords"][0] for t in tiles.values())
    max_col = max(t["coords"][1] for t in tiles.values())

    width = (max_col + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER
    height = (max_row + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER

    # ---- load / prepare background ------------------------------------
    bg_path = Path("images/backgrounds/board_bg.png")
    if bg_path.is_file():
        bg = Image.open(bg_path).convert("RGBA")
        bg = ImageOps.fit(bg, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    else:
        bg = Image.new("RGBA", (width, height), (30, 30, 30, 255))

    canvas = bg.copy()

    # ---------------- pass 1: draw tiles -------------------------------- #
    for tid, t in tiles.items():
        r, c = t["coords"]
        x, y = _tile_top_left(r, c, tile_size)

        sprite_path = Path("images") / t["item-picture"]
        if not sprite_path.is_file():
            print(f"[WARN] missing art for {tid}: {sprite_path}")
            continue

        tile_img = Image.open(sprite_path).convert("RGBA")
        tile_img = ImageProcess.image_resizer(tile_img, board_data)
        canvas.alpha_composite(tile_img, (x, y))

        caption_crop = canvas.crop((x, y, x + tile_size, y + tile_size))
        ImageProcess.add_text_to_image(caption_crop, t["item-name"])
        canvas.alpha_composite(caption_crop, (x, y))

    # ---------------- pass 2: arrows ------------------------------------ #
    for tid, t in tiles.items():
        r, c = t["coords"]
        cx1, cy1 = _tile_center(r, c, tile_size)
        for nxt in t.get("next", []):
            if nxt not in tiles:
                print(f"[WARN] {tid} points to missing {nxt} – skipped")
                continue
            nr, nc = tiles[nxt]["coords"]
            cx2, cy2 = _tile_center(nr, nc, tile_size)
            _draw_arrow(canvas, cx1, cy1, cx2, cy2)

    # ---------------- pass 3: team tokens ------------------------------- #
    if teams:
        player_size = int(board_data.get("player-size", 40))
        token_radius = player_size // 2

        by_tile: Dict[str, list[str]] = {}
        for tname, tdata in teams.items():
            by_tile.setdefault(tdata["tile"], []).append(tname)

        for tile_id, team_list in by_tile.items():
            if tile_id not in tiles:
                continue
            row, col = tiles[tile_id]["coords"]
            cx, cy = _tile_center(row, col, tile_size)

            grid_pos = [
                (-token_radius, -token_radius),
                ( token_radius, -token_radius),
                (-token_radius,  token_radius),
                ( token_radius,  token_radius),
            ]

            for idx, tname in enumerate(team_list[:4]):
                dx, dy = grid_pos[idx]
                px = cx + dx
                py = cy + dy

                sprite_file = TOKEN_DIR / f"{tname}.png"
                if sprite_file.is_file():
                    token = Image.open(sprite_file).convert("RGBA")
                    token = ImageProcess.player_image_resizer(token, board_data)
                    canvas.alpha_composite(token, (px - token_radius, py - token_radius))
                else:
                    colour = tuple((hash(tname + str(i)) & 0x7F) + 64 for i in range(3)) + (255,)
                    draw = ImageDraw.Draw(canvas)
                    draw.ellipse(
                        [(px - token_radius, py - token_radius),
                         (px + token_radius, py + token_radius)],
                        fill=colour, outline=(255, 255, 255, 255), width=2
                    )
                    crop = canvas.crop((px - token_radius, py - token_radius,
                                        px + token_radius, py + token_radius))
                    ImageProcess.add_text_to_image(
                        crop, tname[:1].upper(), font_size=player_size // 2
                    )
                    canvas.alpha_composite(crop, (px - token_radius, py - token_radius))

    # ---------------- save ---------------------------------------------- #
    canvas.save("game_board.png")
    print(f"[board] saved game_board.png  ({width}×{height})")
