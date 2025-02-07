import disnake
from disnake.ext import commands
import requests


class ReportOp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeh6ttpvjVbON_cnQVLRWPe-5SPOcp74bKgI8oh8YxMBjGOHA/formResponse"

    @commands.slash_command(name="report_op", description="Отправить рапорт об операции")
    async def report_op(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel

        data = {}
        questions = {
            'reporter': "Докладывает: (пинг себя)",
            'cmdo': "КМДО Операции: (пинг или впишите вручную)",
            'adjutant': "Адъютант: (пинг или впишите вручную)",
            'participants': "Участники: (пинг одного или нескольких участников)",
            'report': "Доклад: (впишите сообщение о докладе)",
            'results': "Итоги: (впишите итог операции)"
        }

        for key, question in questions.items():
            await interaction.followup.send(question)
            msg = await self.bot.wait_for('message', check=lambda m: m.author == interaction.author)

            # Обработка упоминаний и замена на никнеймы
            content = msg.content
            for mention in msg.mentions:
                member = interaction.guild.get_member(mention.id)
                if member:
                    display_name = member.display_name
                    content = content.replace(f'<@{mention.id}>', display_name)
                    content = content.replace(f'<@!{mention.id}>', display_name)

            # Сохранение вводных данных
            data[key] = content
            await msg.delete()

        # Отправка в Google Form
        form_data = {
            'entry.1638391424': data['reporter'],
            'entry.1818173806': data['cmdo'],
            'entry.1240289721': data['adjutant'],
            'entry.786519394': data['participants'],
            'entry.1062158297': data['report'],
            'entry.1309579927': data['results']
        }

        requests.post(self.form_url, data=form_data)

        # Отправка в Discord
        embed = disnake.Embed(
            title="Рапорт об операции",
            color=disnake.Color.blue()
        )
        embed.add_field(name="Докладывает", value=data['reporter'], inline=False)
        embed.add_field(name="КМДО Операции", value=data['cmdo'], inline=False)
        embed.add_field(name="Адъютант", value=data['adjutant'], inline=False)
        embed.add_field(name="Участники", value=data['participants'], inline=False)
        embed.add_field(name="Доклад", value=data['report'], inline=False)
        embed.add_field(name="Итоги", value=data['results'], inline=False)

        await channel.send(embed=embed)
        await interaction.followup.send("Рапорт отправлен!", ephemeral=True)


def setup(bot):
    bot.add_cog(ReportOp(bot))