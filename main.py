from __future__ import annotations

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
import os
import warnings
from typing import Dict, Any

import discord
import networkx as nx

from load_config import ETL
from utils.board import generate_board
from utils.game_functions import GameUtils

warnings.filterwarnings("ignore", category=UserWarning)

# --------------------------------------------------------------------------- #
# Emoji constants
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
# Helpers
# --------------------------------------------------------------------------- #
def is_me(msg: discord.Message) -> bool:
    return msg.author == client.user


async def refresh_board() -> None:
    chan = client.get_channel(board_channel_id)
    await chan.purge(check=is_me)
    generate_board(tiles, board_data, teams)
    await chan.send(file=discord.File("game_board.png"))
    print("[DEBUG] Board refreshed")

# --------------------------------------------------------------------------- #
# Team movement
# --------------------------------------------------------------------------- #
async def advance_team(team: Dict[str, Any], dice: int) -> None:
    """Move *team* forward exactly *dice* edges, prompting if multiple paths."""
    cur = team["tile"]
    paths: list[list[str]] = []

    # collect all simple paths of exact length `dice`
    for node in GRAPH.nodes:
        try:
            for path in nx.all_simple_paths(GRAPH, cur, node, cutoff=dice):
                if len(path) - 1 == dice:
                    paths.append(path)
        except nx.NetworkXNoPath:
            continue

    if not paths:
        print(f"[INFO] No path from {cur} with roll {dice}")
        return
    if len(paths) == 1:
        team["tile"] = paths[0][-1]
        print(f"[MOVE] {team['name']} auto → {team['tile']}")
        return

    # fork prompt
    channel = client.get_channel(notification_channel_id)
    prompt = await channel.send(
        f"**{team['name']}**, you rolled **{dice}** – choose a path:"
    )
    emoji_map, opts = {}, ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫"]
    for idx, path in enumerate(paths[: len(opts)]):
        dest, emoji = path[-1], opts[idx]
        emoji_map[emoji] = dest
        await prompt.add_reaction(emoji)
        await channel.send(f"{emoji} → {tiles[dest]['item-name']}")
    team["pending_paths"] = emoji_map
    print(f"[FORK] Waiting choice from {team['name']} ({len(paths)} options)")

# --------------------------------------------------------------------------- #
# Discord events
# --------------------------------------------------------------------------- #
@client.event
async def on_ready():
    await client.get_channel(notification_channel_id).purge(check=is_me)
    await refresh_board()
    print(f"[READY] {client.user} is online ✔")

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    # ----- image submission -----
    if message.channel.id == image_channel_id and message.attachments:
        tname = GameUtils.find_team_name(message.author, teams)
        if not tname:
            print(f"[WARN] Upload from user with no team: {message.author.id}")
            return

        await client.get_channel(notification_channel_id).send(
            f"**{tname}** uploaded a drop – waiting for approval."
        )
        for emoji in (CHECK_EMOJI, CROSS_EMOJI):
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                print(f"[WARN] add_reaction {emoji}: {e}")
        return

    # ----- !reroll -----
    if (
        message.channel.id == notification_channel_id
        and message.content.strip().lower() == "!reroll"
    ):
        tname = GameUtils.find_team_name(message.author, teams)
        if not tname:
            return
        if teams[tname]["rerolls"] == 0:
            await message.channel.send(f"Team **{tname}** has no rerolls left.")
            return
        await perform_reroll(tname)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    print(f"[REACTION] '{reaction.emoji}' by {user.display_name} in #{reaction.message.channel.name}")

    # ----- approve / decline -----
    if reaction.message.channel.id == image_channel_id:
        tname = GameUtils.find_team_name(reaction.message.author, teams)
        if not tname:
            return
        if str(reaction.emoji) == CHECK_EMOJI:
            await process_drop_approval(tname)
        elif str(reaction.emoji) == CROSS_EMOJI:
            await client.get_channel(notification_channel_id).send(
                f"Drop declined for **{tname}** – try again."
            )
        return

    # ----- fork choice -----
    tname = GameUtils.find_team_name(user, teams)
    if not tname:
        return
    pending = teams[tname].get("pending_paths")
    if pending and str(reaction.emoji) in pending:
        teams[tname]["tile"] = pending.pop(str(reaction.emoji))
        teams[tname].pop("pending_paths", None)
        await refresh_board()

# --------------------------------------------------------------------------- #
# Roll helpers
# --------------------------------------------------------------------------- #
async def perform_reroll(team_name: str):
    team = teams[team_name]
    old = tiles[team["tile"]]["item-name"]
    dice = GameUtils.roll_dice(3, True)
    await advance_team(team, dice)
    team["rerolls"] -= 1
    await announce_roll(team_name, old, dice, tiles[team["tile"]]["item-name"], reroll=True)
    await refresh_board()

async def process_drop_approval(team_name: str):
    team = teams[team_name]
    old = tiles[team["tile"]]["item-name"]
    dice = GameUtils.roll_dice(3, True)
    await advance_team(team, dice)
    await announce_roll(team_name, old, dice, tiles[team["tile"]]["item-name"], approved=True)
    await refresh_board()

async def announce_roll(team: str, old: str, dice: int, new: str, *, reroll=False, approved=False):
    verb = "reroll" if reroll else "approved" if approved else "rolled"
    await client.get_channel(notification_channel_id).send(
        f"**{team}** {verb}: **{old}** → **{new}** (🎲 {dice})"
    )

# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

    # Build directed graph
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
