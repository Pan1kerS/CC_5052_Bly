import disnake
from config import  BOT_TOKEN, TEST_GUILDS
from disnake.ext import commands
from events import events_bot
import asyncio

bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=disnake.Intents.all(),
    test_guilds=TEST_GUILDS
)

async def main():
    await events_bot(bot)
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())