from __future__ import annotations
"""
utils/image_processor.py – Pillow helpers
• Square tile sprite with white border
• Caption rendered inside tile, 2 px above bottom border
• Optional player token resizer
• Simple straight arrow
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
FONT_PATH = Path("assets/fonts/DejaVuSans-Bold.ttf")
DEFAULT_FONT_SIZE = 14
BORDER_COLOUR = (255, 255, 255, 255)
TILE_BG = (45, 45, 45, 255)
TEXT_COLOUR = (255, 255, 255, 255)

# --------------------------------------------------------------------------- #
# ImageProcess
# --------------------------------------------------------------------------- #
class ImageProcess:
    # ---------------------- Tile sprites ------------------------------ #
    @staticmethod
    def image_resizer(img: Image.Image, board_data: dict) -> Image.Image:
        """Return a square sprite exactly tile-size × tile-size with a caption band inside."""
        tile_size = int(board_data["tile-size"])
        caption_band = 20  # px reserved at bottom

        # Create blank tile
        tile = Image.new("RGBA", (tile_size, tile_size), TILE_BG)

        # Scale artwork to fit inside the area above the caption band
        max_art_h = tile_size - caption_band - 6  # 6 px breathing room
        img = img.convert("RGBA")
        img.thumbnail((tile_size - 6, max_art_h), Image.Resampling.LANCZOS)

        # Center-paste art
        x = (tile_size - img.width) // 2
        y = (max_art_h - img.height) // 2 + 3
        tile.alpha_composite(img, (x, y))

        # White border
        draw = ImageDraw.Draw(tile)
        draw.rectangle([(0, 0), (tile_size - 1, tile_size - 1)], outline=BORDER_COLOUR, width=2)
        return tile

    # ---------------------- Player tokens ----------------------------- #
    @staticmethod
    def player_image_resizer(img: Image.Image, board_data: dict) -> Image.Image:
        player_size = int(board_data["player-size"])
        img = img.convert("RGBA")
        img.thumbnail((player_size, player_size), Image.Resampling.LANCZOS)
        token = Image.new("RGBA", (player_size, player_size), (0, 0, 0, 0))
        x = (player_size - img.width) // 2
        y = (player_size - img.height) // 2
        token.alpha_composite(img, (x, y))
        return token

    # ---------------------- Captions ---------------------------------- #
   @staticmethod
    def add_text_to_image(image: Image.Image, text: str, *, font_size: int | None = None) -> None:
        if not text:
            return

        target_w = image.width - 8          # 4-px margin either side
        font_size = font_size or DEFAULT_FONT_SIZE

    # Try progressively smaller fonts until it fits
        while font_size >= 8:
            try:
                font = ImageFont.truetype(str(FONT_PATH), font_size)
            except FileNotFoundError:
                font = ImageFont.load_default()
            text_w = ImageDraw.Draw(image).textlength(text, font=font)
            if text_w <= target_w:
               break
            font_size -= 1                  # step down size

        draw = ImageDraw.Draw(image)
        x = (image.width - text_w) // 2
        y = image.height - font_size - 2    # 2 px above border
        draw.text((x, y), text, font=font, fill=TEXT_COLOUR)


    # ---------------------- Arrow primitive --------------------------- #
    @staticmethod
    def draw_arrow(canvas: Image.Image, x1: int, y1: int, x2: int, y2: int, *, width: int = 4):
        import math
        draw = ImageDraw.Draw(canvas)
        draw.line((x1, y1, x2, y2), fill=TEXT_COLOUR, width=width)

        head_len = 12
        angle = math.atan2(y2 - y1, x2 - x1)
        left = (x2 - head_len * math.cos(angle - math.pi / 6),
                y2 - head_len * math.sin(angle - math.pi / 6))
        right = (x2 - head_len * math.cos(angle + math.pi / 6),
                 y2 - head_len * math.sin(angle + math.pi / 6))
        draw.polygon([left, (x2, y2), right], fill=TEXT_COLOUR)
