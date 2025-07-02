from __future__ import annotations
"""
utils/board.py – branching-path board renderer (auto-scaling)
"""

from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageOps

from utils.image_processor import ImageProcess

# --------------------------------------------------------------------------- #
# Tunables
# --------------------------------------------------------------------------- #
TILE_GUTTER = 10          # px between squares
ARROW_WIDTH = 4
TOKEN_DIR   = Path("images/team_tokens")

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _tile_top_left(row: int, col: int, tile_size: int) -> Tuple[int, int]:
    return (TILE_GUTTER + col * (tile_size + TILE_GUTTER),
            TILE_GUTTER + row * (tile_size + TILE_GUTTER))

def _tile_center(row: int, col: int, tile_size: int) -> Tuple[int, int]:
    x, y = _tile_top_left(row, col, tile_size)
    return x + tile_size // 2, y + tile_size // 2

def _draw_arrow(canvas: Image.Image, x1: int, y1: int, x2: int, y2: int):
    ImageProcess.draw_arrow(canvas, x1, y1, x2, y2, width=ARROW_WIDTH)

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def generate_board(tiles: Dict[str, Dict[str, Any]],
                   board_data: Dict[str, Any],
                   teams: Dict[str, Dict[str, Any]] | None = None) -> None:

    # ---------- auto-scale square size ----------
    TARGET_W = int(board_data.get("board-width", 1600))
    TARGET_H = int(board_data.get("board-height", 900))
    MIN_TILE = 32

    max_row = max(t["coords"][0] for t in tiles.values())
    max_col = max(t["coords"][1] for t in tiles.values())

    tiles_w = TARGET_W - TILE_GUTTER * (max_col + 1)
    tiles_h = TARGET_H - TILE_GUTTER * (max_row + 1)

    tile_size = int(min(tiles_w / (max_col + 1), tiles_h / (max_row + 1)))
    tile_size = max(tile_size, MIN_TILE)
    print(f"[SCALE] tile_size = {tile_size}px")

    # derive player sprite size
    player_size = max(16, int(tile_size * 0.75))
    scale_ctx = {"tile-size": tile_size, "player-size": player_size}

    width  = (max_col + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER
    height = (max_row + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER

    # ---------- background ----------
    bg_path = Path("images/backgrounds/board_bg.png")
    if bg_path.is_file():
        bg = Image.open(bg_path).convert("RGBA")
        bg = ImageOps.fit(bg, (width, height), Image.Resampling.LANCZOS, 0.5)
    else:
        bg = Image.new("RGBA", (width, height), (30, 30, 30, 255))
    canvas = bg.copy()

    # ---------- pass 1: tiles ----------
    for tid, t in tiles.items():
        r, c = t["coords"]
        x, y = _tile_top_left(r, c, tile_size)

        sprite_path = Path("images") / t["item-picture"]
        if not sprite_path.is_file():
            print(f"[WARN] missing art for {tid}: {sprite_path}")
            continue

        tile_img = Image.open(sprite_path).convert("RGBA")
        tile_img = ImageProcess.image_resizer(tile_img, scale_ctx)
        canvas.alpha_composite(tile_img, (x, y))

        caption_crop = canvas.crop((x, y, x + tile_size, y + tile_size))
        ImageProcess.add_text_to_image(caption_crop, t["item-name"])
        canvas.alpha_composite(caption_crop, (x, y))

    # ---------- pass 2: arrows ----------
    for tid, t in tiles.items():
        r, c = t["coords"]
        cx1, cy1 = _tile_center(r, c, tile_size)
        for nxt in t.get("next", []):
            if nxt not in tiles:
                print(f"[WARN] {tid} points to missing {nxt}")
                continue
            nr, nc = tiles[nxt]["coords"]
            cx2, cy2 = _tile_center(nr, nc, tile_size)
            _draw_arrow(canvas, cx1, cy1, cx2, cy2)

    # ---------- pass 3: team tokens ----------
    if teams:
        token_radius = player_size // 2

        # group teams by tile
        by_tile: Dict[str, list[str]] = {}
        for tname, tdata in teams.items():
            by_tile.setdefault(tdata["tile"], []).append(tname)

        for tile_id, team_list in by_tile.items():
            if tile_id not in tiles:
                continue
            row, col = tiles[tile_id]["coords"]
            cx, cy   = _tile_center(row, col, tile_size)

            # 2×2 grid offsets
            grid = [(-token_radius, -token_radius), ( token_radius, -token_radius),
                    (-token_radius,  token_radius), ( token_radius,  token_radius)]

            for idx, tname in enumerate(team_list[:4]):
                dx, dy = grid[idx]
                px, py = cx + dx, cy + dy

                sprite_file = TOKEN_DIR / f"{tname}.png"
                if sprite_file.is_file():
                    token = Image.open(sprite_file).convert("RGBA")
                    token = ImageProcess.player_image_resizer(token, scale_ctx)
                    canvas.alpha_composite(token, (px - token_radius, py - token_radius))
                else:
                    colour = tuple((hash(tname+str(i)) & 0x7F)+64 for i in range(3)) + (255,)
                    draw = ImageDraw.Draw(canvas)
                    draw.ellipse([(px - token_radius, py - token_radius),
                                  (px + token_radius, py + token_radius)],
                                 fill=colour, outline=(255,255,255,255), width=2)
                    crop = canvas.crop((px - token_radius, py - token_radius,
                                        px + token_radius, py + token_radius))
                    ImageProcess.add_text_to_image(crop, tname[:1].upper(),
                                                   font_size=player_size//2)
                    canvas.alpha_composite(crop, (px - token_radius, py - token_radius))

    # ---------- save ----------
    canvas.save("game_board.png")
    print(f"[board] saved game_board.png ({width}×{height})")
