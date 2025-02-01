import disnake
from disnake.ext import commands
import asyncio
from config import LOG_CHANNEL_ID, ROLE_MUTE_ID
from collections import defaultdict

muted_roles = defaultdict(list)

async def setup_moderation_commands(bot: commands.Bot):
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

    # ban
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