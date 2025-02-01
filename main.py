import disnake
from disnake.ext import commands
from config import BOT_TOKEN, TEST_GUILDS
from events import setup_events
from commands.moderation import setup_moderation_commands

# Инициализация бота
bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=disnake.Intents.all(),
    test_guilds=TEST_GUILDS
)


async def main():
    # Регистрация событий
    await setup_events(bot)
    # Регистрация команд
    await setup_moderation_commands(bot)
    # Запуск бота
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())