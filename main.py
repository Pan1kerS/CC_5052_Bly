import disnake
from disnake.ext import commands

bot = commands.Bot(command_prefix="!", help_command=None, intents=disnake.Intents.all())

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
@bot.command()
# Kick
@commands.has_permissions(kick_members=True, administrator=True)
async def kick(ctx, member: disnake.Member, *, reason="Нарушение правил"):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    await member.kick(reason=reason)
    await ctx.send(f"Представитель подразделения {ctx.author.mention} выгнал с батальона {member.mention}",
                   delete_after=10)

    embed = disnake.Embed(
        title="Исключение из батальона",
        description=f"**Испольнитель наказания**: {ctx.author.mention}\n**Нарушитель:** {member.mention}\n**Причина:** {reason}",
        color=disnake.Color.red()
    )
    await log_channel.send(embed=embed)

    await ctx.message.delete(delay=5)


# Запуск бота
bot.run("Вставить токен")
