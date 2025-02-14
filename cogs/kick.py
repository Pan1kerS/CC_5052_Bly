import disnake
from disnake.ext import commands
from typing import Optional

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(    
    name="kick",
    description="Был выгнан с казармы данный боец"
    )
    @commands.has_permissions(kick_members=True)
    async def kick(
        self, 
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        reason: Optional[str] = "Причина не указана"
    ):
        if member.top_role >= inter.author.top_role:
            await inter.response.send_message("Вы не можете кикнуть участника с равной или более высокой ролью.")
            return
        
        try:
            await member.kick(reason=reason)
            
            embed = disnake.Embed(
                title="Выгнали с казармы",
                color=disnake.Color.red()
            )
            embed.add_field(name="Выгнали с казармы", value=f"{member.mention} ({member.id})", inline=False)
            embed.add_field(name="Представитель", value=f"{inter.author.mention} ({inter.author.id})", inline=False)
            embed.add_field(name="Причина", value=reason, inline=False)
            
            await inter.response.send_message(embed=embed)
            
            logs_channel = disnake.utils.get(inter.guild.channels, name="logs")
            if logs_channel:
                await logs_channel.send(embed=embed)
                
        except disnake.Forbidden:
            await inter.response.send_message("У меня недостаточно прав для кика этого участника.")
        except Exception as e:
            await inter.response.send_message(f"Произошла ошибка: {str(e)}")

def setup(bot):
    bot.add_cog(Kick(bot))
