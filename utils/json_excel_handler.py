import json
import pandas as pd


def json_to_excel(tiles):
    '''Function to convert tiles object to excel format'''
    df = pd.DataFrame()

    for item in tiles:
        temp_df = pd.json_normalize(tiles[item])
        temp_df["tile"] = item
        df = pd.concat([df, temp_df])

    df.to_excel(r"./Tile-race-tiles.xlsx")


def excel_to_json(df):
    '''Function to convert tiles from excel format to json'''
    tiles = {}

    for _, row in df.iterrows():
        tiles[f"{row['tile']}"] = {
            "item-name": row['item-name'],
            "tile-desc": row['tile-desc'],
            "item-picture": row['item-picture'],
            "must-hit": row['must-hit']
        }

    with open('from_excel.json', 'w') as fp:
        json.dump(tiles, fp)


if __name__ == "__main__":
    operation = "to_json"
    #operation = "to_excel"

    if operation == "to_excel":
        with open('game-config.json', 'r') as json_file:
            game_config = json.load(json_file)  # Load game configuration data from JSON file
        tiles = game_config["tiles"]  # Extract tile data
        json_to_excel(tiles)

    elif operation == "to_json":
        df = pd.read_excel(r"./Tile-race-tiles.xlsx")
        excel_to_json(df)
