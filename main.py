from __future__ import annotations

import os
import random
import discord
import networkx as nx

from typing import Dict, Any
from load_config import ETL
from utils.board import generate_board
from utils.game_functions import GameUtils

CHECK_EMOJI = "\N{WHITE HEAVY CHECK MARK}"   # ✅
CROSS_EMOJI = "\N{CROSS MARK}"               # ❌

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

image_channel_id: int
notification_channel_id: int
board_channel_id: int
board_data: Dict[str, Any]
tiles: Dict[str, Dict[str, Any]]
teams: Dict[str, Dict[str, Any]]
GRAPH: nx.DiGraph

# ----------------------------- Core Logic ----------------------------- #

def is_me(msg: discord.Message) -> bool:
    return msg.author == client.user

def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    for tid, tdata in tiles.items():
        for nxt in tdata.get("next", []):
            G.add_edge(tid, nxt)
    return G

async def refresh_board():
    generate_board(tiles, board_data, teams)
    print("[DEBUG] Board refreshed")

async def advance_team(team: Dict[str, Any], dice: int):
    cur = team["tile"]
    paths = list(nx.all_simple_paths(GRAPH, cur, None, cutoff=dice))
    if not paths:
        print(f"[WARN] No paths from {cur} with roll {dice}")
        return
    path = random.choice(paths)
    dest = path[-1]
    team["tile"] = dest
    print(f"[MOVE] {team['name']} auto → {dest}")
    await refresh_board()

async def perform_reroll(tname: str):
    team = teams[tname]
    if team["rerolls"] <= 0:
        print(f"[INFO] {tname} has no rerolls left")
        return

    team["rerolls"] -= 1
    dice = GameUtils.roll_dice(3, bonus_roll=False)

    old_tile_name = tiles[team["tile"]]["item-name"]
    paths = list(nx.all_simple_paths(GRAPH, team["tile"], None, cutoff=dice))
    if not paths:
        print(f"[REROLL] No valid reroll paths for {tname}")
        return
    new_tile = random.choice(paths)[-1]
    new_tile_name = tiles[new_tile]["item-name"]
    team["tile"] = new_tile

    print(f"[REROLL] {tname} ({old_tile_name}) rerolled to {new_tile_name} → {new_tile}")
    await refresh_board()

async def perform_skip(tname: str):
    team = teams[tname]
    if team.get("skips", 0) <= 0:
        print(f"[INFO] {tname} has no skips left")
        return

    team["skips"] -= 1
    dice = GameUtils.roll_dice(3, bonus_roll=False)
    cur = team["tile"]

    next_tiles = tiles[cur].get("next", [])
    if not next_tiles:
        print(f"[SKIP] No next tiles for {cur}")
        return

    skipped = random.choice(next_tiles)
    paths = list(nx.all_simple_paths(GRAPH, skipped, None, cutoff=dice))
    if not paths:
        print(f"[SKIP] No valid path from skipped {skipped}")
        return

    new_tile = random.choice(paths)[-1]
    print(f"[SKIP] {tname} skipped {cur}, moved to {new_tile}")
    team["tile"] = new_tile
    await refresh_board()

async def process_drop_approval(tname: str):
    team = teams[tname]
    dice = GameUtils.roll_dice(3, bonus_roll=True)
    await advance_team(team, dice)

# --------------------------- Event Handlers --------------------------- #

@client.event
async def on_ready():
    global image_channel_id, notification_channel_id, board_channel_id
    global board_data, tiles, teams, GRAPH

    config = ETL("config.json")
    image_channel_id        = config.get("image_channel_id")
    notification_channel_id = config.get("notification_channel_id")
    board_channel_id        = config.get("board_channel_id")
    board_data              = config.get("board_data")
    tiles                   = config.get("tiles")
    teams                   = config.get("teams")

    for tname in teams:
        teams[tname]["name"] = tname

    GRAPH = build_graph()
    await refresh_board()
    print(f"[READY] {client.user} is online ✔")

@client.event
async def on_message(msg):
    if is_me(msg): return

    content = msg.content.lower()
    tname = GameUtils.find_team_name(msg.author, teams)
    if tname is None:
        return

    if content.startswith("!reroll"):
        await perform_reroll(tname)
    elif content.startswith("!skip"):
        await perform_skip(tname)

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user: return
    if str(reaction.emoji) != CHECK_EMOJI:
        print(f"[REACTION] '{reaction.emoji}' by {user.display_name} in #{reaction.message.channel.name}")
        return

    tname = GameUtils.find_team_name(user, teams)
    if tname is None:
        return

    await process_drop_approval(tname)

# ------------------------------ Launch ------------------------------- #

token = os.environ.get("DISCORD_BOT_TOKEN")
if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN not set in environment")

client.run(token)
