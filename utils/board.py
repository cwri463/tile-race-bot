"""utils/board.py – branch‑path board renderer (supports negative coords)

• Auto‑scales board to the min/max row/col so tiles at (‑1,‑3) work.
• Draws tiles, arrows, team tokens, captions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Tuple, List
from PIL import Image, ImageDraw, ImageOps

from utils.image_processor import ImageProcess

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
TILE_GUTTER = 10          # px gap around every square
ARROW_WIDTH = 4
TOKEN_DIR   = Path("images/team_tokens")  # teama.png etc.

# ---------------------------------------------------------------------------
# Helpers that respect negative coords (need min_row/min_col offsets)
# ---------------------------------------------------------------------------

def _tile_top_left(row: int, col: int, tile_size: int,
                   min_row: int, min_col: int) -> Tuple[int, int]:
    """Return pixel (x, y) of the tile's top‑left corner."""
    x = TILE_GUTTER + (col - min_col) * (tile_size + TILE_GUTTER)
    y = TILE_GUTTER + (row - min_row) * (tile_size + TILE_GUTTER)
    return x, y


def _tile_center(row: int, col: int, tile_size: int,
                 min_row: int, min_col: int) -> Tuple[int, int]:
    tlx, tly = _tile_top_left(row, col, tile_size, min_row, min_col)
    return tlx + tile_size // 2, tly + tile_size // 2


def _draw_arrow(canvas: Image.Image, x1: int, y1: int, x2: int, y2: int):
    ImageProcess.draw_arrow(canvas, x1, y1, x2, y2, width=ARROW_WIDTH)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_board(tiles: Dict[str, Dict[str, Any]],
                   board_data: Dict[str, Any],
                   teams: Dict[str, Dict[str, Any]] | None = None) -> None:
    """Render game_board.png accommodating negative row/col indices."""

    # gather extents
    rows = [t["coords"][0] for t in tiles.values()]
    cols = [t["coords"][1] for t in tiles.values()]
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)

    tile_size = int(board_data.get("tile-size", 100))
    width  = (max_col - min_col + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER
    height = (max_row - min_row + 1) * (tile_size + TILE_GUTTER) + TILE_GUTTER

    # ---------------- background ----------------
    bg_path = Path("images/backgrounds/board_bg.png")
    if bg_path.is_file():
        bg = Image.open(bg_path).convert("RGBA")
        bg = ImageOps.fit(bg, (width, height), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (width, height), (30, 30, 30, 255))

    canvas = bg.copy()

    # ---------------- draw tiles ----------------
    for tid, t in tiles.items():
        r, c = t["coords"]
        x, y = _tile_top_left(r, c, tile_size, min_row, min_col)

        sprite_path = Path("images") / t["item-picture"]
        if sprite_path.is_file():
            tile_img = Image.open(sprite_path).convert("RGBA")
            tile_img = ImageProcess.image_resizer(tile_img, board_data)
            canvas.alpha_composite(tile_img, (x, y))
        else:
            # placeholder box
            draw = ImageDraw.Draw(canvas)
            draw.rectangle([x, y, x + tile_size, y + tile_size], outline=(255,0,0), width=2)

        # caption inside tile
        crop = canvas.crop((x, y, x + tile_size, y + tile_size))
        ImageProcess.add_text_to_image(crop, t["item-name"])
        canvas.alpha_composite(crop, (x, y))

    # ---------------- arrows ----------------
    for tid, t in tiles.items():
        r, c = t["coords"]
        cx1, cy1 = _tile_center(r, c, tile_size, min_row, min_col)
        for nxt in t.get("next", []):
            if nxt not in tiles:
                continue
            nr, nc = tiles[nxt]["coords"]
            cx2, cy2 = _tile_center(nr, nc, tile_size, min_row, min_col)
            _draw_arrow(canvas, cx1, cy1, cx2, cy2)

    # ---------------- team tokens ----------------
    if teams:
        player_size  = int(board_data.get("player-size", 40))
        token_radius = player_size // 2
        by_tile: Dict[str, List[str]] = {}
        for name, d in teams.items():
            by_tile.setdefault(d["tile"], []).append(name)

        for tid, team_list in by_tile.items():
            if tid not in tiles:
                continue
            row, col = tiles[tid]["coords"]
            cx, cy = _tile_center(row, col, tile_size, min_row, min_col)

            grid_pos = [(-token_radius, -token_radius),
                        ( token_radius, -token_radius),
                        (-token_radius,  token_radius),
                        ( token_radius,  token_radius)]

            for idx, tname in enumerate(team_list[:4]):
                dx, dy = grid_pos[idx]
                px, py = cx + dx, cy + dy

                sprite = TOKEN_DIR / f"{tname}.png"
                if sprite.is_file():
                    tok = Image.open(sprite).convert("RGBA")
                    tok = ImageProcess.player_image_resizer(tok, board_data)
                    canvas.alpha_composite(tok, (px - token_radius, py - token_radius))
                else:
                    # coloured circle fallback
                    colour = tuple((hash(tname+str(i)) & 0x7F) + 64 for i in range(3)) + (255,)
                    draw = ImageDraw.Draw(canvas)
                    draw.ellipse([(px-token_radius, py-token_radius),
                                  (px+token_radius, py+token_radius)],
                                 fill=colour, outline=(255,255,255))

    canvas.save("game_board.png")
    print(f"[board] saved game_board.png  ({width}×{height})")
