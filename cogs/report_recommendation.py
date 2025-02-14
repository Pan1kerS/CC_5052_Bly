import disnake
from disnake.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
import googleapiclient.errors
from config import (
    CHANNELS, ROLES, SPREADSHEET_ID, SHEETS
)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials/cc-5052-bly-e24abd47118d.json'

class RecommendationModal(disnake.ui.Modal):
    def __init__(self, cog, report_data):
        self.cog = cog
        self.report_data = report_data
        components = [
            disnake.ui.TextInput(
                label="Суть рекомендации",
                placeholder="Опишите суть рекомендации",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
                required=True
            )
        ]
        super().__init__(
            title="Рекомендация",
            components=components,
            custom_id="recommendation_modal"
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        self.report_data["description"] = interaction.text_values["description"]
        await self.cog.submit_report(interaction, self.report_data)

class ReportRecommendation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.active_reports = {}
        self.temp_messages = {}

    def get_members_select(self, guild, placeholder, max_values=1):
        options = []
        for member in guild.members:
            if not member.bot:
                options.append(
                    disnake.SelectOption(
                        label=member.display_name,
                        value=member.display_name,
                        description=f"ID: {member.id}"
                    )
                )
        
        actual_max = min(max_values, len(options))
        return disnake.ui.Select(
            placeholder=placeholder,
            min_values=1,
            max_values=actual_max,
            options=options
        )

    async def start_report(self, interaction: disnake.MessageInteraction):
        if interaction.channel.id != CHANNELS['RECOMMENDATION_REPORTS']:
            await interaction.response.send_message("Неверный канал", ephemeral=True)
            return

        self.temp_messages[interaction.author.id] = []
        
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Выберите кто докладывает")
        
        async def reporter_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id] = {"reporter": select.values[0]}
            await self.show_subjects_selection(inter)

        select.callback = reporter_callback
        view.add_item(select)
        
        message = await interaction.response.send_message("Кто докладывает?", view=view, ephemeral=True)
        if isinstance(message, disnake.Message):
            self.temp_messages[interaction.author.id].append(message)

    async def show_subjects_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_members_select(
            interaction.guild,
            "Выберите кого рекомендуют",
            max_values=10
        )
        
        async def subjects_callback(inter: disnake.MessageInteraction):
            if 'subjects' not in self.active_reports[inter.author.id]:
                self.active_reports[inter.author.id]['subjects'] = []
            
            current_subjects = self.active_reports[inter.author.id]['subjects']
            for value in select.values:
                if value not in current_subjects:
                    current_subjects.append(value)
            
            await inter.response.edit_message(
                content=f"Выбранные бойцы: {', '.join(current_subjects)}\nВыберите ещё или нажмите 'Завершить выбор'",
                view=view
            )

        async def finish_selection(inter: disnake.MessageInteraction):
            await self.show_recommendation_modal(inter)

        select.callback = subjects_callback
        view.add_item(select)
        
        # Добавляем кнопку завершения выбора
        finish_button = disnake.ui.Button(
            label="Завершить выбор",
            style=disnake.ButtonStyle.success,
            custom_id="finish_selection"
        )
        finish_button.callback = finish_selection
        view.add_item(finish_button)
        
        # Добавляем кнопку очистки списка
        clear_button = disnake.ui.Button(
            label="Очистить список",
            style=disnake.ButtonStyle.danger,
            custom_id="clear_list"
        )
        
        async def clear_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]['subjects'] = []
            await inter.response.edit_message(
                content="Список очищен. Выберите бойцов:",
                view=view
            )
            
        clear_button.callback = clear_callback
        view.add_item(clear_button)
        
        await interaction.response.edit_message(content="Выберите кого рекомендуют:", view=view)

    async def show_recommendation_modal(self, interaction: disnake.MessageInteraction):
        await self.cleanup_messages(interaction)
        modal = RecommendationModal(self, self.active_reports[interaction.author.id])
        await interaction.response.send_modal(modal)

    async def cleanup_messages(self, interaction: disnake.MessageInteraction):
        try:
            if hasattr(interaction, 'message') and interaction.message:
                try:
                    await interaction.message.delete()
                except:
                    pass
        except:
            pass

    async def cleanup_temp_messages(self, user_id):
        if user_id in self.temp_messages:
            for message in self.temp_messages[user_id]:
                try:
                    await message.delete()
                except:
                    pass
            del self.temp_messages[user_id]

    async def submit_report(self, interaction: disnake.ModalInteraction, data):
        try:
            await interaction.response.defer(ephemeral=True)

            sheet = self.service.spreadsheets()
            
            # Получаем текущее количество строк
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'Рекомендация'!A:A",
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            current_rows = len(result.get('values', []))
            row_number = current_rows + 1

            # Создаем значения для строки в правильном порядке
            row_values = [
                data['reporter'],          # A - Кто докладывает
                ", ".join(data['subjects']), # B - Кого рекомендует
                data['description'],       # C - Суть рекомендации
                ""                         # D - Одобренно/Отказано
            ]
            
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'Рекомендация'!A:D",
                valueInputOption="RAW",
                body={'values': [row_values]}
            ).execute()

            await self.cleanup_temp_messages(interaction.author.id)

            # Создаем embed для отчета
            report_embed = disnake.Embed(
                title="Рекомендация",
                color=disnake.Color.blue()
            )
            report_embed.add_field(name="Кто докладывает", value=data['reporter'], inline=False)
            report_embed.add_field(name="Кого рекомендует", value=", ".join(data['subjects']), inline=False)
            report_embed.add_field(name="Суть рекомендации", value=data['description'], inline=False)

            # Отправляем embed с пингом роли
            content = f"<@&{ROLES['ADMIN']}>"
            message = await interaction.channel.send(content=content, embed=report_embed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Сохраняем информацию о сообщении
            self.bot.report_messages[message.id] = {
                'sheet_row': row_number,
                'type': 'recommendation'
            }

            # Удаляем ephemeral сообщение
            await interaction.delete_original_response()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Ошибка при отправке рекомендации: {str(e)}",
                delete_after=10
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.message_id not in self.bot.report_messages:
                return

            report_info = self.bot.report_messages.get(payload.message_id)
            if report_info['type'] != 'recommendation':
                return

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            member = message.guild.get_member(payload.user_id)
            if not member or not any(role.id == ROLES['ADMIN'] for role in member.roles):
                return

            if str(payload.emoji) not in ['✅', '❌']:
                return

            row_number = report_info['sheet_row']

            status = "Одобрено" if str(payload.emoji) == '✅' else "Отклонено"
            sheet = self.service.spreadsheets()
            try:
                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"'Рекомендация'!D{row_number}",
                    valueInputOption="RAW",
                    body={'values': [[status]]}
                ).execute()

                embed = message.embeds[0]
                embed.add_field(name="Статус", value=status, inline=False)
                await message.edit(embed=embed)

                self.bot.report_messages.pop(payload.message_id, None)

            except googleapiclient.errors.HttpError as e:
                await channel.send(f"Ошибка при обновлении статуса в таблице: {e}", delete_after=10)

        except Exception as e:
            print(f"Ошибка в обработке реакции: {str(e)}")

def setup(bot):
    if not hasattr(bot, 'report_messages'):
        bot.report_messages = {}
    bot.add_cog(ReportRecommendation(bot))
