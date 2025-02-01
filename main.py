import disnake
from disnake.ext import commands
from config import BOT_TOKEN, TEST_GUILDS
from events import setup_events
import os

# Инициализация бота
bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=disnake.Intents.all(),
    test_guilds=TEST_GUILDS
)


async def load_cogs(bot):
    for folder in os.listdir('./commands'):
        if os.path.isdir(f'./commands/{folder}'):
            for filename in os.listdir(f'./commands/{folder}'):
                if filename.endswith('.py'):
                    cog_name = filename[:-3]
                    await bot.load_extension(f'commands.{folder}.{cog_name}')

async def main():
    # Регистрация событий
    await setup_events(bot)
    # Регистрация команд
    await load_cogs(bot)
    # Запуск бота
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())