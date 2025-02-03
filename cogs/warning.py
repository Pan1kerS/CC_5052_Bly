import disnake
from disnake.ext import commands
from config import FIRST_WARNING_ROLE_ID, SECOND_WARNING_ROLE_ID, THIRD_WARNING_ROLE_ID, LOG_CHANNEL_ID

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="warn", description="Дал шапакляк")
    @commands.has_permissions(administrator=True)
    async def warn(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member, level: str):
        role_id = {
            "1": FIRST_WARNING_ROLE_ID[0],
            "2": SECOND_WARNING_ROLE_ID[0],
            "3": THIRD_WARNING_ROLE_ID[0]
        }[level]

        role = user.guild.get_role(role_id)
        await user.add_roles(role)
        await interaction.response.send_message(f"Представитель {interaction.author.mention} выдал {level} шапакляк  {user.mention}", ephemeral=True)

        # Отправляем отчет в лог канал
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        embed = disnake.Embed(
            title="Выдан шапакляк",
            description=f"**Выдал:** {interaction.author.mention}\n**Получил:** {user.mention}\n**Уровень:** {level}",
            color=disnake.Color.orange()
        )
        await log_channel.send(embed=embed)

    @commands.slash_command(name="unwarn", description="Снять предупреждение")
    @commands.has_permissions(administrator=True)
    async def unwarn(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member, level: str):
        role_id = {
            "1": FIRST_WARNING_ROLE_ID[0],
            "2": SECOND_WARNING_ROLE_ID[0],
            "3": THIRD_WARNING_ROLE_ID[0]
        }[level]

        role = user.guild.get_role(role_id)
        await user.remove_roles(role)
        await interaction.response.send_message(f"Представитель {interaction.author.mention} забрал {level} шапакляк  {user.mention}", ephemeral=True)

        # Отправляем отчет в лог канал
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        embed = disnake.Embed(
            title="Снят шапакляк",
            description=f"**Забрал:** {interaction.author.mention}\n**У кого:** {user.mention}\n**Уровень:** {level}",
            color=disnake.Color.green()
        )
        await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Warn(bot))
