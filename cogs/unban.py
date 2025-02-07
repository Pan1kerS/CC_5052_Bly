import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="unban", description="Допуск обратно в батальон")
    @commands.has_permissions(ban_members=True, administrator=True)
    async def unban(self,
        interaction: disnake.ApplicationCommandInteraction,
        member_id: str = commands.Param(description="ID участника для разбана"),
        reason: str = commands.Param(description="Причина разрешения", default="Прощение")
    ):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)

        try:
            banned_users = await interaction.guild.bans().flatten()
            member_to_unban = next((ban_entry.user for ban_entry in banned_users if str(ban_entry.user.id) == member_id), None)

            if member_to_unban is None:
                await interaction.response.send_message("Участник с таким ID не найден в списке изгнаных!", ephemeral=True)
                return

            await interaction.guild.unban(member_to_unban, reason=reason)

            await interaction.response.send_message(
                f"Представитель подразделения {interaction.author.mention} разрешил вернуться {member_to_unban.mention}",
                ephemeral=True
            )

            embed = disnake.Embed(
                title="Возвращение в батальон",
                description=f"**Исполнитель:** {interaction.author.mention}\n**Нарушитель:** {member_to_unban.mention}\n**Причина:** {reason}",
                color=disnake.Color.green()
            )
            await log_channel.send(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"Произошла ошибка при разбане: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Unban(bot))