from PIL import Image, ImageDraw, ImageOps, ImageFont


class image_process:
    def image_resizer(img, board_data):
        wpercent = (board_data["tile-size"]/float(img.size[0]))
        hsize = int((float(img.size[0])*float(wpercent)))
        img = img.resize((hsize, board_data["tile-size"]), Image.Resampling.LANCZOS)
        return img


    def add_text_to_image(image, text):
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 25)  # You can change the font and size
        text_width, text_height = draw.textsize(text, font=font)
        x = (image.width - text_width) // 2
        y = image.height - text_height - 10
        draw.text((x, y), text, font=font, fill=(0, 0, 0))  # Black text