from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FONT_PATH = Path("assets/fonts/DejaVuSans-Bold.ttf")

def render_empty_grid(board_data, tiles):
    tile = board_data.get("tile-size", 90)
    gutter = 10

    max_r = max(t["coords"][0] for t in tiles.values())
    max_c = max(t["coords"][1] for t in tiles.values())

    cols = max_c + 1
    rows = max_r + 1

    W = cols * (tile + gutter) + gutter
    H = rows * (tile + gutter) + gutter

    img = Image.new("RGBA", (W, H), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(str(FONT_PATH), tile // 4)
    except OSError:
        print(f"❌ Could not load font at {FONT_PATH}")
        font = ImageFont.load_default()

    # Draw tiles with their tile ID (e.g., tile0, tile1)
    for tid, t in tiles.items():
        r, c = t["coords"]
        x = gutter + c * (tile + gutter)
        y = gutter + r * (tile + gutter)

        draw.rectangle([x, y, x + tile, y + tile], outline=(255, 255, 255, 180), width=2)
        draw.text((x + 5, y + 5), tid, font=font, fill=(255, 255, 255, 255))

    # Draw vertical lines and column numbers
    for c in range(cols):
        x = gutter + c * (tile + gutter)
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 100), width=1)
        draw.text((x + tile // 2, 5), str(c), font=font, fill="white", anchor="mm")

    # Draw horizontal lines and row numbers
    for r in range(rows):
        y = gutter + r * (tile + gutter)
        draw.line([(0, y), (W, y)], fill=(255, 255, 255, 100), width=1)
        draw.text((5, y + tile // 2), str(r), font=font, fill="white", anchor="lm")

    out_file = "grid_preview.png"
    img.save(out_file)
    print(f"[grid] saved {out_file}  ({W}×{H})")
    return Path(out_file)
