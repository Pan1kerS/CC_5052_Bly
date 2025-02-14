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

class TrainingModal(disnake.ui.Modal):
    def __init__(self, cog, report_data):
        self.cog = cog
        self.report_data = report_data
        components = [
            disnake.ui.TextInput(
                label="Суть тренировки/симуляции",
                placeholder="Опишите суть тренировки",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
                required=True
            ),
            disnake.ui.TextInput(
                label="Итоги",
                placeholder="Опишите итоги тренировки",
                custom_id="results",
                style=disnake.TextInputStyle.paragraph,
                required=True
            )
        ]
        super().__init__(
            title="Тренировка",
            components=components,
            custom_id="training_modal"
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        self.report_data["description"] = interaction.text_values["description"]
        self.report_data["results"] = interaction.text_values["results"]
        await self.cog.submit_report(interaction, self.report_data)

class ReportTraining(commands.Cog):
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
        if interaction.channel.id != CHANNELS['TRAINING_REPORTS']:
            await interaction.response.send_message("Неверный канал", ephemeral=True)
            return

        self.temp_messages[interaction.author.id] = []
        
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Выберите кто проводил/симуляцию")
        
        async def reporter_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id] = {"reporter": select.values[0]}
            await self.show_participants_selection(inter)

        select.callback = reporter_callback
        view.add_item(select)
        
        message = await interaction.response.send_message("Кто проводил тренировку/симуляцию?", view=view, ephemeral=True)
        if isinstance(message, disnake.Message):
            self.temp_messages[interaction.author.id].append(message)

    async def show_participants_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_members_select(
            interaction.guild,
            "Выберите участников тренировки/симуляции",
            max_values=25
        )
        
        async def participants_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["participants"] = select.values
            await self.show_type_selection(inter)

        select.callback = participants_callback
        view.add_item(select)
        
        # Добавляем кнопку завершения выбора
        finish_button = disnake.ui.Button(
            label="Завершить выбор",
            style=disnake.ButtonStyle.success,
            custom_id="finish_selection"
        )
        finish_button.callback = self.finish_selection
        view.add_item(finish_button)
        
        # Добавляем кнопку очистки списка
        clear_button = disnake.ui.Button(
            label="Очистить список",
            style=disnake.ButtonStyle.danger,
            custom_id="clear_list"
        )
        clear_button.callback = self.clear_callback
        view.add_item(clear_button)
        
        await interaction.response.edit_message(content="Выберите участников тренировки/симуляции:", view=view)

    def get_type_select(self):
        type_options = [
            disnake.SelectOption(
                label="Тренировка",
                value="Тренировка",
                description="Отчет о тренировке"
            ),
            disnake.SelectOption(
                label="Симуляция",
                value="Симуляция",
                description="Отчет о симуляции"
            )
        ]
        
        return disnake.ui.Select(
            placeholder="Выберите тип отчета",
            min_values=1,
            max_values=1,
            options=type_options
        )

    async def show_type_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_type_select()
        
        async def type_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["type"] = select.values[0]
            await self.show_training_modal(inter)

        select.callback = type_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите тип отчета:", view=view)

    async def show_training_modal(self, interaction: disnake.MessageInteraction):
        await self.cleanup_messages(interaction)
        modal = TrainingModal(self, self.active_reports[interaction.author.id])
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
            print(f"[Training] Отправка данных в таблицу: {data}")

            sheet = self.service.spreadsheets()
            
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{SHEETS['TRAINING']['name']}'!A:A",
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            current_rows = len(result.get('values', []))
            row_number = current_rows + 1

            # Добавляем текущее время (московское)
            msk_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(msk_tz).strftime('%d.%m.%Y %H:%M МСК')

            # Создаем значения для строки
            row_values = [
                current_time,                        # A - Время отправки
                data['reporter'],                    # B - Кто проводил (было A)
                data.get('type', 'Тренировка'),     # C - Тренировка/симуляция (было B)
                data['description'],                 # D - Суть тренировки/симуляции (было C)
                ", ".join(data['participants']),     # E - Участники (было D)
                data.get('results', ''),            # F - Итоги (было E)
                ""                                  # G - Одобренно/отказано (было F)
            ]
            
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{SHEETS['TRAINING']['name']}'!A:G",
                valueInputOption="RAW",
                body={'values': [row_values]}
            ).execute()

            await self.cleanup_temp_messages(interaction.author.id)

            # Создаем embed для отчета
            report_embed = disnake.Embed(
                title="Отчет о тренировке/симуляции",
                color=disnake.Color.blue()
            )
            report_embed.add_field(name="Кто проводил", value=data['reporter'], inline=False)
            report_embed.add_field(name="Тип", value=data['type'], inline=False)
            report_embed.add_field(name="Суть тренировки/симуляции", value=data['description'], inline=False)
            report_embed.add_field(name="Участники", value=", ".join(data['participants']), inline=False)
            report_embed.add_field(name="Итоги", value=data['results'], inline=False)

            # Отправляем embed с пингом роли
            content = f"<@&{ROLES['ADMIN']}>"
            message = await interaction.channel.send(content=content, embed=report_embed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Сохраняем информацию о сообщении
            self.bot.report_messages[message.id] = {
                'sheet_row': row_number,
                'type': 'training'
            }

            await interaction.delete_original_response()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Ошибка при отправке отчета: {str(e)}",
                delete_after=10
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.message_id not in self.bot.report_messages:
                return

            report_info = self.bot.report_messages.get(payload.message_id)
            if report_info['type'] != 'training':
                return

            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
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
                    range=f"'{SHEETS['TRAINING']['name']}'!G{row_number}",
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

    async def finish_selection(self, interaction: disnake.MessageInteraction):
        await self.show_type_selection(interaction)

    async def clear_callback(self, interaction: disnake.MessageInteraction):
        await self.show_participants_selection(interaction)

def setup(bot):
    if not hasattr(bot, 'report_messages'):
        bot.report_messages = {}
    bot.add_cog(ReportTraining(bot))
