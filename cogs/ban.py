import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID
import asyncio

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @commands.has_permissions(ban_members=True, administrator=True)
    async def ban(self,
            interaction: disnake.ApplicationCommandInteraction,
            user: disnake.Member = commands.Param(description="Боец для изгнания"),
            duration: str = commands.Param(
                description="Длительность изгнания",
                choices=["30 минут", "2 часа", "12 часов", "1 день", "7 дней", "1 месяц", "Навсегда"]
            ),
            reason: str = commands.Param(description="Причина изгнания", default="Нарушение правил")
):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)

        duration_seconds = {
            "30 минут": 1800,
            "2 часа": 7200,
            "12 часов": 43200,
            "1 день": 86400,
            "7 дней": 604800,
            "1 месяц": 2592000,
            "Навсегда": None
        }[duration]

        try:
            await user.ban(reason=reason)
            await interaction.response.send_message(
            f"Представитель подразделения {interaction.author.mention} изгнал с батальона {user.mention} на {duration}",
            ephemeral=True
        )

            embed = disnake.Embed(
                title="Изгнание с батальона",
                description=f"**Исполнитель наказания**: {interaction.author.mention}\n**Нарушитель:** {user.mention}\n**Длительность:** {duration}\n**Причина:** {reason}",
                color=disnake.Color.red()
            )
            await log_channel.send(embed=embed)

            if duration_seconds:
                await asyncio.sleep(duration_seconds)
                await interaction.guild.unban(user, reason="Истек срок бана")
                await log_channel.send(f"Участник {user.mention} был разбанен автоматически (истек срок бана)")

        except Exception as e:
            print(f"Error in ban command: {e}")

async def setup(bot):
    await bot.add_cog(Ban(bot))
