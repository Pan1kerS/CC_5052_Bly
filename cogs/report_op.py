import disnake
from disnake.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
import googleapiclient.errors
from config import (
    CHANNELS, ROLES, SPREADSHEET_ID, SHEETS
)
from datetime import datetime
import pytz

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials/cc-5052-bly-e24abd47118d.json'

class OperationModal(disnake.ui.Modal):
    def __init__(self, cog, report_data):
        self.cog = cog
        self.report_data = report_data
        components = [
            disnake.ui.TextInput(
                label="Задача ВАР",
                placeholder="Укажите общую задачу ВАР",
                custom_id="var_task",
                style=disnake.TextInputStyle.paragraph,
                required=True
            ),
            disnake.ui.TextInput(
                label="Задача вашего отделения",
                placeholder="Укажите задачу вашего отделения",
                custom_id="squad_task",
                style=disnake.TextInputStyle.paragraph,
                required=True
            ),
            disnake.ui.TextInput(
                label="Описание операции",
                placeholder="Опишите как прошла операция",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
                required=True
            )
        ]
        super().__init__(
            title="Боевой вылет",
            components=components,
            custom_id="operation_modal"
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        self.report_data["var_task"] = interaction.text_values["var_task"]
        self.report_data["squad_task"] = interaction.text_values["squad_task"]
        self.report_data["description"] = interaction.text_values["description"]
        await self.cog.submit_report(interaction, self.report_data)

class ReportOperation(commands.Cog):
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
        
        # Устанавливаем max_values не больше, чем количество доступных опций
        actual_max = min(max_values, len(options))
        return disnake.ui.Select(
            placeholder=placeholder,
            min_values=1,
            max_values=actual_max,
            options=options
        )

    async def start_report(self, interaction: disnake.MessageInteraction):
        if interaction.channel.id != CHANNELS['COMBAT_REPORTS']:
            await interaction.response.send_message("Неверный канал", ephemeral=True)
            return

        self.temp_messages[interaction.author.id] = []
        
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Выберите кто докладывает")
        
        async def reporter_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id] = {"reporter": select.values[0]}
            await self.show_squad_leader_selection(inter)

        select.callback = reporter_callback
        view.add_item(select)
        
        message = await interaction.response.send_message("Кто докладывает?", view=view, ephemeral=True)
        if isinstance(message, disnake.Message):
            self.temp_messages[interaction.author.id].append(message)

    async def show_squad_leader_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Выберите командира отделения")
        
        async def squad_leader_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["squad_leader"] = select.values[0]
            await self.show_participants_selection(inter)

        select.callback = squad_leader_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите командира отделения:", view=view)

    async def show_participants_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Выберите участников", max_values=10)
        
        # Создаем список для хранения выбранных участников
        if 'participants' not in self.active_reports[interaction.author.id]:
            self.active_reports[interaction.author.id]['participants'] = []
        
        async def participants_callback(inter: disnake.MessageInteraction):
            # Добавляем новых выбранных участников
            current_participants = self.active_reports[inter.author.id]['participants']
            current_participants.extend(select.values)
            # Убираем дубликаты
            self.active_reports[inter.author.id]['participants'] = list(dict.fromkeys(current_participants))
            
            # Обновляем сообщение, показывая текущий список участников
            participants_list = "\n".join(self.active_reports[inter.author.id]['participants'])
            await inter.response.edit_message(
                content=f"Выбранные участники:\n{participants_list}\n\nВыберите ещё участников или нажмите 'Завершить выбор'",
                view=view
            )

        select.callback = participants_callback
        view.add_item(select)
        
        # Добавляем кнопку завершения выбора
        finish_button = disnake.ui.Button(
            label="Завершить выбор",
            style=disnake.ButtonStyle.success,
            custom_id="finish_selection"
        )
        
        async def finish_callback(inter: disnake.MessageInteraction):
            if not self.active_reports[inter.author.id]['participants']:
                await inter.response.send_message(
                    "Выберите хотя бы одного участника!",
                    ephemeral=True
                )
                return
                
            # Преобразуем список участников в строку
            self.active_reports[inter.author.id]['participants'] = ", ".join(
                self.active_reports[inter.author.id]['participants']
            )
            await self.show_operation_modal(inter)

        finish_button.callback = finish_callback
        view.add_item(finish_button)
        
        # Добавляем кнопку очистки списка
        clear_button = disnake.ui.Button(
            label="Очистить список",
            style=disnake.ButtonStyle.danger,
            custom_id="clear_list"
        )
        
        async def clear_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]['participants'] = []
            await inter.response.edit_message(
                content="Список участников очищен. Выберите участников заново.",
                view=view
            )

        clear_button.callback = clear_callback
        view.add_item(clear_button)
        
        await interaction.response.edit_message(
            content="Выберите участников операции:",
            view=view
        )

    async def show_operation_modal(self, interaction: disnake.MessageInteraction):
        await self.cleanup_messages(interaction)
        modal = OperationModal(self, self.active_reports[interaction.author.id])
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
                range=f"'Боевой вылет'!A:A",
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            current_rows = len(result.get('values', []))
            row_number = current_rows + 1

            # Добавляем текущее время (московское)
            msk_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(msk_tz).strftime('%d.%m.%Y %H:%M МСК')
            
            # Создаем значения для строки
            row_values = [
                current_time,              # A - Время отправки
                data['reporter'],          # B - Кто докладывает
                data['squad_leader'],      # C - Командир отделения
                data['participants'],      # D - Кто участвовал
                data['var_task'],          # E - Задача ВАР
                data['squad_task'],        # F - Задача вашего отделения
                data['description'],       # G - Описание операции
                ""                         # H - Статус
            ]
            
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'Боевой вылет'!A:H",
                valueInputOption="RAW",
                body={'values': [row_values]}
            ).execute()

            await self.cleanup_temp_messages(interaction.author.id)

            # Создаем embed для отчета
            report_embed = disnake.Embed(
                title="Боевой вылет",
                color=disnake.Color.blue()
            )
            report_embed.add_field(name="Кто докладывает", value=data['reporter'], inline=False)
            report_embed.add_field(name="Командир отделения", value=data['squad_leader'], inline=False)
            report_embed.add_field(name="Участники", value=data['participants'], inline=False)
            report_embed.add_field(name="Задача ВАР", value=data['var_task'], inline=False)
            report_embed.add_field(name="Задача отделения", value=data['squad_task'], inline=False)
            report_embed.add_field(name="Описание", value=data['description'], inline=False)

            # Отправляем embed
            content = f"<@&{ROLES['ADMIN']}>"
            message = await interaction.channel.send(content=content, embed=report_embed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Сохраняем информацию о сообщении для отслеживания
            self.bot.report_messages[message.id] = {
                'sheet_row': row_number,
                'type': 'combat'
            }

            # Удаляем ephemeral сообщение
            await interaction.delete_original_response()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Ошибка при отправке рапорта: {str(e)}",
                delete_after=10
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.message_id not in self.bot.report_messages:
                return

            report_info = self.bot.report_messages.get(payload.message_id)
            # Проверяем, что это наш тип отчета
            if report_info['type'] != 'combat':
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
                    range=f"'Боевой вылет'!H{row_number}",
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
    bot.add_cog(ReportOperation(bot))