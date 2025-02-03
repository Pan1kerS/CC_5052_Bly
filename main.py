import disnake
from config import BOT_TOKEN, TEST_GUILDS, DEFAULT_ROLES_IDS, WELCOME_CHANNEL_ID, CENSORED_WORDS
from disnake.ext import commands
import os

intents=disnake.Intents.all()
bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=intents,
    test_guilds=TEST_GUILDS
)
@bot.event
async def on_ready():
    print(f'СС 5052 Bly прибыл в расположение штаба')

@bot.event
async def on_member_join(member):
    try:
        roles = [member.guild.get_role(role_id) for role_id in DEFAULT_ROLES_IDS if member.guild.get_role(role_id)]
        await member.add_roles(*roles)

        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        embed = disnake.Embed(
            title = "Новоприбовший боец!",
            description = f"{member.name}#{member.discriminator}",
            color = 0xbda600
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

    if any(censored_word in content for censored_word in CENSORED_WORDS):
        await message.delete()
        await message.channel.send(f"{message.author.mention} Отставить мандалорскую лексику!")
        return

for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(BOT_TOKEN)
