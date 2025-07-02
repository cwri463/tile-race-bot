import os

def load_secrets():
    return {
        "DISCORD_TOKEN": os.environ.get("DISCORD_TOKEN")
    }
