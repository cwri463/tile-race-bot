# ========================== main.py (PART 1/3) ==========================
"""Discord Tile‑Race Bot – core boot‑strap & helpers.
Copy this block into **main.py** first, then add PART 2 and PART 3 below it.
"""
from __future__ import annotations

import os, asyncio, random, warnings
from typing import Dict, Any, List

import discord
import networkx as nx
from discord.ext import commands
import discord.app_commands as appcmd

from load_config import ETL
from utils.board import generate_board
from utils.game_functions import GameUtils
from utils.grid_preview import render_empty_grid

warnings.filterwarnings("ignore", category=UserWarning)

# ----- Emoji constants -----
CHECK_EMOJI = "\N{WHITE HEAVY CHECK MARK}"   # ✅
CROSS_EMOJI = "\N{CROSS MARK}"               # ❌
FORK_EMOJIS = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫"]

# ----- Discord client -----
intents = discord.Intents.default()
intents.message_content = True
intents.reactions       = True
bot = commands.Bot(command_prefix="!", intents=intents)
TREE = bot.tree  # slash‑command interface

# ----- Globals (populated in on_ready) -----
image_channel_id:       int
notification_channel_id:int
board_channel_id:       int
board_data: Dict[str, Any]
tiles:      Dict[str, Dict[str, Any]]
teams:      Dict[str, Dict[str, Any]]
GRAPH:      nx.DiGraph
# ---------------------------------------------------------------------------


def is_me(msg: discord.Message) -> bool:
    return msg.author == bot.user


def tile_index(tid: str) -> int:
    return int(tid.replace("tile", ""))


def tile_id(idx: int) -> str:
    return f"tile{idx}"


def announce(team: str, verb: str, old_tile: str, dice: int, new_tile: str):
    """Send a status line in the notification channel."""
    chan = bot.get_channel(notification_channel_id)
    msg = (
        f"**{team}** {verb}: **{old_tile}** → **{new_tile}** "
        f"(🎲 {dice}) • rerolls **{teams[team]['rerolls']}** • "
        f"skips **{teams[team]['skips']}**"
    )
    asyncio.create_task(chan.send(msg))


async def refresh_board():
    chan = bot.get_channel(board_channel_id)
    await chan.purge(check=is_me)
    generate_board(tiles, board_data, teams)
    await chan.send(file=discord.File("game_board.png"))
    print("[DEBUG] Board refreshed")

# ======================= END PART 1/3 =======================

# ========================== main.py (PART 2/3) ==========================
"""Movement logic, skip/reroll, fork chooser, approvals."""

async def choose_path(team: Dict[str, Any], paths: List[List[str]]):
    """Prompt a team to pick a fork; deduplicate by destination."""
    # first path for each unique destination
    uniq: Dict[str, List[str]] = {}
    for p in paths:
        uniq.setdefault(p[-1], p)

    channel = bot.get_channel(notification_channel_id)
    prompt  = await channel.send(f"**{team['name']}**, choose your path:")

    emoji_map = {}
    for idx, (dest, _path) in enumerate(uniq.items()):
        if idx >= len(FORK_EMOJIS):
            break
        emoji = FORK_EMOJIS[idx]
        emoji_map[emoji] = dest
        await prompt.add_reaction(emoji)
        await channel.send(f"{emoji} → {tiles[dest]['item-name']}")

    team["pending_paths"] = emoji_map


async def advance_team(team: Dict[str, Any], dice: int):
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
        print(f"[MOVE] No path from {cur} with roll {dice}")
        return
    if len(paths) == 1:
        team["tile"] = paths[0][-1]
        return
    await choose_path(team, paths)


async def perform_reroll(tname: str):
    t = teams[tname]
    if t["rerolls"] <= 0:
        await bot.get_channel(notification_channel_id).send(
            f"Team **{tname}** has no rerolls left.")
        return
    back_idx = tile_index(t["tile"]) - t.get("last_roll", 0)
    t["tile"] = tile_id(back_idx)

    dice = GameUtils.roll_dice(3, True)
    old_name = tiles[tile_id(back_idx)]["item-name"]
    await advance_team(t, dice)
    GameUtils.update_last_roll(t, dice)
    t["rerolls"] -= 1
    announce(tname, "rerolled", old_name, dice, tiles[t["tile"]]["item-name"])
    await refresh_board()


async def perform_skip(tname: str):
    t = teams[tname]
    if t.get("skips", 0) <= 0:
        await bot.get_channel(notification_channel_id).send(
            f"Team **{tname}** has no skips left.")
        return
    dice = GameUtils.roll_dice(3, True)
    old_name = tiles[t["tile"]]["item-name"]
    await advance_team(t, dice)
    GameUtils.update_last_roll(t, dice)
    t["skips"] -= 1
    announce(tname, "skipped", old_name, dice, tiles[t["tile"]]["item-name"])
    await refresh_board()


async def process_drop_approval(tname: str):
    t = teams[tname]
    dice = GameUtils.roll_dice(3, True)
    old_name = tiles[t["tile"]]["item-name"]
    await advance_team(t, dice)
    GameUtils.update_last_roll(t, dice)
    announce(tname, "approved", old_name, dice, tiles[t["tile"]]["item-name"])
    await refresh_board()

# ======================= END PART 2/3 =======================

# ========================== main.py (PART 3/3) ==========================
"""Discord event-handlers, slash commands (/grid, /reroll, /skip) and the
entry-point."""

