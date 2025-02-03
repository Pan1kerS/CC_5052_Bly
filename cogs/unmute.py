import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID, ROLE_MUTE_ID, ALL_ROLE_IDS

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="unmute", description="Разрешение говорить")
    @commands.has_permissions(manage_messages=True, administrator=True)
    async def unmute(self,
        interaction: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Бойцу разрешено говорить"),
        reason: str = commands.Param(description="Причина разрешения", default="Истек срок наказания")
    ):
        await interaction.response.defer(ephemeral=True)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        mute_role = user.guild.get_role(ROLE_MUTE_ID)

        try:
            # Проверка наличия мута
            if mute_role not in user.roles:
                await interaction.followup.send("Этому бойцу можно говорить!", ephemeral=True)
                return

            # Возвращаем сохраненные роли и снимаем мут
            if user.id in self.bot.muted_roles:
                await user.add_roles(*self.bot.muted_roles[user.id])
                await user.remove_roles(mute_role)
                del self.bot.muted_roles[user.id]

                # Отправляем ответ
                await interaction.followup.send(
                    f"Представитель подразделения {interaction.author.mention} разрешил говорить {user.mention}",
                    ephemeral=True
                )

                # Отправляем в логи
                embed = disnake.Embed(
                    title="Разрешение говорить",
                    description=f"**Исполнитель:** {interaction.author.mention}\n**Нарушитель:** {user.mention}\n**Причина:** {reason}",
                    color=disnake.Color.green()
                )
                if log_channel:
                    await log_channel.send(embed=embed)
                else:
                    print("Лог канал не найден!")
            else:
                await interaction.followup.send(
                    "Не найдены сохраненные роли участника",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Ошибка в команде unmute: {e}")
            await interaction.followup.send(
                f"Произошла ошибка при размуте: {str(e)}",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(Unmute(bot))