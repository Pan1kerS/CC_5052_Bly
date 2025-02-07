import disnake
from disnake.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
import asyncio

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials/cc-5052-bly-e24abd47118d.json'
SPREADSHEET_ID = '10bUeIRVHd-0IgOyiSWp4UWoi1_RPP2LwoJCiL7e_t2I'
SHEET_NAME = 'Рапорт операции'
ROSTER_SHEET_NAME = 'Battalion Roster'


class ReportOp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)

    @commands.slash_command(name="report_op", description="Отправить рапорт об операции")
    async def report_op(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel

        data = {}
        questions = {
            'reporter': "Кто докладывает?",
            'cmdo': "Кто КМДО?",
            'adjutant': "Кто Адъютант?",
            'cmdg': "Кто КМДГ?",
            'participants': "Кто участвовал?",
            'report': "Суть доклада?",
            'results': "Итоги операции?"
        }

        for key, question in questions.items():
            question_msg = await interaction.followup.send(question)
            msg = await self.bot.wait_for('message', check=lambda m: m.author == interaction.author)

            # Обработка упоминаний и замена на никнеймы
            content = msg.content
            for mention in msg.mentions:
                member = interaction.guild.get_member(mention.id)
                if member:
                    display_name = member.display_name
                    content = content.replace(f'<@{mention.id}>', display_name)
                    content = content.replace(f'<@!{mention.id}>', display_name)

            data[key] = content
            await msg.delete()
            await question_msg.delete()

        # Запись данных в Google Sheets
        sheet = self.service.spreadsheets()
        values = [
            [data['reporter'], data['cmdo'], data['adjutant'], data['cmdg'], data['participants'], data['report'],
             data['results']]
        ]
        body = {
            'values': values
        }
        try:
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
        except googleapiclient.errors.HttpError as e:
            await interaction.followup.send(f"Ошибка при записи данных в Google Sheets: {e}", ephemeral=True)
            return

        # Обновление таблицы "Battalion Roster"
        try:
            roster_data = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                             range=f"{ROSTER_SHEET_NAME}!A:O").execute().get('values', [])
            roster_dict = {row[0]: row for row in roster_data if row}

            def update_roster(column, name):
                for key, row in roster_dict.items():
                    if name in key:
                        row[column] = str(int(row[column]) + 1)
                        break

            update_roster(3, data['reporter'])  # Колонка "Д"
            update_roster(2, data['cmdo'])  # Колонка "К"
            update_roster(2, data['adjutant'])  # Колонка "К"
            update_roster(2, data['cmdg'])  # Колонка "К"
            for participant in data['participants'].split(','):
                update_roster(14, participant.strip())  # Колонка "О"

            roster_values = list(roster_dict.values())
            roster_body = {
                'values': roster_values
            }
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{ROSTER_SHEET_NAME}!A1",
                valueInputOption="RAW",
                body=roster_body
            ).execute()
        except googleapiclient.errors.HttpError as e:
            await interaction.followup.send(f"Ошибка при обновлении таблицы 'Battalion Roster': {e}", ephemeral=True)
            return

        # Отправка в Discord
        embed = disnake.Embed(
            title="Рапорт об операции",
            color=disnake.Color.blue()
        )
        embed.add_field(name="Кто докладывает", value=data['reporter'], inline=False)
        embed.add_field(name="Кто КМДО", value=data['cmdo'], inline=False)
        embed.add_field(name="Кто Адъютант", value=data['adjutant'], inline=False)
        embed.add_field(name="Кто КМДГ", value=data['cmdg'], inline=False)
        embed.add_field(name="Кто участвовал", value=data['participants'], inline=False)
        embed.add_field(name="Суть доклада", value=data['report'], inline=False)
        embed.add_field(name="Итоги операции", value=data['results'], inline=False)

        await channel.send(embed=embed)
        await interaction.followup.send("Рапорт отправлен!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReportOp(bot))