# ── optional one-guild fast-sync ─────────────────────────────────────────
# Add DISCORD_GUILD_ID to Railway (server-ID as integer). If unset, commands
# register globally (may take up to 1 h to appear).
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0") or 0)
GUILD    = discord.Object(id=GUILD_ID) if GUILD_ID else None
# ------------------------------------------------------------------------

# ---- Slash command: /grid ----------------------------------------------
@TREE.command(name="grid",
              description="Generate an empty planning grid",
              guild=GUILD)
async def grid_slash(inter: discord.Interaction):
    await inter.response.defer()
    path = render_empty_grid(board_data, tiles)
    await inter.followup.send(file=discord.File(path))

# ---- Slash command: /reroll --------------------------------------------
@TREE.command(name="reroll",
              description="Use one reroll to roll again from your previous spot",
              guild=GUILD)
async def reroll_slash(inter: discord.Interaction):
    tname = GameUtils.find_team_name(inter.user, teams)
    if not tname:
        await inter.response.send_message(
            "You aren't on any team. Ask an admin to add you first.",
            ephemeral=True,
        )
        return
    await inter.response.defer()
    await perform_reroll(tname)

# ---- Slash command: /skip ----------------------------------------------
@TREE.command(name="skip",
              description="Spend one skip token to roll ahead without completing the tile",
              guild=GUILD)
async def skip_slash(inter: discord.Interaction):
    tname = GameUtils.find_team_name(inter.user, teams)
    if not tname:
        await inter.response.send_message(
            "You aren't on any team. Ask an admin to add you first.",
            ephemeral=True,
        )
        return
    await inter.response.defer()
    await perform_skip(tname)
    
# ---- Slash command: /syncsheet ----------------------------------------
@TREE.command(
    name="syncsheet",
    description="Admin: reload board from Google Sheet CSVs",
    guild=GUILD,
)
@appcmd.default_permissions(manage_guild=True)   # requires Manage Guild
async def syncsheet_slash(inter: discord.Interaction):
    await inter.response.defer(thinking=True)

    try:
        from tools.sheet_loader import load_from_sheet
        global board_data, tiles, teams, GRAPH   # overwrite in-memory state

        board_data, tiles, teams = load_from_sheet()

        # rebuild graph
        GRAPH.clear()
        for tid, td in tiles.items():
            for nxt in td.get("next", []):
                GRAPH.add_edge(tid, nxt)

        # refresh board PNG
        await refresh_board()

        await inter.followup.send(
            f"Sheet imported – **{len(tiles)} tiles**, **{len(teams)} teams**"
        )
    except Exception as e:
        await inter.followup.send(f"❌ Import failed: `{e}`", ephemeral=True)
        raise  # still log full traceback
        
# ── Events ───────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    # ── remove lingering GLOBAL commands so you don’t see duplicates ──
    if GUILD:                      # we are using per-guild commands
        TREE.clear_commands(guild=None)   # wipe globals once

    # (re)-register commands for the chosen scope
    synced = await TREE.sync(guild=GUILD) if GUILD else await TREE.sync()
    print("[SLASH] synced:", [c.name for c in synced])

    # normal startup housekeeping
    await bot.get_channel(notification_channel_id).purge(check=is_me)
    await refresh_board()
    print(f"[READY] {bot.user} online ✔")
@bot.event
async def on_message(msg: discord.Message):
    if is_me(msg):
        return

    tname   = GameUtils.find_team_name(msg.author, teams)
    content = msg.content.strip().lower()

    # image upload channel
    if msg.channel.id == image_channel_id and msg.attachments:
        if tname:
            await bot.get_channel(notification_channel_id).send(
                f"**{tname}** uploaded a drop – waiting for approval.")
        for e in (CHECK_EMOJI, CROSS_EMOJI):
            try:
                await msg.add_reaction(e)
            except Exception:
                pass
        return

    # legacy text commands (keep or delete)
    if content == "!skip" and msg.channel.id == notification_channel_id and tname:
        await perform_skip(tname)
        return
    if content == "!reroll" and msg.channel.id == notification_channel_id and tname:
        await perform_reroll(tname)
        return

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return

    # ✅ / ❌ approval on image
    if reaction.message.channel.id == image_channel_id:
        tname = GameUtils.find_team_name(user, teams)
        if not tname:
            return
        if str(reaction.emoji) == CHECK_EMOJI:
            await process_drop_approval(tname)
        elif str(reaction.emoji) == CROSS_EMOJI:
            await bot.get_channel(notification_channel_id).send(
                f"**{tname}** drop was declined.")
        return

    # fork-choice reactions
    for t in teams.values():
        pending = t.get("pending_paths")
        if pending and str(reaction.emoji) in pending and str(user.id) in t["members"]:
            t["tile"] = pending.pop(str(reaction.emoji))
            t.pop("pending_paths", None)
            await refresh_board()
            return

# ── Entry-point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    board_data, tiles, teams = ETL.load()

    image_channel_id        = int(os.environ["IMAGE_CHANNEL_ID"])
    notification_channel_id = int(os.environ["NOTIFICATION_CHANNEL_ID"])
    board_channel_id        = int(os.environ["BOARD_CHANNEL_ID"])

    # ensure counters present
    for d in teams.values():
        d.setdefault("rerolls", 0)
        d.setdefault("skips",   0)
        d.setdefault("last_roll", 0)

    # build graph once
    GRAPH = nx.DiGraph()
    for tid, td in tiles.items():
        for nxt in td.get("next", []):
            GRAPH.add_edge(tid, nxt)

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set")
    bot.run(token)

# ======================== END main.py ===================================
