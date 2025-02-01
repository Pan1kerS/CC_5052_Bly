import disnake
from disnake.ext import commands
from config import WELCOME_CHANNEL_ID, DEFAULT_ROLES_IDS, CENSORED_WORDS

async def setup_events(bot: commands.Bot):
    # Оповещение, что бот запущен
    @bot.event
    async def on_ready():
        print(f"СС 5052 Bly прибыл в штаб")

    # Новприбывшие бойцы + авто-выдача ролей
    @bot.event
    async def on_member_join(member):
        try:
            roles = [member.guild.get_role(role_id) for role_id in DEFAULT_ROLES_IDS if member.guild.get_role(role_id)]
            await member.add_roles(*roles)

            channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

            embed = disnake.Embed(
                title="Новоприбывший боец!",
                description=f"{member.name}#{member.discriminator}",
                color=0xbda600
            )

            await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in on_member_join: {e}")

    # Провека сообщений
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