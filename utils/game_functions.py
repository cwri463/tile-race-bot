import random
from typing import Dict


class GameUtils:
    # ------------------------------------------------------------------ #
    # Dice & board helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def update_team_tiles(team: Dict, dice_roll: int) -> None:
        """Advance *team* exactly *dice_roll* tiles on the board."""
        team["tile"] += dice_roll

    @staticmethod
    def update_last_roll(team: Dict, dice_roll: int) -> None:
        """Store the last roll so reroll logic can undo it."""
        team["last_roll"] = dice_roll

    @staticmethod
    def roll_dice(max_roll: int, bonus_roll: bool) -> int:
        """
        Roll from 1-max_roll.  
        If *bonus_roll* is True, there’s a 5 % chance to return 4 (for boards that allow it).
        """
        if bonus_roll and random.random() < 0.05:
            return 4
        return random.randint(1, max_roll)

    # ------------------------------------------------------------------ #
    # Team lookup
    # ------------------------------------------------------------------ #
    @staticmethod
    def find_team_name(user, teams: Dict[str, Dict]) -> str | None:
        """
        Return the team name this Discord *user* belongs to.
        Logs a warning if the user ID isn’t found in any team’s ``members`` list.
        """
        uid = str(user.id)                       # always compare as string
        for name, data in teams.items():
            if uid in data.get("members", []):
                return name

        # --- not found → warn in logs ---
        print(f"[WARN] No team found for user {uid} ({user.display_name})")
        return None

