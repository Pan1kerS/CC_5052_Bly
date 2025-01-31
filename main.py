import disnake
from disnake.ext import commands
import asyncio

bot = commands.Bot(command_prefix="/", help_command=None, intents=disnake.Intents.all(), test_guilds=[1334403880590770176])

CENSORED_WORDS = ["маму ебал"]
WELCOME_CHANNEL_ID = 1334403881345744928
LOG_CHANNEL_ID = 1334528486521573446


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
            choices=["30 минут", "2 часа", "12 часов", "1 день", "7 дней", "1 месяц", "навсегда"]
        ),
        reason: str = commands.Param(description="Причина изгнания", default="Нарушение правил")
):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    duration_seconds = {
        "30 минут": 1800,
        "2 часа": 7200,
        "12 часов": 43200,
        "1 день": 86400,
        "7 дней": 604800,
        "1 месяц": 2592000,
        "навсегда": None
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
            await member.unban(reason="Истек срок изгнания")
            await log_channel.send(f"Боец> {member.mention} может вернуться встрой (истек срок изгнания)")

    except Exception:
        pass

# Запуск бота
bot.run("")
