# utils/grid_preview.py  (updated for negative coords)
from pathlib import Path
from typing  import Dict, Any
from PIL import Image, ImageDraw, ImageFont

FONT_PATH   = Path("assets/fonts/DejaVuSans-Bold.ttf")
TILE_GUTTER = 10

def render_empty_grid(board: Dict[str, Any],
                      tiles: Dict[str, Dict[str, Any]],
                      out_file: str = "grid_preview.png") -> Path:
    tile = int(board.get("tile-size", 100))

    # --- extents --------------------------------------------------------
    rows = [t["coords"][0] for t in tiles.values()]
    cols = [t["coords"][1] for t in tiles.values()]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)

    n_rows = max_r - min_r + 1
    n_cols = max_c - min_c + 1

    W = n_cols * (tile + TILE_GUTTER) + TILE_GUTTER
    H = n_rows * (tile + TILE_GUTTER) + TILE_GUTTER

    img  = Image.new("RGBA", (W, H), (45, 45, 45, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(str(FONT_PATH), tile // 4)
    except OSError:
        font = ImageFont.load_default()

    # --- draw grid boxes & IDs -----------------------------------------
    for tid, t in tiles.items():
        r, c = t["coords"]
        # shift by min_r/min_c so every tile lands on canvas
        x = TILE_GUTTER + (c - min_c) * (tile + TILE_GUTTER)
        y = TILE_GUTTER + (r - min_r) * (tile + TILE_GUTTER)

        draw.rectangle([x, y, x + tile, y + tile],
                       outline=(255, 255, 255, 180), width=2)
        draw.text((x + 4, y + 4), tid, font=font, fill="white")

    # --- axis labels ----------------------------------------------------
    for idx, c in enumerate(range(min_c, max_c + 1)):
        x = TILE_GUTTER + idx * (tile + TILE_GUTTER) + tile // 2
        draw.text((x, 5), str(c), font=font, fill="white", anchor="mm")

    for idx, r in enumerate(range(min_r, max_r + 1)):
        y = TILE_GUTTER + idx * (tile + TILE_GUTTER) + tile // 2
        draw.text((5, y), str(r), font=font, fill="white", anchor="lm")

    img.save(out_file)
    print(f"[grid] saved {out_file}  ({W}×{H})")
    return Path(out_file)
