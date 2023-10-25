import random


class game_utils:
    # Function to update the team's position on the board based on dice roll
    def update_team_tiles(teams_dict, dice_roll):
        teams_dict["tile"] += dice_roll


    # Function to update the last dice roll value for a team
    def update_last_roll(teams_dict, dice_roll):
        teams_dict["last_roll"] = dice_roll


    # Function to simulate rolling a dice with values 1, 2, and 3
    def roll_dice():
        return random.randint(1, 3) # Return a random integer between 1 and 3


    # Function to find the team name based on the user's Discord name
    def find_team_name(name, teams):
        team = None
        # Iterate through teams and check if the user's name is in the team's member list
        for team_name, team_data in teams.items():
            if str(name) in team_data["members"]:
                team = team_name
                break
        return team # Return the found team name (or None if not found)