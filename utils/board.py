from PIL import Image, ImageOps
from utils.image_processor import image_process


class board:
    def get_teams_with_number(teams_dict, number):
        matching_teams = []
        for team_name, team_info in teams_dict.items():
            if team_info.get("tile") == number:
                matching_teams.append(team_name)
        return matching_teams


    def generate_board(tiles, board_data, teams):
        image = Image.open(r".\images\board_background.jpg")
        x, y = 80, 30
        tile_counter = 0
        for tile in tiles:
            img = Image.open(rf"images\{tiles[tile]['item-picture']}")
            img = image_process.image_resizer(img, board_data)
            width, height = img.size
            new_width = width + 100
            new_height = height + 100
            result = Image.new(img.mode, (new_width, new_height), (255, 255, 255))
            result.paste(img, (50, 50), mask=img)
            border_size = 2
            bordered_img = ImageOps.expand(result, border=border_size, fill=(0, 0, 0))  # Black border
            
            # Add text to the image
            item_name = tiles[tile]["item-name"]
            image_process.add_text_to_image(bordered_img, item_name)
            image.paste(bordered_img, (x, y), mask=bordered_img)

            matching_teams = board.get_teams_with_number(teams, tile_counter)

            if matching_teams:
                team_counter = 1
                team_placement_x = 15
                team_placement_y = 15
                for team in matching_teams:
                    if team_counter == 1:
                        player_image = Image.open(rf"images\{teams[team]['team_icon']}")
                        player_image = image_process.player_image_resizer(player_image, board_data)
                        image.paste(player_image, (x+team_placement_x, y+team_placement_y), mask=player_image)
                        team_counter += 1
                        team_placement_x += 90
                        team_placement_y += 65
                    elif team_counter == 2:
                        player_image = Image.open(rf"images\{teams[team]['team_icon']}")
                        player_image = image_process.player_image_resizer(player_image, board_data)
                        image.paste(player_image, (x+team_placement_x, y+team_placement_y), mask=player_image)
                        team_counter += 1
                        team_placement_x -= 90
                    elif team_counter == 3:
                        player_image = Image.open(rf"images\{teams[team]['team_icon']}")
                        player_image = image_process.player_image_resizer(player_image, board_data)
                        image.paste(player_image, (x+team_placement_x, y+team_placement_y), mask=player_image)
                        team_counter += 1
                        team_placement_x += 90
                        team_placement_y -= 65
                    elif team_counter == 4:
                        player_image = Image.open(rf"images\{teams[team]['team_icon']}")
                        player_image = image_process.player_image_resizer(player_image, board_data)
                        image.paste(player_image, (x+team_placement_x, y+team_placement_y), mask=player_image)
            
            tile_counter += 1
            if tile_counter < 8:
                x = x + bordered_img.size[0] + 40
            elif tile_counter >= 8 and tile_counter <= 9:
                y = y + bordered_img.size[1] + 25
            elif tile_counter > 9 and tile_counter < 17:
                x = x - bordered_img.size[0] - 40
            elif tile_counter >= 17 and tile_counter <= 18:
                y = y + bordered_img.size[1] + 25
            elif tile_counter > 19:
                x = x + bordered_img.size[0] + 40
        image.save('game_board.png')