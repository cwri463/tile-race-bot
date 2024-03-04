import random


class GameUtils:
    def update_team_tiles(teams_dict, dice_roll):
        '''Function to update the team's position on the board based on dice roll'''
        teams_dict["tile"] += dice_roll


    def update_last_roll(teams_dict, dice_roll):
        '''Function to update the last dice roll value for a team'''
        teams_dict["last_roll"] = dice_roll


    def roll_dice(max_roll):
        '''Function to simulate rolling a dice with values 1, 2, and 3'''
        if max_roll != 3:
            return random.randint(1, max_roll)
        
        percentage_chance = 0.05
        if random.random() < percentage_chance:
            return 5
        else:
            return random.randint(1, max_roll) # Return a random integer between 1 and 3


    def find_team_name(name, teams):
        '''Function to find the team name based on the user's Discord name'''
        team = None
        # Iterate through teams and check if the user's name is in the team's member list
        for team_name, team_data in teams.items():
            if str(name) in team_data["members"]:
                team = team_name
                break
        return team # Return the found team name (or None if not found)
