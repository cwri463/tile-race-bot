import discord
import warnings
from load_config import ETL
from utils.board import Board
from utils.game_functions import GameUtils
warnings.filterwarnings("ignore")


# Set up Discord client with specific intents to handle messages and reactions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)


# Event handler for when the bot is ready and connected to the Discord server
@client.event
async def on_ready():
    # Delete all messages sent in the notifications channel when initialising new game.
    await client.get_channel(notification_channel_id).purge(check=is_me)

    # Delete all messages sent in the board channel when initialising new game.
    await client.get_channel(board_channel).purge(check=is_me)

    # Generate and send the initial game board to the specified channel
    Board.generate_board(tiles, board_data, teams)
    await client.get_channel(board_channel).send(file=discord.File('game_board.png'))
    print(f'{client.user} have logged in and are ready to play!')


# Event handler for incoming messages
@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Handle messages in the image submission channel
    if message.channel.id == image_channel_id:
        if message.attachments:
            await message.add_reaction('✅')
            await message.add_reaction('❌')
            # Find the team name of the user who submitted the image
            team_name = GameUtils.find_team_name(message.author, teams)
            # user_id = 165559954516738049

            # Notify in the designated notification channel about the image submission
            await client.get_channel(notification_channel_id) \
                        .send(f"**{team_name}** just uploaded a drop - " \
                              + "waiting for approval.") #  from <@{user_id}>")

    # Handle messages in the notification channel with the "!reroll" command
    if message.channel.id == notification_channel_id and message.content == "!reroll":

        # Find the team name of the user who sent the command
        team_name = GameUtils.find_team_name(message.author, teams)

        # Check if the team has remaining rerolls
        if teams[team_name]["rerolls"] == 0:
            await client.get_channel(notification_channel_id) \
                        .send(f'Requesting team **{team_name}** ' \
                              +'does not have any rerolls left - too bad!')
        else:
            # Perform a reroll for the team and update the game state
            old_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
            last_roll = teams[team_name]["last_roll"]
            teams[team_name]["tile"] -= last_roll

            # Check the amount of tiles left and correct the diceroll hereafter
            if teams[team_name]['tile'] + 3 <= len(tiles) - 1:
                # Extra check to account for the chance to roll a 4
                if teams[team_name]['tile'] + 5 <= len(tiles) - 1:
                    max_dice = 3
                    bonus_roll = True
                else:
                    max_dice = 3
                    bonus_roll = False       
            else:
                max_dice = len(tiles) - teams[team_name]['tile'] - 1
                bonus_roll = False

            # Check if any of the next 3 tiles is a must hit tile
            next_tiles = []
            for x in range(max_dice):
                next_tiles.append(tiles[f"tile{teams[team_name]['tile'] + x + 1}"]["must-hit"])


            dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
            GameUtils.update_team_tiles(teams[team_name], dice_roll)
            GameUtils.update_last_roll(teams[team_name], dice_roll)
            new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
            new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

            # Only use the reroll token if the new roll is different from the last roll
            if last_roll != dice_roll:
                teams[team_name]["rerolls"] -= 1
            
            # Roll again if the tile is a roll again tile
            if new_tile_name == 'Roll again':
                await client.get_channel(notification_channel_id) \
                            .send(f'Drop for **{old_tile_name}** was approved, rolling for **{team_name}** \
                                    \nRoll is: **{dice_roll}** \
                                    \nNew tile is **{new_tile_name}**! \
                                    \nRolling again ...')
                dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
                GameUtils.update_team_tiles(teams[team_name], dice_roll)
                GameUtils.update_last_roll(teams[team_name], dice_roll)
                new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
                new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

                await client.get_channel(notification_channel_id) \
                            .send(f'Roll is: **{dice_roll}** \
                                \nNew tile is **{new_tile_name}** good luck! \
                                \n**Description:** {new_tile_desc}.')
                # Delete all messages sent in the board channel before posting a new board
                await client.get_channel(board_channel).purge(check=is_me)

                # Updating the board and posting it in the channel
                Board.generate_board(tiles, board_data, teams)
                await client.get_channel(board_channel).send(file=discord.File('game_board.png'))
                return

            # Notify the team about the reroll result and update the game board
            await client.get_channel(notification_channel_id) \
                        .send(f'Rerolling for team **{team_name}** from **{old_tile_name}** ... 🎲\
                              \nNew roll is: **{dice_roll}** \
                              \nNew tile is **{new_tile_name}** you have **{teams[team_name]["rerolls"]}** rerolls left! \
                              \n**Description:** {new_tile_desc}.')

            # Delete all messages sent in the board channel before posting a new board
            await client.get_channel(board_channel).purge(check=is_me)

            # Updating the board and posting it in the channel
            Board.generate_board(tiles, board_data, teams)
            await client.get_channel(board_channel).send(file=discord.File('game_board.png'))


