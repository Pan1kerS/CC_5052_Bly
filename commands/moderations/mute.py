import disnake
from disnake.ext import commands
import asyncio
from config import LOG_CHANNEL_ID, ROLE_MUTE_ID
from collections import defaultdict

muted_roles = defaultdict(list)

async def setup_mute_command(bot: commands.Bot):
    # Mute
    @bot.slash_command()
    @commands.has_permissions(manage_messages=True, administrator=True)
    async def mute(
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(description="Боец для мута"),
        duration: str = commands.Param(
            description="Длительность мута",
            choices=["30m", "2h", "12h", "1d", "7d", "1M", "forever"]
        ),
        reason: str = commands.Param(description="Причина мута", default="Нарушение правил")
    ):
        await inter.response.defer(ephemeral=True)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        mute_role = member.guild.get_role(ROLE_MUTE_ID)

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
            # Сохраняем роли
            user_roles = [role for role in member.roles if role != member.guild.default_role]
            muted_roles[member.id] = user_roles

            # Применяем мут
            await member.remove_roles(*user_roles, reason="Мут")
            await member.add_roles(mute_role)

            # Отправляем ответ
            await inter.response.send_message(
                f"Представитель подразделения {inter.author.mention} запретил говорить {member.mention} на {duration}",
                ephemeral=True
            )

            # Отправляем в логи
            embed = disnake.Embed(
                title="Запрет говорить",
                description=f"**Исполнитель наказания**: {inter.author.mention}\n**Нарушитель:** {member.mention}\n**Длительность:** {duration}\n**Причина:** {reason}",
                color=disnake.Color.red()
            )
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print("Лог канал не найден!")

            # Автоматический размут
            if duration_seconds:
                await asyncio.sleep(duration_seconds)
                if member.id in muted_roles:
                    await member.remove_roles(mute_role)
                    await member.add_roles(*muted_roles[member.id])
                    del muted_roles[member.id]
                    if log_channel:
                        await log_channel.send(f"Участник {member.mention} был размучен автоматически (истек срок мута)")

        except Exception as e:
            print(f"Ошибка в команде mute: {e}")
            await inter.response.send_message(
                "Произошла ошибка при выполнении команды",
                ephemeral=True
            )