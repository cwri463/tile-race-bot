# load_config.py
import json
from pathlib import Path
from typing import Any, Dict, Tuple

class ETL:
    @staticmethod
    def load() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Load tiles and teams from game-config.json.
        Returns: (board_data, tiles, teams)
        """
        config_path = Path("game-config.json")
        if not config_path.is_file():
            raise FileNotFoundError("game-config.json not found – run tools/csv_to_board.py first")

        with config_path.open(encoding="utf-8") as f:
            cfg = json.load(f)

        # Default board settings
        board_data = {
            "tile-size":    100,
            "player-size":   40,
            "board-width": 1920,
            "board-height": 1080,
        }

        # Update from file if available
        board_data.update(cfg.get("board", {}))

        tiles = cfg.get("tiles", {})
        teams = cfg.get("teams", {})

        if not tiles or not teams:
            raise ValueError("Missing tiles or teams in game-config.json")

        return board_data, tiles, teams
