from __future__ import annotations
"""
main.py – Discord Tile‑Race Bot with separate **!skip** and **!reroll** powers
----------------------------------------------------------------------
 • **!skip**   – spend one *skip* token, ignore the current tile, roll ahead
 • **!reroll** – undo the previous dice roll, then roll again from the
                 earlier tile (classic reroll)
The rest of the gameplay (uploads, ✅/❌ approvals, forks, auto board refresh)
remains unchanged.
"""

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
import os
import warnings
from typing import Dict, Any, List

import discord
import networkx as nx

from load_config import ETL
from utils.board import generate_board
from utils.game_functions import GameUtils

warnings.filterwarnings("ignore", category=UserWarning)

# --------------------------------------------------------------------------- #
# Constants & Emojis
# --------------------------------------------------------------------------- #
CHECK_EMOJI = "\N{WHITE HEAVY CHECK MARK}"   # ✅
CROSS_EMOJI = "\N{CROSS MARK}"               # ❌

# --------------------------------------------------------------------------- #
# Discord client
# --------------------------------------------------------------------------- #
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

# --------------------------------------------------------------------------- #
# Globals filled at runtime
# --------------------------------------------------------------------------- #
image_channel_id: int
notification_channel_id: int
board_channel_id: int

board_data: Dict[str, Any]
tiles: Dict[str, Dict[str, Any]]
teams: Dict[str, Dict[str, Any]]
GRAPH: nx.DiGraph

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def is_me(msg: discord.Message) -> bool:
    return msg.author == client.user


def tile_index(tile_id: str) -> int:
    """Convert 'tile17' → 17 (helper for numeric math)."""
    return int(tile_id.replace("tile", ""))


def tile_id(idx: int) -> str:
    return f"tile{idx}"


async def refresh_board() -> None:
    board_chan = client.get_channel(board_channel_id)
    await board_chan.purge(check=is_me)
    generate_board(tiles, board_data, teams)
    await board_chan.send(file=discord.File("game_board.png"))
    print("[DEBUG] Board refreshed")


# --------------------------------------------------------------------------- #
# Movement helpers
# --------------------------------------------------------------------------- #
async def advance_team(team: Dict[str, Any], dice: int) -> None:
    """Move *team* exactly *dice* edges; auto‑choose path if single."""
    cur = team["tile"]
    paths: List[List[str]] = []

    for node in GRAPH.nodes:
        try:
            for p in nx.all_simple_paths(GRAPH, cur, node, cutoff=dice):
                if len(p) - 1 == dice:
                    paths.append(p)
        except nx.NetworkXNoPath:
            continue

    if not paths:
        print(f"[INFO] No path from {cur} with roll {dice}")
        return

    if len(paths) == 1:
        team["tile"] = paths[0][-1]
        return

    channel = client.get_channel(notification_channel_id)
    prompt = await channel.send(
        f"**{team['name']}**, you rolled **{dice}** – choose a path:"
    )
    opts = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫"]
    emoji_map = {}
    for idx, p in enumerate(paths[: len(opts)]):
        dest, emoji = p[-1], opts[idx]
        emoji_map[emoji] = dest
        await prompt.add_reaction(emoji)
        await channel.send(f"{emoji} → {tiles[dest]['item-name']}")
    team["pending_paths"] = emoji_map


async def perform_reroll(team_name: str):
    """Undo previous roll and reroll from the earlier tile."""
    team = teams[team_name]
    if team["rerolls"] <= 0:
        await client.get_channel(notification_channel_id).send(
            f"Team **{team_name}** has no rerolls left."
        )
        return

    # step back to previous tile index
    cur_idx  = tile_index(team["tile"])
    back_idx = cur_idx - team.get("last_roll", 0)
    team["tile"] = tile_id(back_idx)

    dice = GameUtils.roll_dice(3, bonus_roll=True)
    await advance_team(team, dice)
    GameUtils.update_last_roll(team, dice)
    team["rerolls"] -= 1

    await refresh_board()


async def perform_skip(team_name: str):
    """Skip current tile completely, then roll from that tile."""
    team = teams[team_name]
    if team.get("skips", 0) <= 0:
        await client.get_channel(notification_channel_id).send(
            f"Team **{team_name}** has no skips left."
        )
        return

    dice = GameUtils.roll_dice(3, bonus_roll=True)
    await advance_team(team, dice)
    GameUtils.update_last_roll(team, dice)
    team["skips"] -= 1

    await refresh_board()


async def process_drop_approval(team_name: str):
    team = teams[team_name]
    dice = GameUtils.roll_dice(3, bonus_roll=True)
    await advance_team(team, dice)
    GameUtils.update_last_roll(team, dice)
    await refresh_board()


# --------------------------------------------------------------------------- #
# Discord events
# --------------------------------------------------------------------------- #
@client.event
async def on_ready():
    await client.get_channel(notification_channel_id).purge(check=is_me)
    await refresh_board()
    print(f"[READY] {client.user} online ✔")


@client.event
async def on_message(message: discord.Message):
    if is_me(message):
        return

    content = message.content.strip().lower()
    tname = GameUtils.find_team_name(message.author, teams)

    # ---------- uploads ---------- #
    if message.channel.id == image_channel_id and message.attachments:
        if tname:
            await client.get_channel(notification_channel_id).send(
                f"**{tname}** uploaded a drop – waiting for approval."
            )
        for e in (CHECK_EMOJI, CROSS_EMOJI):
            try:
                await message.add_reaction(e)
            except Exception:
                pass
        return

    # ---------- !skip ---------- #
    if content == "!skip" and message.channel.id == notification_channel_id:
        if tname:
            await perform_skip(tname)
        return

    # ---------- !reroll ---------- #
    if content == "!reroll" and message.channel.id == notification_channel_id:
        if tname:
            await perform_reroll(tname)
        return


@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    # approval/decline channel
    if reaction.message.channel.id == image_channel_id:
        tname = GameUtils.find_team_name(reaction.message.author, teams)
        if not tname:
            return
        if str(reaction.emoji) == CHECK_EMOJI:
            await process_drop_approval(tname)
        return

    # fork choice
    tname = GameUtils.find_team_name(user, teams)
    if not tname:
        return
    pending = teams[tname].get("pending_paths")
    if pending and str(reaction.emoji) in pending:
        teams[tname]["tile"] = pending.pop(str(reaction.emoji))
        teams[tname].pop("pending_paths", None)
        await refresh_board()


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

    GRAPH = nx.DiGraph()
    for tid, td in tiles.items():
        for nxt in td.get("next", []):
            GRAPH.add_edge(tid, nxt)

    image_channel_id        = int(os.environ["IMAGE_CHANNEL_ID"])
    notification_channel_id = int(os.environ["NOTIFICATION_CHANNEL_ID"])
    board_channel_id        = int(os.environ["BOARD_CHANNEL_ID"])

    for name, data in teams.items():
        data.setdefault("name", name)
        data.setdefault("skips", 0)
        data.setdefault("last_roll", 0)

    client.run(secrets["DISCORD_TOKEN"])
