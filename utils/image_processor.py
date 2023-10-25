from PIL import Image, ImageDraw, ImageFont


class image_process:
    # Function to resize an image maintaining aspect ratio based on specified tile size
    def image_resizer(img, board_data):
        wpercent = (board_data["tile-size"]/float(img.size[0]))
        hsize = int((float(img.size[0])*float(wpercent)))
        img = img.resize((hsize, board_data["tile-size"]), Image.Resampling.LANCZOS)
        return img # Return the resized image
    
    
    # Function to resize a player image maintaining aspect ratio based on specified player size
    def player_image_resizer(img, board_data):
        wpercent = (board_data["player-size"]/float(img.size[0]))
        hsize = int((float(img.size[0])*float(wpercent)))
        img = img.resize((hsize, board_data["player-size"]), Image.Resampling.LANCZOS)
        return img # Return the resized player image


    # Function to add text to an image
    def add_text_to_image(image, text):
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 18)  # Use Arial font with font size 18 (font and size can be changed)
        text_width, text_height = draw.textsize(text, font=font)
        x = (image.width - text_width) // 2 # Calculate X position to center the text horizontally
        y = image.height - text_height - 10 # Calculate Y position to place the text at the bottom with a small offset
        draw.text((x, y), text, font=font, fill=(0, 0, 0))  # Add black text to the image