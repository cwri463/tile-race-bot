import json


class etl:
    # Function to load configuration data from the game-config.json file
    def load_config_file():
        with open('game-config.json', 'r') as json_file:
            game_config = json.load(json_file)  # Load game configuration data from JSON file
        board_data = game_config["board-config"]  # Extract board configuration data
        tiles = game_config["tiles"]  # Extract tile data
        teams = game_config["teams"]  # Extract team data
        return board_data, tiles, teams  # Return extracted data


    # Function to load secrets from the secrets.json file
    def load_secrets():
        with open('secrets.json', 'r') as json_file:
            secrets = json.load(json_file)  # Load secrets data from JSON file
        return secrets  # Return loaded secrets data