from __future__ import annotations

"""Discord Tile‑Race Bot – branching‑path edition.

This version builds a directed graph from each tile’s ``next`` list and
supports forks with 🇦/🇧/… reaction choices.  It relies on the new
``utils/board.generate_board`` function to render the board image.
"""

# --------------------------------------------------------------------------- #
# Imports & global objects
# --------------------------------------------------------------------------- #
import os
import warnings
from typing import Dict, Any

import discord
import networkx as nx

from load_config import ETL
from utils.board import generate_board  # ← function, not class
from utils.game_functions import GameUtils

warnings.filterwarnings("ignore", category=UserWarning)

# Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

# Globals populated at runtime
image_channel_id: int
notification_channel_id: int
board_channel_id: int
board_data: Dict[str, Any]
tiles: Dict[str, Dict[str, Any]]
teams: Dict[str, Dict[str, Any]]
GRAPH: nx.DiGraph

# --------------------------------------------------------------------------- #
# Helper utils
# --------------------------------------------------------------------------- #

def is_me(msg: discord.Message) -> bool:
    return msg.author == client.user


async def refresh_board() -> None:
    """Regenerate and post the board image."""
    chan = client.get_channel(board_channel_id)
    await chan.purge(check=is_me)
    generate_board(tiles, board_data, teams)
    await chan.send(file=discord.File("game_board.png"))


# --------------------------------------------------------------------------- #
# Graph movement logic
# --------------------------------------------------------------------------- #
async def advance_team(team: Dict[str, Any], dice: int) -> None:
    cur = team["tile"]
    paths = [p for p in nx.all_simple_paths(GRAPH, cur, None, cutoff=dice) if len(p) - 1 == dice]
    if not paths:
        return
    if len(paths) == 1:
        team["tile"] = paths[0][-1]
        return

    # prompt fork choice
    channel = client.get_channel(notification_channel_id)
    prompt_msg = await channel.send(
        f"**{team['name']}**, you rolled **{dice}** – choose a path:"
    )
    emoji_map, options = {}, ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫"]
    for idx, path in enumerate(paths[: len(options)]):
        dest, emoji = path[-1], options[idx]
        emoji_map[emoji] = dest
        await prompt_msg.add_reaction(emoji)
        await channel.send(f"{emoji} → {tiles[dest]['item-name']}")
    team["pending_paths"] = emoji_map


# --------------------------------------------------------------------------- #
# Discord events
# --------------------------------------------------------------------------- #
@client.event
async def on_ready():
    await client.get_channel(notification_channel_id).purge(check=is_me)
    await refresh_board()
    print(f"{client.user} is online and ready!")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.channel.id == image_channel_id and message.attachments:
        await message.add_reaction("✅"); await message.add_reaction("❌")
        tname = GameUtils.find_team_name(message.author, teams)
        await client.get_channel(notification_channel_id).send(
            f"**{tname}** uploaded a drop – waiting for approval."
        )
        return

    if message.channel.id == notification_channel_id and message.content.strip().lower() == "!reroll":
        tname = GameUtils.find_team_name(message.author, teams)
        if teams[tname]["rerolls"] == 0:
            await message.channel.send(f"Team **{tname}** has no rerolls left.")
            return
        await perform_reroll(tname)


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    if reaction.message.channel.id == image_channel_id:
        tname = GameUtils.find_team_name(reaction.message.author, teams)
        if str(reaction.emoji) == "✅":
            await process_drop_approval(tname)
        elif str(reaction.emoji) == "❌":
            await client.get_channel(notification_channel_id).send(
                f"Drop declined for **{tname}** – try again."
            )
        return

    # fork choice handling
    tname = GameUtils.find_team_name(user, teams)
    pending = teams[tname].get("pending_paths")
    if pending and str(reaction.emoji) in pending:
        teams[tname]["tile"] = pending.pop(str(reaction.emoji))
        teams[tname].pop("pending_paths", None)
        await refresh_board()


# --------------------------------------------------------------------------- #
# Roll handlers
# --------------------------------------------------------------------------- #
async def perform_reroll(team_name: str):
    team = teams[team_name]
    old = tiles[team["tile"]]["item-name"]
    dice = GameUtils.roll_dice(3, True)
    await advance_team(team, dice)
    team["rerolls"] -= 1
    await announce_roll(team_name, old, dice, tiles[team["tile"]]["item-name"], reroll=True)


async def process_drop_approval(team_name: str):
    team = teams[team_name]
    old = tiles[team["tile"]]["item-name"]
    dice = GameUtils.roll_dice(3, True)
    await advance_team(team, dice)
    await announce_roll(team_name, old, dice, tiles[team["tile"]]["item-name"], approved=True)


async def announce_roll(team: str, old: str, dice: int, new: str, *, reroll=False, approved=False):
    verb = "reroll" if reroll else "approved" if approved else "rolled"
    await client.get_channel(notification_channel_id).send(
        f"**{team}** {verb}: {old} → **{new}** (🎲 {dice})"
    )


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

    # Directed graph
    GRAPH = nx.DiGraph()
    for tid, td in tiles.items():
        for nxt in td.get("next", []):
            GRAPH.add_edge(tid, nxt)

    image_channel_id        = int(os.getenv("IMAGE_CHANNEL_ID"))
    notification_channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
    board_channel_id        = int(os.getenv("BOARD_CHANNEL_ID"))

    for name, data in teams.items():
        data.setdefault("name", name)

    client.run(secrets["DISCORD_TOKEN"])
