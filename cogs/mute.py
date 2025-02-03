import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID, ROLE_MUTE_ID, ALL_ROLE_IDS
import asyncio

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.muted_roles = {}

# Mute
    @commands.slash_command(description="Заткнул бойца!")
    @commands.has_permissions(manage_messages=True, administrator=True)
    async def mute(self,
        interaction: disnake.ApplicationCommandInteraction,
        user: disnake.Member = commands.Param(description="Заткнул бойца"),
        duration: str = commands.Param(
            description="Длительность наказания",
            choices=["5 минут", "30 минут", "1 час", "2 часа", "12 часов", "1 день"]
        ),
        reason: str = commands.Param(description="Причина наказания", default="Нарушение правил")
    ):
        await interaction.response.defer(ephemeral=True)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        mute_role = user.guild.get_role(ROLE_MUTE_ID)

        duration_seconds = {
            "5 минут": 300,
            "30 минут": 1800,
            "1 час": 3600,
            "2 часа": 7200,
            "12 часов": 43200,
            "1 день": 86400
        }[duration]

        # Сохраняем текущие роли участника
        self.bot.muted_roles[user.id] = [role for role in user.roles if role.id in ALL_ROLE_IDS]

        # Снимаем все роли и выдаем роль mute
        await user.remove_roles(*self.bot.muted_roles[user.id], reason=reason)
        await user.add_roles(mute_role, reason=reason)

        await interaction.followup.send(f"Представитель подразделения {interaction.author.mention} заткнул {user.mention} на {duration}")

        embed = disnake.Embed(
            title="Мут",
            description=f"**Испольнитель наказания**: {interaction.author.mention}\n**Нарушитель:** {user.mention}\n**Причина:** {reason}\n**Длительность:** {duration}",
            color=disnake.Color.red()
        )
        await log_channel.send(embed=embed)

        # Ожидаем окончания наказания
        await asyncio.sleep(duration_seconds)

        # Возвращаем все роли и снимаем роль mute
        if user.id in self.bot.muted_roles:
            await user.remove_roles(mute_role, reason="Окончание наказания")
            await user.add_roles(*self.bot.muted_roles[user.id], reason="Окончание наказания")
            del self.bot.muted_roles[user.id]

            await log_channel.send(f"Бойцу {user.mention} разрешенно говорить, наказание оконченно")

def setup(bot):
    bot.add_cog(Mute(bot))