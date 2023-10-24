import discord
import warnings
from etl.load_config import etl
from utils.board import board
from utils.game_functions import game_utils
warnings.filterwarnings("ignore")


intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    board.generate_board(tiles, board_data, teams)
    await client.get_channel(board_channel).send(file=discord.File('game_board.png'))
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.id == image_channel_id:
        if message.attachments:
            team_name = game_utils.find_team_name(message.author, teams)
            user_id = 165559954516738049
            await client.get_channel(notification_channel_id).send(f"**{team_name}** just uploaded a drop - Waiting for approval from <@{user_id}>")
    if message.channel.id == notification_channel_id and message.content == "!reroll":
        team_name = game_utils.find_team_name(message.author, teams)

        if teams[team_name]["rerolls"] == 0:
            await client.get_channel(notification_channel_id).send(f'Requesting team **{team_name}** does not have any rerolls left - too bad!')
        else:
            old_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
            last_roll = teams[team_name]["last_roll"]
            teams[team_name]["tile"] -= last_roll
            dice_roll = game_utils.roll_dice()
            game_utils.update_team_tiles(teams[team_name], dice_roll)
            game_utils.update_last_roll(teams[team_name], dice_roll)
            new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
            new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]
            teams[team_name]["rerolls"] -= 1
            await client.get_channel(notification_channel_id).send(f'Rerolling for team **{team_name}** from **{old_tile_name}** 🎲 ... \
                                                                \nNew roll is: **{dice_roll}** new tile is **{new_tile_name}** you have **{teams[team_name]["rerolls"]}** rerolls left! \
                                                                \n**Description:** {new_tile_desc}.')
            board.generate_board(tiles, board_data, teams)
            await client.get_channel(board_channel).send(file=discord.File('game_board.png'))


@client.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    if reaction.message.channel.id == image_channel_id and str(reaction.emoji) == '✅':
        team_name = game_utils.find_team_name(reaction.message.author, teams)
        dice_roll = game_utils.roll_dice()
        old_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
        game_utils.update_team_tiles(teams[team_name], dice_roll)
        game_utils.update_last_roll(teams[team_name], dice_roll)
        new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
        new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

        await client.get_channel(notification_channel_id).send(f'Drop for **{old_tile_name}** was approved 🎲 rolling for **{team_name}** ... \
                                                               \nRoll is: **{dice_roll}** new tile is **{new_tile_name}** good luck! \
                                                               \n**Description:** {new_tile_desc}.')
        
        board.generate_board(tiles, board_data, teams)
        await client.get_channel(board_channel).send(file=discord.File('game_board.png'))

    elif reaction.message.channel.id == image_channel_id and str(reaction.emoji) == '❌':
        team_name = game_utils.find_team_name(reaction.message.author, teams)
        await client.get_channel(notification_channel_id).send(f'Drop was declined for **{team_name}** check your image and try again!\n')


if __name__ == "__main__":
    board_data, tiles, teams = etl.load_config_file()
    secrets = etl.load_secrets()

    image_channel_id = secrets["image_channel_id"]
    notification_channel_id = secrets["notification_channel_id"]
    board_channel = secrets["board_channel"]

    client.run(secrets["discord-bot-token"])