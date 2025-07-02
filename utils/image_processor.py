import os
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.path.join("assets", "fonts", "DejaVuSans-Bold.ttf")

class ImageProcess:
    @staticmethod
    def image_resizer(img: Image.Image, board_data: dict) -> Image.Image:
        wpercent = board_data["tile-size"] / float(img.size[0])
        hsize = int(float(img.size[1]) * wpercent)
        return img.resize((board_data["tile-size"], hsize), Image.Resampling.LANCZOS)

    @staticmethod
    def player_image_resizer(img: Image.Image, board_data: dict) -> Image.Image:
        wpercent = board_data["player-size"] / float(img.size[0])
        hsize = int(float(img.size[1]) * wpercent)
        return img.resize((board_data["player-size"], hsize), Image.Resampling.LANCZOS)

    @staticmethod
    def add_text_to_image(image: Image.Image, text: str) -> None:
        draw = ImageDraw.Draw(image)
        font_size = 18
        font = ImageFont.truetype(FONT_PATH, font_size)  # ✅ using your bundled font
        text_width = draw.textlength(text, font=font)
        text_height = font_size
        x = (image.width - text_width) // 2
        y = image.height - text_height - 10
        draw.text((x, y), text, font=font, fill=(0, 0, 0))

    @staticmethod
    def add_arrow(image: Image.Image, x: int, y: int, end_x: int, end_y: int, tile_counter: int, end_tile: int) -> None:
        if tile_counter == end_tile:
            return

        draw = ImageDraw.Draw(image)

        def h_line(): draw.line([(x, end_y), (end_x, end_y)], fill="white", width=5)
        def v_line(): draw.line([(end_x, y), (end_x, end_y)], fill="white", width=5)

        if tile_counter < 11:                          h_line(); draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)], fill="white")
        elif 11 <= tile_counter <= 12:                v_line(); draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)], fill="white")
        elif 12 < tile_counter < 17:                  h_line(); draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)], fill="white")
        elif 17 <= tile_counter <= 18:                v_line(); draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)], fill="white")
        elif 18 < tile_counter < 23:                  h_line(); draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)], fill="white")
        elif 23 <= tile_counter <= 24:                v_line(); draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)], fill="white")
        elif 24 < tile_counter < 30:                  h_line(); draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)], fill="white")
        elif 30 <= tile_counter <= 34:                v_line(); draw.polygon([(end_x - 5, y),  (end_x + 5, y),  (end_x, y - 10)], fill="white")
        elif 34 < tile_counter < 40:                  h_line(); draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)], fill="white")
        elif 40 <= tile_counter <= 41:                v_line(); draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)], fill="white")
        elif 41 < tile_counter < 46:                  h_line(); draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)], fill="white")
        elif 46 <= tile_counter <= 47:                v_line(); draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)], fill="white")
        elif 47 < tile_counter < 52:                  h_line(); draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)], fill="white")
        elif tile_counter >= 52 and tile_counter != end_tile:
                                                     v_line(); draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)], fill="white")
