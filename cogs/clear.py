import disnake
from disnake.ext import commands

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="clear",
        description="Очистить чат"
    )
    @commands.has_permissions(administrator=True)  # Требуются права администратора
    async def clear(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer(ephemeral=True)
        
        # Очищаем сообщения
        await interaction.channel.purge()
        
        # Отправляем подтверждение
        await interaction.edit_original_response(
            content="Чат очищен",
            delete_after=5
        )

    @clear.error
    async def clear_error(self, interaction: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message(
                "У вас недостаточно прав для использования этой команды. Требуются права администратора.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Произошла ошибка: {str(error)}",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(Clear(bot))
