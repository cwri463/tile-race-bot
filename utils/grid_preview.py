from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

TILE_GUTTER = 10
FONT_PATH   = "DejaVuSans-Bold.ttf"   # or any TTF available

def render_empty_grid(board: Dict[str, Any],
                      tiles: Dict[str, Dict[str, Any]],
                      out_file: str = "empty_board.png") -> Path:
    max_r = max(t["coords"][0] for t in tiles.values())
    max_c = max(t["coords"][1] for t in tiles.values())

    tile = int(board.get("tile-size", 100))
    gut  = TILE_GUTTER
    W = (max_c + 1) * (tile + gut) + gut
    H = (max_r + 1) * (tile + gut) + gut

    img  = Image.new("RGBA", (W, H), (45, 45, 45, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, tile // 4)

    # vertical grid + col numbers
    for c in range(max_c + 1):
        x = gut + c * (tile + gut)
        draw.rectangle([x, 0, x + tile, H], outline=(255,255,255,120), width=2)
        cx = x + tile // 2
        draw.text((cx, 5), str(c), fill="white", font=font, anchor="mm")

    # horizontal grid + row numbers
    for r in range(max_r + 1):
        y = gut + r * (tile + gut)
        draw.rectangle([0, y, W, y + tile], outline=(255,255,255,120), width=2)
        cy = y + tile // 2
        draw.text((5, cy), str(r), fill="white", font=font, anchor="lm")

    img.save(out_file)
    print(f"[grid] saved {out_file}  ({W}×{H})")
    return Path(out_file)
