import disnake
from disnake.ext import commands

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Выгнать пользователя с сервера")
    async def kick(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member, *, reason: str = "Не указана"):
        try:
            await interaction.guild.kick(user, reason=reason)
            await interaction.response.send_message(f"Представитель батальона {user.name} выгнал с казармы {user.mention}", ephemeral=True)
        except disnake.Forbidden:
            await interaction.response.send_message("У меня нет прав для кика этого пользователя!", ephemeral=True)
        except disnake.HTTPException as e:
            await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)


def setup(bot):
    bot.add_cog(Kick(bot))