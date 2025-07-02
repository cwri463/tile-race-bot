from __future__ import annotations

"""utils/image_processor.py – helpers for Pillow image handling.

This version guarantees every tile sprite is a **perfect square** of size
``board_data['tile-size']`` with the item art centred, a dark background,
and a crisp white border.  Caption text is rendered *below* the square to
avoid overlapping the art.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Configurable paths / constants (relative to repo root)
# --------------------------------------------------------------------------- #
FONT_PATH = Path("assets/fonts/DejaVuSans-Bold.ttf")
DEFAULT_FONT_SIZE = 16
BORDER_COLOUR = (255, 255, 255, 255)  # white
TILE_BG        = (45, 45, 45, 255)    # dark grey
TEXT_COLOUR    = (255, 255, 255, 255)  # white text

# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
class ImageProcess:
    """Stateless helpers used by utils/board.py."""

    # ---------------------- Tile sprites ------------------------------ #
    @staticmethod
    def image_resizer(img: Image.Image, board_data: dict) -> Image.Image:
        """Return a *square* sprite exactly tile-size × tile-size.

        1. Scales *img* to fit inside the square, preserving aspect ratio.
        2. Pastes it centred on a dark background.
        3. Adds a 2‑pixel white border.
        """
        tile_size = int(board_data["tile-size"])

        # 1️⃣  resize art to fit inside the square
        img = img.convert("RGBA")
        img.thumbnail((tile_size - 4, tile_size - 4), Image.Resampling.LANCZOS)

        # 2️⃣  create blank tile & centre‑paste the art
        tile = Image.new("RGBA", (tile_size, tile_size), TILE_BG)
        x = (tile_size - img.width)  // 2
        y = (tile_size - img.height) // 2
        tile.alpha_composite(img, (x, y))

        # 3️⃣  border
        draw = ImageDraw.Draw(tile)
        draw.rectangle([(0, 0), (tile_size - 1, tile_size - 1)], outline=BORDER_COLOUR, width=2)
        return tile

    # ---------------------- Player tokens ----------------------------- #
    @staticmethod
    def player_image_resizer(img: Image.Image, board_data: dict) -> Image.Image:
        """Resize a player token (square) maintaining aspect ratio."""
        player_size = int(board_data["player-size"])
        img = img.convert("RGBA")
        img.thumbnail((player_size, player_size), Image.Resampling.LANCZOS)
        token = Image.new("RGBA", (player_size, player_size), (0, 0, 0, 0))
        x = (player_size - img.width)  // 2
        y = (player_size - img.height) // 2
        token.alpha_composite(img, (x, y))
        return token

    # ---------------------- Text overlays ----------------------------- #
    @staticmethod
    def add_text_to_image(image: Image.Image, text: str, *, font_size: int | None = None) -> None:
        """Draw *text* centred horizontally at the *bottom* of *image*.

        The text baseline sits **4 px below** the image’s bottom border so the
        caller must ensure extra canvas height exists if needed.
        """
        if not text:
            return
        font_size = font_size or DEFAULT_FONT_SIZE
        try:
            font = ImageFont.truetype(str(FONT_PATH), font_size)
        except FileNotFoundError:
            font = ImageFont.load_default()

        draw = ImageDraw.Draw(image)
        text_width = draw.textlength(text, font=font)
        text_height = font_size

        x = (image.width - text_width) // 2
        y = image.height - text_height + 4  # below the square tile

        draw.text((x, y), text, font=font, fill=TEXT_COLOUR)

    # ---------------------- Arrow primitive --------------------------- #
    @staticmethod
    def draw_arrow(canvas: Image.Image, x1: int, y1: int, x2: int, y2: int, *, width: int = 4):
        """Simple straight arrow (line + triangular head) on *canvas*."""
        draw = ImageDraw.Draw(canvas)
        draw.line((x1, y1, x2, y2), fill=TEXT_COLOUR, width=width)

        # arrow head
        import math
        head_len = 12
        angle = math.atan2(y2 - y1, x2 - x1)
        left  = (x2 - head_len * math.cos(angle - math.pi / 6), y2 - head_len * math.sin(angle - math.pi / 6))
        right = (x2 - head_len * math.cos(angle + math.pi / 6), y2 - head_len * math.sin(angle + math.pi / 6))
        draw.polygon([left, (x2, y2), right], fill=TEXT_COLOUR)
