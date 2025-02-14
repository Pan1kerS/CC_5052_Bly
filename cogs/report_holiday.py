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

class HolidayModal(disnake.ui.Modal):
    def __init__(self, cog, report_data, is_enter=True):
        self.cog = cog
        self.report_data = report_data
        components = []
        
        if is_enter:
            components.extend([
                disnake.ui.TextInput(
                    label="С какого числа",
                    placeholder="Укажите дату начала",
                    custom_id="start_date",
                    style=disnake.TextInputStyle.short,
                    required=True
                ),
                disnake.ui.TextInput(
                    label="До какого числа",
                    placeholder="Укажите дату окончания",
                    custom_id="end_date",
                    style=disnake.TextInputStyle.short,
                    required=True
                ),
            ])
        
        components.append(
            disnake.ui.TextInput(
                label="Причина",
                placeholder="Укажите причину",
                custom_id="reason",
                style=disnake.TextInputStyle.paragraph,
                required=True
            )
        )
        
        super().__init__(
            title="Запрос на мороз",
            components=components,
            custom_id="holiday_modal"
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        if "start_date" in interaction.text_values:
            self.report_data["start_date"] = interaction.text_values["start_date"]
            self.report_data["end_date"] = interaction.text_values["end_date"]
        self.report_data["reason"] = interaction.text_values["reason"]
        await self.cog.submit_report(interaction, self.report_data)

class ReportHoliday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.active_reports = {}
        self.temp_messages = {}

    def get_members_select(self, guild, placeholder):
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
        
        return disnake.ui.Select(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options
        )

    async def start_report(self, interaction: disnake.MessageInteraction):
        if interaction.channel.id != CHANNELS['HOLIDAY_REPORTS']:
            await interaction.response.send_message("Неверный канал", ephemeral=True)
            return

        self.temp_messages[interaction.author.id] = []
        
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Выберите кто запрашивает мороз")
        
        async def reporter_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id] = {"reporter": select.values[0]}
            await self.show_type_selection(inter)

        select.callback = reporter_callback
        view.add_item(select)
        
        message = await interaction.response.send_message("Кто запрашивает мороз?", view=view, ephemeral=True)
        if isinstance(message, disnake.Message):
            self.temp_messages[interaction.author.id].append(message)

    async def show_type_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = disnake.ui.Select(
            placeholder="Выберите тип запроса",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(label="Зайти в отпуск", value="enter"),
                disnake.SelectOption(label="Выйти из отпуска", value="exit")
            ]
        )
        
        async def type_callback(inter: disnake.MessageInteraction):
            is_enter = select.values[0] == "enter"
            self.active_reports[inter.author.id]["type"] = "Зайти" if is_enter else "Выйти"
            await self.show_holiday_modal(inter, is_enter)

        select.callback = type_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите тип запроса:", view=view)

    async def show_holiday_modal(self, interaction: disnake.MessageInteraction, is_enter):
        await self.cleanup_messages(interaction)
        modal = HolidayModal(self, self.active_reports[interaction.author.id], is_enter)
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
            print(f"[Holiday] Отправка данных в таблицу: {data}")
            print(f"[Holiday] Название листа в конфиге: {SHEETS['HOLIDAY']['name']}")
            print(f"[Holiday] Весь конфиг SHEETS['HOLIDAY']: {SHEETS['HOLIDAY']}")

            sheet = self.service.spreadsheets()
            
            range_str = f"Мороз!A:A"
            print(f"[Holiday] Используемый range: {range_str}")
            print(f"[Holiday] Создаем запрос к API...")

            try:
                result = sheet.values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_str,
                    valueRenderOption='FORMATTED_VALUE'
                ).execute()
                print(f"[Holiday] Запрос выполнен успешно")
            except Exception as e:
                print(f"[Holiday] Ошибка при запросе к API: {str(e)}")
                raise e

            current_rows = len(result.get('values', []))
            row_number = current_rows + 1

            # Создаем значения для строки
            row_values = [
                data['reporter'],          # A - Кто запрашивает
                data['type'],              # B - Зайти/Выйти
                data.get('start_date', ''), # C - С какого числа
                data.get('end_date', ''),   # D - До какого числа
                data['reason'],            # E - Причина
                ""                         # F - Одобрено/Отказано
            ]
            
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"Мороз!A:F",
                valueInputOption="RAW",
                body={'values': [row_values]}
            ).execute()

            await self.cleanup_temp_messages(interaction.author.id)

            # Создаем embed для отчета
            report_embed = disnake.Embed(
                title="Запрос на мороз",
                color=disnake.Color.blue()
            )
            report_embed.add_field(name="Кто запрашивает", value=data['reporter'], inline=False)
            report_embed.add_field(name="Тип", value=data['type'], inline=False)
            if data.get('start_date'):
                report_embed.add_field(name="С", value=data['start_date'], inline=False)
                report_embed.add_field(name="До", value=data['end_date'], inline=False)
            report_embed.add_field(name="Причина", value=data['reason'], inline=False)

            # Отправляем embed с пингом роли
            content = f"<@&{ROLES['ADMIN']}>"
            message = await interaction.channel.send(content=content, embed=report_embed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Сохраняем информацию о сообщении
            self.bot.report_messages[message.id] = {
                'sheet_row': row_number,
                'type': 'holiday'
            }
            print(f"[Holiday] Сохранено сообщение {message.id} в report_messages")

            await interaction.delete_original_response()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Ошибка при отправке запроса: {str(e)}",
                delete_after=10
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            print(f"[Holiday] Получена реакция на сообщение {payload.message_id}")
            print(f"[Holiday] Текущие сообщения: {self.bot.report_messages}")

            if payload.message_id not in self.bot.report_messages:
                print(f"[Holiday] Сообщение {payload.message_id} не найдено в report_messages")
                return

            report_info = self.bot.report_messages.get(payload.message_id)
            if report_info['type'] != 'holiday':
                return

            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                print(f"[Holiday] Не найдена гильдия {payload.guild_id}")
                return

            member = guild.get_member(payload.user_id)
            if not member or not any(role.id == ROLES['ADMIN'] for role in member.roles):
                return

            if str(payload.emoji) not in ['✅', '❌']:
                return

            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            row_number = report_info['sheet_row']
            status = "Одобрено" if str(payload.emoji) == '✅' else "Отклонено"

            sheet = self.service.spreadsheets()
            try:
                sheet.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"Мороз!F{row_number}",
                    valueInputOption="RAW",
                    body={'values': [[status]]}
                ).execute()

                embed = message.embeds[0]
                embed.add_field(name="Статус", value=status, inline=False)
                await message.edit(embed=embed)

                # Удаляем сообщение из отслеживаемых после обработки
                self.bot.report_messages.pop(payload.message_id, None)

            except googleapiclient.errors.HttpError as e:
                await channel.send(f"Ошибка при обновлении статуса в таблице: {e}", delete_after=10)

        except Exception as e:
            print(f"Ошибка в обработке реакции: {str(e)}")

def setup(bot):
    if not hasattr(bot, 'report_messages'):
        bot.report_messages = {}
    bot.add_cog(ReportHoliday(bot))
