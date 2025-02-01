import disnake
from disnake.ext import commands
import asyncio

bot = commands.Bot(command_prefix="/", help_command=None, intents=disnake.Intents.all(),
                   test_guilds=[1334403880590770176])

CENSORED_WORDS = ["маму ебал"]
WELCOME_CHANNEL_ID = 1334403881345744928
LOG_CHANNEL_ID = 1334528486521573446
ROLE_MUTE_ID = 1334845457217748992
muted_roles = {}


# Оповещение, что бот запущен
@bot.event
async def on_ready():
    print(f"СС 5052 Bly прибыл в штаб")


# Новприбывшие бойцы + авто-выдача ролей
@bot.event
# Авто-выдача ролей
async def on_member_join(member):
    try:
        role_ids = [
            1334403880800358463,
            1334403880800358458,
            1334403880800358456,
            1334403880745959449,
            1334403880640974899,
            1334403880640974890,
            1334403880590770182,
            1334403880590770181
        ]

        for role_id in role_ids:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)

        # Новоприбывшие бойцы
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

        embed = disnake.Embed(
            title="Новоприбывший боец!",
            description=f"{member.name}#{member.discriminator}",
            color=0xbda600
        )

        await channel.send(embed=embed)

    except Exception:
        pass


# Провека сообщений
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    content = message.content.lower()

    for censored_word in CENSORED_WORDS:
        if censored_word in content:
            await message.delete()
            await message.channel.send(f"{message.author.mention} Отставить мандалорскую лексику!")
            return


# Команды для бота
@bot.slash_command()
# Kick
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


# Ban
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
        "1dь": 86400,
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
            await member.unban(reason="Истек срок бана")
            await log_channel.send(f"Участник {member.mention} был разбанен автоматически (истек срок бана)")

    except Exception:
        pass


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
        # Получаем информацию о забаненном участнике
        banned_users = await inter.guild.bans()
        member_to_unban = None

        for ban_entry in banned_users:
            if str(ban_entry.user.id) == member_id:
                member_to_unban = ban_entry.user
                break

        if member_to_unban is None:
            await inter.response.send_message("Участник с таким ID не найден в списке забаненных!", ephemeral=True)
            return

        # Разбаниваем участника
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


# Mute (Доделать)
@bot.slash_command()
@commands.has_permissions(manage_messages=True, administrator=True)
async def mute(inter, member: disnake.Member, duration: str, *, reason="Нарушение правил"):
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

    mute_role = member.guild.get_role(ROLE_MUTE_ID)

    try:
        # Сохраняем текущие роли пользователя
        user_roles = [role for role in member.roles if role != member.guild.default_role]
        muted_roles[member.id] = user_roles

        # Снимаем все роли и выдаем мут
        await member.remove_roles(*user_roles, reason="Мут")
        await member.add_roles(mute_role)

        await inter.response.send_message(
            f"Представитель подразделения {inter.author.mention} запретил говорить {member.mention} на {duration}",
            ephemeral=True
        )

        embed = disnake.Embed(
            title="Запрет говорить",
            description=f"**Исполнитель наказания**: {inter.author.mention}\n**Нарушитель:** {member.mention}\n**Длительность:** {duration}\n**Причина:** {reason}",
            color=disnake.Color.red()
        )
        await log_channel.send(embed=embed)

        if duration_seconds:
            await asyncio.sleep(duration_seconds)
            # Возвращаем старые роли и снимаем мут
            await member.remove_roles(mute_role)
            await member.add_roles(*user_roles)
            await log_channel.send(f"Участник {member.mention} был размучен автоматически (истек срок мута)")

    except Exception:
        pass


# Unmute (Доделать надо)
@bot.slash_command(name="unmute", description="Разрешение говорить")
@commands.has_permissions(manage_messages=True, administrator=True)
async def unmute(
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(description="Бойцу разрешено говорить"),
        reason: str = commands.Param(description="Причина разрешения", default="Истек срок наказания")
):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    mute_role = member.guild.get_role(ROLE_MUTE_ID)

    try:
        if mute_role not in member.roles:
            await inter.response.send_message("Этому бойцу можно говорить!", ephemeral=True)
            return

        # Возвращаем сохраненные роли
        if member.id in muted_roles:
            await member.add_roles(*muted_roles[member.id])
            del muted_roles[member.id]

        await member.remove_roles(mute_role)

        await inter.response.send_message(
            f"Представитель подразделения {inter.author.mention} разрешил говорить {member.mention}",
            ephemeral=True
        )

        embed = disnake.Embed(
            title="Разрешение говорить",
            description=f"**Исполнитель:** {inter.author.mention}\n**Нарушитель:** {member.mention}\n**Причина:** {reason}",
            color=disnake.Color.green()
        )
        await log_channel.send(embed=embed)

    except Exception as e:
        await inter.response.send_message(
            f"Произошла ошибка при размуте: {str(e)}",
            ephemeral=True
        )


# Запуск бота
bot.run("")
