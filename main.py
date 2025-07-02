from __future__ import annotations

"""Discord Tile‑Race Bot – branching‑path edition.

This file replaces the old linear `main.py`.  Key upgrades:
• uses a directed graph (networkx) for forks / shortcuts
• prompts teams with 🇦/🇧… reactions when multiple paths are available
• relies on the new utils/board.py renderer (coords + next list)

Environment variables expected (set in Railway → Variables):
    DISCORD_TOKEN
    IMAGE_CHANNEL_ID
    NOTIFICATION_CHANNEL_ID
    BOARD_CHANNEL_ID

External deps:  discord.py  +  networkx  +  Pillow (already in requirements).
"""

# --------------------------------------------------------------------------- #
# Imports & global objects
# --------------------------------------------------------------------------- #
import os
import warnings
import asyncio
from typing import Dict, Any, List

import discord
import networkx as nx

from load_config import ETL
from utils.board import Board
from utils.game_functions import GameUtils

warnings.filterwarnings("ignore", category=UserWarning)

# Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

# Will be populated in __main__
image_channel_id: int
notification_channel_id: int
board_channel_id: int
board_data: Dict[str, Any]
tiles: Dict[str, Dict[str, Any]]
teams: Dict[str, Dict[str, Any]]
GRAPH: nx.DiGraph

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def is_me(msg: discord.Message) -> bool:
    """Used for `.purge()` – only delete the bot’s own messages."""
    return msg.author == client.user


async def refresh_board() -> None:
    """Regenerate and post the board image, wiping the old one first."""
    chan = client.get_channel(board_channel_id)
    await chan.purge(check=is_me)
    Board.generate_board(tiles, board_data, teams)
    await chan.send(file=discord.File("game_board.png"))


# --------------------------------------------------------------------------- #
# Graph‑aware movement
# --------------------------------------------------------------------------- #
async def advance_team(team: Dict[str, Any], dice: int) -> None:
    """Move *team* along exactly *dice* edges in *GRAPH*.

    If multiple valid paths exist, store a mapping in `team['pending_paths']`
    and prompt the team to react.  The move is finalised in `on_reaction_add`.
    """
    cur = team["tile"]
    # list all simple paths of length == dice
    paths = [
        p for p in nx.all_simple_paths(GRAPH, cur, None, cutoff=dice)
        if len(p) - 1 == dice
    ]
    if not paths:
        return                        # dead‑end

    if len(paths) == 1:               # deterministic
        team["tile"] = paths[0][-1]
        return

    # --- prompt for fork choice ----------------------------------------- #
    channel = client.get_channel(notification_channel_id)
    prompt_msg = await channel.send(
        f"**{team['name']}**, you rolled **{dice}** – choose a path:"
    )

    emoji_map: Dict[str, str] = {}
    options = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫"]
    for idx, path in enumerate(paths[: len(options)]):
        dest = path[-1]
        emoji = options[idx]
        emoji_map[emoji] = dest
        await prompt_msg.add_reaction(emoji)
        await channel.send(f"{emoji} → {tiles[dest]['item-name']}")

    team["pending_paths"] = emoji_map
    team["pending_msg"] = prompt_msg.id


