import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID, ROLE_MUTE_ID
from collections import defaultdict

muted_roles = defaultdict(list)
async def setup_unmute_command(bot: commands.Bot):
    # Unmute
    @bot.slash_command(name="unmute", description="Разрешение говорить")
    @commands.has_permissions(manage_messages=True, administrator=True)
    async def unmute(
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(description="Бойцу разрешено говорить"),
        reason: str = commands.Param(description="Причина разрешения", default="Истек срок наказания")
    ):
        await inter.response.defer(ephemeral=True)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        mute_role = member.guild.get_role(ROLE_MUTE_ID)

        try:
            # Проверка наличия мута
            if mute_role not in member.roles:
                await inter.response.send_message("Этому бойцу можно говорить!", ephemeral=True)
                return

            # Возвращаем сохраненные роли и снимаем мут
            if member.id in muted_roles:
                await member.add_roles(*muted_roles[member.id])
                await member.remove_roles(mute_role)
                del muted_roles[member.id]

                # Отправляем ответ
                await inter.response.send_message(
                    f"Представитель подразделения {inter.author.mention} разрешил говорить {member.mention}",
                    ephemeral=True
                )

                # Отправляем в логи
                embed = disnake.Embed(
                    title="Разрешение говорить",
                    description=f"**Исполнитель:** {inter.author.mention}\n**Нарушитель:** {member.mention}\n**Причина:** {reason}",
                    color=disnake.Color.green()
                )
                if log_channel:
                    await log_channel.send(embed=embed)
                else:
                    print("Лог канал не найден!")
            else:
                await inter.response.send_message(
                    "Не найдены сохраненные роли участника",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Ошибка в команде unmute: {e}")
            await inter.response.send_message(
                f"Произошла ошибка при размуте: {str(e)}",
                ephemeral=True
            )