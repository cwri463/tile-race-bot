from PIL import Image, ImageOps
from utils.image_processor import ImageProcess


class Board:
    def get_teams_with_number(teams_dict, number):
        '''Function to get teams with a specific tile number'''
        matching_teams = []
        for team_name, team_info in teams_dict.items():
            if team_info.get("tile") == number:
                matching_teams.append(team_name)
        return matching_teams


    def generate_board(tiles, board_data, teams):
        '''Function to generate and save the game board image'''
        # Open the background image of the game board
        image = Image.open(r".\images\board_background.jpg")
        x, y = 80, 30  # Initial position to paste tiles on the board
        tile_counter = 0  # Counter for tracking the tile number

        # Loop through each tile and process it
        for tile in tiles:
            # Open the image of the current tile item and standardize the size
            img = Image.open(rf"images\{tiles[tile]['item-picture']}")
            img = ImageProcess.image_resizer(img, board_data)
            width, height = img.size
            new_width = width + 100
            new_height = height + 100

            # Resize the image and add a white background
            result = Image.new(img.mode, (new_width, new_height), (255, 255, 255))
            result.paste(img, (50, 50), mask=img)

            # Add a black border to the tile
            border_size = 2
            bordered_img = ImageOps.expand(result, border=border_size, fill=(0, 0, 0))

            # Add item name as text to the tile image
            item_name = tiles[tile]["item-name"]
            ImageProcess.add_text_to_image(bordered_img, item_name)

            # Paste the tile on the game board
            image.paste(bordered_img, (x, y), mask=bordered_img)

            # Get teams located on this tile
            matching_teams = Board.get_teams_with_number(teams, tile_counter)

            # Paste team icons on the tile for each matching team
            if matching_teams:
                team_counter = 0
                team_placement_x = 15
                team_placement_y = 15
                for team in matching_teams:
                    player_image = Image.open(rf"images\{teams[team]['team_icon']}")
                    player_image = ImageProcess.player_image_resizer(player_image, board_data)
                    image.paste(player_image, (x + team_placement_x, y + team_placement_y), 
                                mask=player_image)

                    # Adjust placement coordinates for next team
                    team_counter += 1
                    if team_counter == 1:
                        team_placement_x += 90
                        team_placement_y += 65
                    elif team_counter == 2:
                        team_placement_x -= 90
                    elif team_counter == 3:
                        team_placement_x += 90
                        team_placement_y -= 65
                    elif team_counter == 4:
                        pass

            tile_counter += 1 # Increment tile counter for the next tile placement
            end_tile = len(tiles) # Get the counter for the final tile

            # Update position for the next tile placement based on the tile number
            if tile_counter < 8:
                start_x = x + 2 * board_data["tile-size"]
                end_x = start_x + 55
                end_y = y + board_data["tile-size"] + 10
                ImageProcess.add_arrow(image, start_x, y, end_x, end_y, tile_counter, end_tile)
                x = x + bordered_img.size[0] + 40 # Move right for the next tile in the same row

            elif tile_counter >= 8 and tile_counter <= 9:
                end_x = x + 10 + board_data["tile-size"]
                start_y = y + board_data["tile-size"] * 2 + 20
                end_y = start_y + 20
                ImageProcess.add_arrow(image, x, start_y, end_x, end_y, tile_counter, end_tile)
                y = y + bordered_img.size[1] + 25 # Move down for the next row of tiles

            elif tile_counter > 9 and tile_counter < 17:
                end_x = x - 30
                end_y = y + board_data["tile-size"] + 10
                ImageProcess.add_arrow(image, x, y, end_x, end_y, tile_counter, end_tile)
                x = x - bordered_img.size[0] - 40 # Move left for the next tile in the same row

            elif tile_counter >= 17 and tile_counter <= 18:
                end_x = x + 10 + board_data["tile-size"]
                start_y = y + board_data["tile-size"] * 2 + 20
                end_y = start_y + 20
                ImageProcess.add_arrow(image, x, start_y, end_x, end_y, tile_counter, end_tile)
                y = y + bordered_img.size[1] + 25  # Move down for the next row of tiles

            elif tile_counter > 18:
                start_x = x + 2 * board_data["tile-size"]
                end_x = start_x + 55
                end_y = y + board_data["tile-size"] + 10
                ImageProcess.add_arrow(image, start_x, y, end_x, end_y, tile_counter, end_tile)
                x = x + bordered_img.size[0] + 40 # Move right for the next tile in the same row

        # Save the final game board image
        image.save('game_board.png')
