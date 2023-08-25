import json


class etl:
    def load_config_file():
        with open('game-config.json', 'r') as json_file:
            game_config = json.load(json_file)
        board_data = game_config["board-config"]
        tiles = game_config["tiles"]
        teams = game_config["teams"]
        return board_data, tiles, teams


    def load_secrets():
        with open('secrets.json', 'r') as json_file:
            secrets = json.load(json_file)
        return secrets