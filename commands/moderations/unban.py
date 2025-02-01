import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID

async def setup_unban_command(bot: commands.Bot):
    # Unban
    @bot.slash_command(name="unban", description="Допуск обратно в батальон")
    @commands.has_permissions(ban_members=True, administrator=True)
    async def unban(
        inter: disnake.ApplicationCommandInteraction,
        member_id: str = commands.Param(description="ID участника для разбана"),
        reason: str = commands.Param(description="Причина разбана", default="Прощение")
    ):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        try:
            banned_users = await inter.guild.bans()
            member_to_unban = next((ban_entry.user for ban_entry in banned_users if str(ban_entry.user.id) == member_id), None)

            if member_to_unban is None:
                await inter.response.send_message("Участник с таким ID не найден в списке забаненных!", ephemeral=True)
                return

            await inter.guild.unban(member_to_unban, reason=reason)

            await inter.response.send_message(
                f"Представитель подразделения {inter.author.mention} разрешил вернуться {member_to_unban.mention}",
                ephemeral=True
            )

            embed = disnake.Embed(
                title="Возвращение в батальон",
                description=f"**Исполнитель:** {inter.author.mention}\n**Нарушитель:** {member_to_unban.mention}\n**Причина:** {reason}",
                color=disnake.Color.green()
            )
            await log_channel.send(embed=embed)

        except Exception as e:
            await inter.response.send_message(
                f"Произошла ошибка при разбане: {str(e)}",
                ephemeral=True
            )