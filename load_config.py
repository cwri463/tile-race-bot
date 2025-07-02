import json
import os
from pathlib import Path


class ETL:
    """
    Helper class for loading the static game data (board, tiles, teams)
    and runtime secrets.
    """

    @staticmethod
    def load_config_file():
        """Read board/tiles/teams from game-config.json"""
        with open("game-config.json", "r", encoding="utf-8") as f:
            game_cfg = json.load(f)

        board_data = game_cfg["board-config"]
        tiles = game_cfg["tiles"]
        teams = game_cfg["teams"]
        return board_data, tiles, teams

    @staticmethod
    def load_secrets():
        """
        Return a dict with at least {"DISCORD_TOKEN": "..."}.

        • In production (Railway/Fly/Render) we expect the token to be
          supplied as an environment variable.

        • During local development we still allow a secrets.json file
          so you don’t have to export variables in your shell.
        """
        token = os.getenv("DISCORD_TOKEN")
        if token:                          # preferred cloud path
            return {"DISCORD_TOKEN": token}

        # --- fallback for local runs ---
        secrets_file = Path("secrets.json")
        if secrets_file.exists():
            with secrets_file.open("r", encoding="utf-8") as f:
                return json.load(f)

        raise RuntimeError(
            "DISCORD_TOKEN env-var not set and secrets.json not found"
        )