# --------------------------------------------------------------------------- #
# Event handlers
# --------------------------------------------------------------------------- #
@client.event
async def on_ready():
    """Called once when Discord gateway is ready."""
    # Clean old messages from bot‑managed channels
    await client.get_channel(notification_channel_id).purge(check=is_me)
    await refresh_board()
    print(f"{client.user} is online and ready!")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    # ----------------------- image submissions --------------------------- #
    if message.channel.id == image_channel_id and message.attachments:
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        team_name = GameUtils.find_team_name(message.author, teams)
        await client.get_channel(notification_channel_id).send(
            f"**{team_name}** uploaded a drop – waiting for approval."
        )

    # --------------------------- !reroll --------------------------------- #
    if (
        message.channel.id == notification_channel_id
        and message.content.strip().lower() == "!reroll"
    ):
        team_name = GameUtils.find_team_name(message.author, teams)
        if teams[team_name]["rerolls"] == 0:
            await message.channel.send(
                f"Team **{team_name}** has no rerolls left."
            )
            return
        await perform_reroll(team_name)


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    # ---------- approve / decline image submissions --------------------- #
    if reaction.message.channel.id == image_channel_id:
        team_name = GameUtils.find_team_name(reaction.message.author, teams)
        if str(reaction.emoji) == "✅":
            await process_drop_approval(team_name)
        elif str(reaction.emoji) == "❌":
            await client.get_channel(notification_channel_id).send(
                f"Drop was declined for **{team_name}** – please try again."
            )
        return

    # ---------- fork choice reactions ----------------------------------- #
    team_name = GameUtils.find_team_name(user, teams)
    pending = teams[team_name].get("pending_paths")
    if pending and str(reaction.emoji) in pending:
        teams[team_name]["tile"] = pending.pop(str(reaction.emoji))
        teams[team_name].pop("pending_paths", None)
        await refresh_board()


# --------------------------------------------------------------------------- #
# Game logic wrappers for rerolls & approvals
# --------------------------------------------------------------------------- #
async def perform_reroll(team_name: str) -> None:
    team = teams[team_name]
    old_tile_name = tiles[team["tile"]]["item-name"]

    max_dice, bonus_roll = compute_roll_window(team["tile"], len(tiles))
    dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
    await advance_team(team, dice_roll)
    team["last_roll"] = dice_roll
    team["rerolls"] -= 1

    new_tile_name = tiles[team["tile"]]["item-name"]
    await announce_roll(team_name, old_tile_name, dice_roll, new_tile_name)
    await refresh_board()


async def process_drop_approval(team_name: str) -> None:
    team = teams[team_name]
    old_tile_name = tiles[team["tile"]]["item-name"]

    if old_tile_name.lower().startswith("end"):
        await client.get_channel(notification_channel_id).send(
            f"Drop for **{old_tile_name}** approved – **{team_name}** finished the board! 🎉"
        )
        return

    max_dice, bonus_roll = compute_roll_window(team["tile"], len(tiles))
    dice_roll = GameUtils.roll_dice(max_dice, bonus_roll)
    await advance_team(team, dice_roll)
    team["last_roll"] = dice_roll

    new_tile_name = tiles[team["tile"]]["item-name"]
    await announce_roll(team_name, old_tile_name, dice_roll, new_tile_name, approved=True)
    await refresh_board()


# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #

def compute_roll_window(current_idx: int, total_tiles: int):
    remaining = total_tiles - int(current_idx.split("tile")[-1]) - 1
    if remaining >= 5:
        return 3, True   # up to 4 with bonus
    if remaining >= 3:
        return 3, False
    return remaining, False


async def announce_roll(team_name: str, old_tile: str, dice_roll: int, new_tile: str, approved: bool = False):
    verb = "approved" if approved else "reroll"
    await client.get_channel(notification_channel_id).send(
        f"**{team_name}** {verb}: from **{old_tile}** rolled **{dice_roll}** → **{new_tile}**"
    )


# --------------------------------------------------------------------------- #
# Entry‑point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

    # Build directed graph from tiles[next]
    GRAPH = nx.DiGraph()
    for tid, td in tiles.items():
        for nxt in td.get("next", []):
            GRAPH.add_edge(tid, nxt)

    # Channels
    image_channel_id        = int(os.getenv("IMAGE_CHANNEL_ID"))
    notification_channel_id = int(os.getenv("NOTIFICATION_CHANNEL_ID"))
    board_channel_id        = int(os.getenv("BOARD_CHANNEL_ID"))

    if not all((image_channel_id, notification_channel_id, board_channel_id)):
        raise RuntimeError("IMAGE_/NOTIFICATION_/BOARD_CHANNEL_ID env vars must be set")

    # Make sure every team dict has a human‑readable name field
    for name, data in teams.items():
        data.setdefault("name", name)

    client.run(secrets["DISCORD_TOKEN"])
