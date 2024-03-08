import random


class GameUtils:
    def update_team_tiles(teams_dict, dice_roll):
        '''Function to update the team's position on the board based on dice roll'''
        teams_dict["tile"] += dice_roll


    def update_last_roll(teams_dict, dice_roll):
        '''Function to update the last dice roll value for a team'''
        teams_dict["last_roll"] = dice_roll


    def roll_dice(max_roll, bonus_roll):
        '''Function to simulate rolling a dice with max value as input and a chance to roll high'''
        if not bonus_roll:
            return random.randint(1, max_roll)
        else:
            percentage_chance = 0.05
            if random.random() < percentage_chance: # 5% chance to roll 4
                return 4
            else:
                return random.randint(1, max_roll) # Return a random integer between 1 and max_roll


    def find_team_name(name, teams):
        '''Function to find the team name based on the user's Discord name'''
        team = None
        # Iterate through teams and check if the user's name is in the team's member list
        for team_name, team_data in teams.items():
            if str(name) in team_data["members"]:
                team = team_name
                break
        return team # Return the found team name (or None if not found)
