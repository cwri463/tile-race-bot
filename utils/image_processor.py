from PIL import Image, ImageDraw, ImageFont


class ImageProcess:
    def image_resizer(img, board_data):
        '''Function to resize an image maintaining aspect ratio based on specified tile size'''
        wpercent = board_data["tile-size"]/float(img.size[0])
        hsize = int((float(img.size[0])*float(wpercent)))
        img = img.resize((hsize, board_data["tile-size"]), Image.Resampling.LANCZOS)
        return img # Return the resized image


    def player_image_resizer(img, board_data):
        '''Function to resize a player image maintaining aspect ratio from specified player size'''
        wpercent = board_data["player-size"]/float(img.size[0])
        hsize = int((float(img.size[0])*float(wpercent)))
        img = img.resize((hsize, board_data["player-size"]), Image.Resampling.LANCZOS)
        return img # Return the resized player image


    def add_text_to_image(image, text):
        '''Function to add text to an image'''
        draw = ImageDraw.Draw(image)
        # Use Arial font with font size 18 (font and size can be changed)
        font = ImageFont.truetype("arial.ttf", 18)
        text_width, text_height = draw.textsize(text, font=font)
        x = (image.width - text_width) // 2 # Calculate X position to center the text horizontally
        y = image.height - text_height - 10 # Calculate Y position to place the text at the bottom
        draw.text((x, y), text, font=font, fill=(0, 0, 0))  # Add black text to the image


    def add_arrow(image, x, y, end_x, end_y, tile_counter, end_tile):
        '''Function to add a directional arrow and line to an image'''
        draw = ImageDraw.Draw(image)
        if tile_counter == end_tile:
            return
        if tile_counter < 11:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 11 and tile_counter <= 12:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)],
                            fill=(255, 255, 255))
        elif tile_counter > 12 and tile_counter < 17:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 17 and tile_counter <= 18:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)],
                            fill=(255, 255, 255))
        elif tile_counter > 18 and tile_counter < 23:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 23 and tile_counter <= 24:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)],
                            fill=(255, 255, 255))
        elif tile_counter > 24 and tile_counter < 30:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 30 and tile_counter <= 34:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, y), (end_x + 5, y), (end_x, y - 10)],
                            fill=(255, 255, 255))
        elif tile_counter > 34 and tile_counter < 40:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 40 and tile_counter <= 41:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)],
                            fill=(255, 255, 255))
        elif tile_counter > 41 and tile_counter < 46:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x + 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 46 and tile_counter <= 47:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)],
                            fill=(255, 255, 255))
        elif tile_counter > 47 and tile_counter < 52:
            draw.line([(x, end_y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x, end_y - 5), (end_x - 10, end_y), (end_x, end_y + 5)],
                            fill=(255, 255, 255))
        elif tile_counter >= 52 and tile_counter != end_tile:
            draw.line([(end_x, y), (end_x, end_y)], fill=(255, 255, 255), width=5)
            draw.polygon([(end_x - 5, end_y), (end_x + 5, end_y), (end_x, end_y + 10)],
                            fill=(255, 255, 255))
        return
