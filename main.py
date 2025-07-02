import os
import warnings

import discord
import networkx as nx 

from load_config import ETL
from utils.board import Board
from utils.game_functions import GameUtils

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
# Discord client setup
# --------------------------------------------------------------------------- #
intents = discord.Intents.default()
intents.message_content = True          # read message content
intents.reactions = True                # see who reacted
client = discord.Client(intents=intents)

# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #
def is_me(message: discord.Message) -> bool:
    """Used for purging only the bot’s own messages."""
    return message.author == client.user


# --------------------------------------------------------------------------- #
# Event handlers
# --------------------------------------------------------------------------- #
@client.event
async def on_ready():
    """Fires once the bot connects to Discord."""
    await client.get_channel(notification_channel_id).purge(check=is_me)
    await client.get_channel(board_channel_id).purge(check=is_me)

    Board.generate_board(tiles, board_data, teams)
    await client.get_channel(board_channel_id).send(
        file=discord.File("game_board.png")
    )
    print(f"{client.user} is online and ready!")


@client.event
async def on_message(message: discord.Message):
    """Handle incoming messages (image uploads, !reroll, etc.)."""
    if message.author == client.user:
        return

    #   Image-submission channel ------------------------------------------ #
    if message.channel.id == image_channel_id and message.attachments:
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        team_name = GameUtils.find_team_name(message.author, teams)
        await client.get_channel(notification_channel_id).send(
            f"**{team_name}** just uploaded a drop – waiting for approval."
        )

    #  !reroll command in notification channel -------------------------- #
    if (
        message.channel.id == notification_channel_id
        and message.content.strip().lower() == "!reroll"
    ):
        team_name = GameUtils.find_team_name(message.author, teams)
        if teams[team_name]["rerolls"] == 0:
            await client.get_channel(notification_channel_id).send(
                f"Team **{team_name}** has no rerolls left."
            )
            return

        await perform_reroll(team_name)


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Handle ✅ / ❌ reactions on image submissions."""
    if user.bot:
        return

    # Approved
    if reaction.message.channel.id == image_channel_id and str(reaction.emoji) == "✅":
        team_name = GameUtils.find_team_name(reaction.message.author, teams)
        await process_drop_approval(team_name)

    # Declined
    if reaction.message.channel.id == image_channel_id and str(reaction.emoji) == "❌":
        team_name = GameUtils.find_team_name(reaction.message.author, teams)
        await client.get_channel(notification_channel_id).send(
            f"Drop was declined for **{team_name}** – check your image and try again!"
        )


# --------------------------------------------------------------------------- #
# Game-logic helpers (unchanged from the original, just refactored)
# --------------------------------------------------------------------------- #
async def perform_reroll(team_name: str):
    old_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
    last_roll = teams[team_name]["last_roll"]
    teams[team_name]["tile"] -= last_roll

    max_dice, bonus_roll = compute_roll_window(teams[team_name]["tile"])
    dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
    GameUtils.update_team_tiles(teams[team_name], dice_roll)
    GameUtils.update_last_roll(teams[team_name], dice_roll)

    new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
    new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

    # spend reroll only if roll changed
    if last_roll != dice_roll:
        teams[team_name]["rerolls"] -= 1

    await announce_roll(
        team_name, old_tile_name, dice_roll, new_tile_name, new_tile_desc
    )
    await refresh_board()


async def process_drop_approval(team_name: str):
    old_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]

    # End tile?
    if old_tile_name == "END (ARAM)":
        await client.get_channel(notification_channel_id).send(
            f"Drop for **{old_tile_name}** approved.\n"
            f"**{team_name}** has completed the board! 🎉"
        )
        return

    max_dice, bonus_roll = compute_roll_window(teams[team_name]["tile"])
    dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
    GameUtils.update_team_tiles(teams[team_name], dice_roll)
    GameUtils.update_last_roll(teams[team_name], dice_roll)

    new_tile_name = tiles[f"tile{teams[team_name]['tile']}"]["item-name"]
    new_tile_desc = tiles[f"tile{teams[team_name]['tile']}"]["tile-desc"]

    await announce_roll(
        team_name, old_tile_name, dice_roll, new_tile_name, new_tile_desc, approved=True
    )
    await refresh_board()


def compute_roll_window(current_tile: int):
    remaining = len(tiles) - current_tile - 1
    if remaining >= 5:
        return 3, True     # may roll up to 4 with bonus roll
    if remaining >= 3:
        return 3, False
    return remaining, False


async def announce_roll(
    team_name: str,
    old_tile: str,
    dice_roll: int,
    new_tile: str,
    new_desc: str,
    approved: bool = False,
):
    verb = "approved, rolling for" if approved else "rerolling for"
    await client.get_channel(notification_channel_id).send(
        f"{verb} **{team_name}** (from **{old_tile}**)\n"
        f"Roll: **{dice_roll}** – new tile: **{new_tile}**\n"
        f"**Description:** {new_desc}\n"
        f"Rerolls left: **{teams[team_name]['rerolls']}**"
    )


async def refresh_board():
    await client.get_channel(board_channel_id).purge(check=is_me)
    Board.generate_board(tiles, board_data, teams)
    await client.get_channel(board_channel_id).send(
        file=discord.File("game_board.png")
    )


# --------------------------------------------------------------------------- #
# Main entry-point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

    # ---- graph of tile connections ----
    GRAPH = nx.DiGraph()
    for tid, t in tiles.items():
        for nxt in t.get("next", []):
            GRAPH.add_edge(tid, nxt)

    image_channel_id       = int(os.getenv("IMAGE_CHANNEL_ID"))
    notification_channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
    board_channel_id       = int(os.getenv("BOARD_CHANNEL_ID"))

    # basic sanity-check
    if not all((image_channel_id, notification_channel_id, board_channel_id)):
        raise RuntimeError(
            "IMAGE_CHANNEL_ID, NOTIFICATION_CHANNEL_ID and BOARD_CHANNEL_ID "
            "must be set as environment variables in Railway."
        )

    # Run the bot
    client.run(secrets["DISCORD_TOKEN"])
