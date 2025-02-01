import disnake
from disnake.ext import commands
import asyncio
from config import LOG_CHANNEL_ID

async def setup_ban_command(bot: commands.Bot):
    @bot.slash_command()
    @commands.has_permissions(ban_members=True, administrator=True)
    async def ban(
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(description="Боец для изгнания"),
        duration: str = commands.Param(
            description="Длительность изгнания",
            choices=["30m", "2h", "12h", "1d", "7d", "1M", "forever"]
        ),
        reason: str = commands.Param(description="Причина изгнания", default="Нарушение правил")
    ):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        duration_seconds = {
            "30m": 1800,
            "2h": 7200,
            "12h": 43200,
            "1d": 86400,
            "7d": 604800,
            "1M": 2592000,
            "forever": None
        }[duration]

        try:
            await member.ban(reason=reason)
            await inter.response.send_message(
                f"Представитель подразделения {inter.author.mention} изгнал с батальона {member.mention} на {duration}",
                ephemeral=True
            )

            embed = disnake.Embed(
                title="Изгнание с батальона",
                description=f"**Исполнитель наказания**: {inter.author.mention}\n**Нарушитель:** {member.mention}\n**Длительность:** {duration}\n**Причина:** {reason}",
                color=disnake.Color.red()
            )
            await log_channel.send(embed=embed)

            if duration_seconds:
                await asyncio.sleep(duration_seconds)
                await inter.guild.unban(member, reason="Истек срок бана")
                await log_channel.send(f"Участник {member.mention} был разбанен автоматически (истек срок бана)")

        except Exception as e:
            print(f"Error in ban command: {e}")