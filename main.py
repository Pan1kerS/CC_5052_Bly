import disnake
from disnake.ext import commands
from config import (
    BOT_TOKEN, TEST_GUILDS, CHANNELS, ROLES, 
    CENSORED_WORDS
)
import asyncio
import os
import traceback

intents = disnake.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, test_guilds=TEST_GUILDS)

@bot.event
async def on_ready():
    print(f'СС 5052 Bly прибыл в расположение штаба')

@bot.event
async def on_member_join(member):
    try:
        # Добавляем роли по умолчанию
        roles = [member.guild.get_role(role_id) for role_id in ROLES['DEFAULT'] if member.guild.get_role(role_id)]
        await member.add_roles(*roles)

        # Отправляем сообщение в канал приветствия
        channel = member.guild.get_channel(CHANNELS['WELCOME'])
        embed = disnake.Embed(
            title="Новоприбовший боец!",
            description=f"{member.name}#{member.discriminator}",
            color=0xbda600
        )
        await channel.send(embed=embed)

    except Exception as e:
        print(f"Error in on_member_join: {e}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    content = message.content.lower()
    if any(word in content for word in CENSORED_WORDS):
        await message.delete()
        await message.channel.send(f"{message.author.mention} Отставить мандалорскую лексику!")
        return

INITIAL_EXTENSIONS = [
    'cogs.report_op',
    'cogs.report_training',
    'cogs.report_holiday',
    'cogs.report_up_down',
    'cogs.report_attestation',
    'cogs.report_recommendation',
    'cogs.report_reprimand',
    'cogs.setup_buttons',
    'cogs.clear',
    'cogs.me',
    'cogs.tables'
]

def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Загружен ког {filename}")
            except Exception as e:
                print(f"Ошибка загрузки кога {filename}: {str(e)}")
                traceback.print_exc()
                print(f"Полная ошибка: {repr(e)}")

load()

bot.run(BOT_TOKEN)