import disnake
from disnake.ext import commands
from config import LOG_CHANNEL_ID

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Выгнать пользователя с сервера")
    async def kick(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member, *, reason: str = "Не указана"):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        try:
            await interaction.guild.kick(user, reason=reason)
            await interaction.response.send_message(f"Представитель батальона {interaction.author.mention} выгнал с казармы {user.mention}", ephemeral=True)
        except disnake.Forbidden:
            await interaction.response.send_message("У меня нет прав для кика этого пользователя!", ephemeral=True)
        except disnake.HTTPException as e:
            await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
        embed = disnake.Embed(
            title="Выгнал с казармы",
            description=f"**Испольнитель наказания**: {interaction.author.mention}\n**Нарушитель:** {user.mention}\n**Причина:** {reason}",
            color=disnake.Color.red()
        )
        await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Kick(bot))