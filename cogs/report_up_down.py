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

class RankModal(disnake.ui.Modal):
    def __init__(self, cog, report_data):
        self.cog = cog
        self.report_data = report_data
        components = [
            disnake.ui.TextInput(
                label="Повышение/понижение",
                placeholder="Укажите: повышение/понижение",
                custom_id="type",
                style=disnake.TextInputStyle.short,
                required=True
            ),
            disnake.ui.TextInput(
                label="Причина",
                placeholder="Укажите причину",
                custom_id="reason",
                style=disnake.TextInputStyle.paragraph,
                required=True
            )
        ]
        super().__init__(
            title="Изменение звания",
            components=components,
            custom_id="rank_modal"
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        self.report_data["type"] = interaction.text_values["type"]
        self.report_data["reason"] = interaction.text_values["reason"]
        await self.cog.submit_report(interaction, self.report_data)

class ReportRank(commands.Cog):
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
        if interaction.channel.id != CHANNELS['RANK_REPORTS']:
            await interaction.response.send_message("Неверный канал", ephemeral=True)
            return

        self.temp_messages[interaction.author.id] = []
        
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Кто докладывает?")
        
        async def reporter_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id] = {"reporter": select.values[0]}
            await self.show_subject_selection(inter)

        select.callback = reporter_callback
        view.add_item(select)
        
        message = await interaction.response.send_message("Кто докладывает?", view=view, ephemeral=True)
        if isinstance(message, disnake.Message):
            self.temp_messages[interaction.author.id].append(message)

    async def show_subject_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_members_select(interaction.guild, "Кого повышают/понижают?")
        
        async def subject_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["subject"] = select.values[0]
            await self.show_current_rank_selection(inter)

        select.callback = subject_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Кого повышают/понижают?", view=view)

    def get_rank_select(self, placeholder):
        rank_options = [
            disnake.SelectOption(
                label=rank,
                value=rank,
                description=f"Звание {rank}"
            ) for rank in ["CT", "PVT", "PFC", "CS", "CPL", "SGT", "SSG", "SGM", "LT", "SLT", "SPLT", "CPT"]
        ]
        
        return disnake.ui.Select(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=rank_options
        )

    async def show_current_rank_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_rank_select("Выберите текущее звание")
        
        async def current_rank_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["current_rank"] = select.values[0]
            await self.show_new_rank_selection(inter)

        select.callback = current_rank_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите текущее звание:", view=view)

    async def show_new_rank_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = self.get_rank_select("Выберите новое звание")
        
        async def new_rank_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["new_rank"] = select.values[0]
            await self.show_rank_modal(inter)

        select.callback = new_rank_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите новое звание:", view=view)

    async def show_rank_modal(self, interaction: disnake.MessageInteraction):
        await self.cleanup_messages(interaction)
        modal = RankModal(self, self.active_reports[interaction.author.id])
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
            print(f"[Rank] Отправка данных в таблицу: {data}")

            sheet = self.service.spreadsheets()
            
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'Ранг'!A:A",
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            current_rows = len(result.get('values', []))
            row_number = current_rows + 1

            # Создаем значения для строки
            row_values = [
                data['reporter'],          # A - Кто докладывает
                data['subject'],           # B - Кого повышают/понижают
                data['current_rank'],      # C - Какое звание было
                data['new_rank'],          # D - Какое станет
                data['type'],              # E - Повышение/понижение
                data['reason'],            # F - Причина
                ""                         # G - Одобренно/отказано
            ]
            
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'Ранг'!A:G",
                valueInputOption="RAW",
                body={'values': [row_values]}
            ).execute()

            await self.cleanup_temp_messages(interaction.author.id)

            # Создаем embed для отчета
            report_embed = disnake.Embed(
                title="Запрос на изменение ранга",
                color=disnake.Color.blue()
            )
            report_embed.add_field(name="Кто докладывает", value=data['reporter'], inline=False)
            report_embed.add_field(name="Кого повышают/понижают", value=data['subject'], inline=False)
            report_embed.add_field(name="Текущее звание", value=data['current_rank'], inline=False)
            report_embed.add_field(name="Новое звание", value=data['new_rank'], inline=False)
            report_embed.add_field(name="Тип изменения", value=data['type'], inline=False)
            report_embed.add_field(name="Причина", value=data['reason'], inline=False)

            # Отправляем embed с пингом роли
            content = f"<@&{ROLES['ADMIN']}>"
            message = await interaction.channel.send(content=content, embed=report_embed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Сохраняем информацию о сообщении
            self.bot.report_messages[message.id] = {
                'sheet_row': row_number,
                'type': 'rank'
            }

            await interaction.delete_original_response()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Ошибка при отправке запроса: {str(e)}",
                delete_after=10
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.message_id not in self.bot.report_messages:
                return

            report_info = self.bot.report_messages.get(payload.message_id)
            if report_info['type'] != 'rank':
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
                    range=f"'Ранг'!G{row_number}",
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
    bot.add_cog(ReportRank(bot))
