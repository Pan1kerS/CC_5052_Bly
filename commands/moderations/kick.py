import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID

async def setup_kick_command(bot: commands.Bot):
    #kick
    @bot.slash_command()
    @commands.has_permissions(kick_members=True, administrator=True)
    async def kick(inter, member: disnake.Member, *, reason="Нарушение правил"):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await member.kick(reason=reason)
        await inter.send(f"Представитель подразделения {inter.author.mention} выгнал с батальона {member.mention}",
                       delete_after=10)

        embed = disnake.Embed(
            title="Исключение из батальона",
            description=f"**Испольнитель наказания**: {inter.author.mention}\n**Нарушитель:** {member.mention}\n**Причина:** {reason}",
            color=disnake.Color.red()
        )
        await log_channel.send(embed=embed)

        await inter.message.delete(delay=5)