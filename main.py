from __future__ import annotations
"""
main.py – Discord Tile-Race Bot (slash-command edition)
------------------------------------------------------
* /reroll  – spend a reroll for your own team
* /refreshboard – admin-only force redraw
* Uploads, ✅/❌ approvals, forks, and board rendering as before
"""

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
import os
import warnings
from typing import Dict, Any

import discord
from discord import app_commands
import networkx as nx

from load_config import ETL
from utils.board import generate_board
from utils.game_functions import GameUtils

warnings.filterwarnings("ignore", category=UserWarning)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
CHECK_EMOJI = "\N{WHITE HEAVY CHECK MARK}"   # ✅
CROSS_EMOJI = "\N{CROSS MARK}"               # ❌
OWNER_IDS   = {"203664557762150401","632453762383872030","731780391031013387"}         # <-- put your Discord user-ID(s)

# --------------------------------------------------------------------------- #
# Discord objects
# --------------------------------------------------------------------------- #
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
tree   = app_commands.CommandTree(client)

# --------------------------------------------------------------------------- #
# Globals populated at runtime
# --------------------------------------------------------------------------- #
image_channel_id: int
notification_channel_id: int
board_channel_id: int
board_data: Dict[str, Any]
tiles: Dict[str, Dict[str, Any]]
teams: Dict[str, Dict[str, Any]]
GRAPH: nx.DiGraph

# --------------------------------------------------------------------------- #
# Helper
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
# Movement / dice logic
# --------------------------------------------------------------------------- #
async def advance_team(team: Dict[str, Any], dice: int) -> None:
    cur = team["tile"]
    paths = []
    for node in GRAPH.nodes:
        try:
            for p in nx.all_simple_paths(GRAPH, cur, node, cutoff=dice):
                if len(p) - 1 == dice:
                    paths.append(p)
        except nx.NetworkXNoPath:
            continue

    if not paths:
        return
    if len(paths) == 1:
        team["tile"] = paths[0][-1]
        return

    channel = client.get_channel(notification_channel_id)
    prompt  = await channel.send(
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
    team = teams[team_name]
    old  = tiles[team["tile"]]["item-name"]
    dice = GameUtils.roll_dice(3, True)
    await advance_team(team, dice)
    team["rerolls"] -= 1
    await announce_roll(team_name, old, dice, tiles[team["tile"]]["item-name"], reroll=True)
    await refresh_board()

async def process_drop_approval(team_name: str):
    team = teams[team_name]
    old  = tiles[team["tile"]]["item-name"]
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
# Slash-commands
# --------------------------------------------------------------------------- #
@tree.command(name="reroll", description="Spend a reroll for your team")
async def reroll_cmd(inter: discord.Interaction):
    tname = GameUtils.find_team_name(inter.user, teams)
    if not tname:
        await inter.response.send_message("You’re not on any team 🤔", ephemeral=True)
        return
    if teams[tname]["rerolls"] == 0:
        await inter.response.send_message(f"Team **{tname}** has no rerolls left.", ephemeral=True)
        return
    await inter.response.defer()
    await perform_reroll(tname)
    await inter.followup.send("Reroll complete ✔", ephemeral=True)

@tree.command(name="refreshboard", description="Force-redraw the board (admin)")
async def refresh_cmd(inter: discord.Interaction):
    if str(inter.user.id) not in OWNER_IDS:
        await inter.response.send_message("Only admins can run this.", ephemeral=True)
        return
    await inter.response.defer()
    await refresh_board()
    await inter.followup.send("Board refreshed ✅", ephemeral=True)

# --------------------------------------------------------------------------- #
# Discord events
# --------------------------------------------------------------------------- #
@client.event
async def on_ready():
    await tree.sync()
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

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    # ----- approval / decline -----
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
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load_config_file()
    secrets = ETL.load_secrets()

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
