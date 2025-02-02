import disnake
from disnake.ext import commands
from config import DEFAULT_ROLES_IDS, WELCOME_CHANNEL_ID

async def events_bot(bot: commands.Bot):
    # Оповещение, что бот запущен
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
