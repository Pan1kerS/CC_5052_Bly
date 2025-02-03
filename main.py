import disnake
from config import BOT_TOKEN, TEST_GUILDS
from disnake.ext import commands
from events import events_bot
import os

intents=disnake.Intents.all()
bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=intents,
    test_guilds=TEST_GUILDS
)

async def main():
    await events_bot(bot)

for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(BOT_TOKEN)