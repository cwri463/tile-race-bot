import random


class game_utils:
    def update_team_tiles(teams_dict, dice_roll):
        teams_dict["tile"] += dice_roll


    def update_last_roll(teams_dict, dice_roll):
        teams_dict["last_roll"] = dice_roll


    def roll_dice():
        return random.randint(1, 3)


    def find_team_name(name, teams):
        team = None
        for team_name, team_data in teams.items():
            if str(name) in team_data["members"]:
                team = team_name
                break
        return team