def is_me(m):
    """Function used for bot to delete bot messages"""
    return m.author == client.user


# Event handler for adding reactions to messages
@client.event
async def on_reaction_add(reaction, user):
    # Ignore reactions from other bots
    if user.bot:
        return

    # Handle reactions in the image submission channel
    if reaction.message.channel.id == image_channel_id and str(reaction.emoji) == '✅':

        # Find the team name of the user who submitted the image
        team_name = GameUtils.find_team_name(reaction.message.author, teams)
        old_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
        
        # Check if the last completed tile was the end tile
        if old_tile_name == 'END (ARAM)':
            await client.get_channel(notification_channel_id) \
                    .send(f'Drop for **{old_tile_name}** was approved. \
                          \n**{team_name}** have completet the board!! \
                          \nThank you for playing and better luck next time to the other teams!')
            return

        # Check the amount of tiles left and correct the diceroll hereafter
        if teams[team_name]['tile'] + 3 <= len(tiles) - 1:
            # Extra check to account for the chance to roll a 4
            if teams[team_name]['tile'] + 5 <= len(tiles) - 1:
                max_dice = 3
                bonus_roll = True
            else:
                max_dice = 3
                bonus_roll = False       
        else:
            max_dice = len(tiles) - teams[team_name]['tile'] - 1
            bonus_roll = False

        # Roll dice based on previous restrictions
        dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)

        # Check if any of the next 3 tiles is a must hit tile
        next_tiles = []
        for x in range(max_dice):
            next_tiles.append(tiles[f"tile{teams[team_name]['tile'] + x + 1}"]["must-hit"])

        if True in next_tiles:

            # Get the tile which is a must hit tile
            index_of_true = next_tiles.index(True) + 1

            # Overwrite the previous dice roll to land on the must hit tile if higher
            if dice_roll > index_of_true:
                dice_roll = index_of_true
        else:
            pass

        # Update the team's position based on the dice roll
        GameUtils.update_team_tiles(teams[team_name], dice_roll)
        GameUtils.update_last_roll(teams[team_name], dice_roll)
        new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
        new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

        # Roll again if the tile is a roll again tile
        if new_tile_name == 'Roll again':
            await client.get_channel(notification_channel_id) \
                        .send(f'Drop for **{old_tile_name}** was approved, rolling for **{team_name}** \
                                \nRoll is: **{dice_roll}** \
                                \nNew tile is **{new_tile_name}**! \
                                \nRolling again ...')
            dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
            GameUtils.update_team_tiles(teams[team_name], dice_roll)
            GameUtils.update_last_roll(teams[team_name], dice_roll)
            new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
            new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

            await client.get_channel(notification_channel_id) \
                        .send(f'Roll is: **{dice_roll}** \
                             \nNew tile is **{new_tile_name}** good luck! \
                             \n**Description:** {new_tile_desc}.')
            # Delete all messages sent in the board channel before posting a new board
            await client.get_channel(board_channel).purge(check=is_me)

            # Updating the board and posting it in the channel
            Board.generate_board(tiles, board_data, teams)
            await client.get_channel(board_channel).send(file=discord.File('game_board.png'))
            return

        # Notify the team about the roll result and update the game board
        await client.get_channel(notification_channel_id) \
                    .send(f'Drop for **{old_tile_name}** was approved, rolling for **{team_name}** \
                          \nRoll is: **{dice_roll}** \
                          \nNew tile is **{new_tile_name}** good luck! \
                          \n**Description:** {new_tile_desc}.')

        # Delete all messages sent in the board channel before posting a new board
        await client.get_channel(board_channel).purge(check=is_me)

        # Updating the board and posting it in the channel
        Board.generate_board(tiles, board_data, teams)
        await client.get_channel(board_channel).send(file=discord.File('game_board.png'))

    # Handle reactions in the image submission channel when the drop is declined
    elif reaction.message.channel.id == image_channel_id and str(reaction.emoji) == '❌':

        # Find the team name of the submitted image and notify the team about the declined drop
        team_name = GameUtils.find_team_name(reaction.message.author, teams)
        await client.get_channel(notification_channel_id) \
                    .send(f'Drop was declined for **{team_name}**' \
                          +'check your image and try again!\n')


if __name__ == "__main__":
    # Load configuration data, secrets, and initialize channels and tokens
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

    # 'develop' for hidden develop channels 'production' for live channels 
    if "develop" in secrets:
   

    image_channel_id = secrets["image_channel_id"]  # Channel ID for image submissions
    notification_channel_id = secrets["notification_channel_id"]  # Channel ID for notifications
    board_channel = secrets["board_channel"]  # Channel ID for the game board display

    # Run the Discord bot with the specified token
    client.run(secrets["discord-bot-token"])
