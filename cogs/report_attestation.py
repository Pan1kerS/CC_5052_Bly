import disnake
from disnake.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
import googleapiclient.errors
from config import (
    CHANNELS, ROLES, ATTESTATION_TYPES,
    KPB_OPTIONS, SPEC_OPTIONS, RANK_OPTIONS,
    SPREADSHEET_ID, SHEETS
)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials/cc-5052-bly-e24abd47118d.json'

class AttestationModal(disnake.ui.Modal):
    def __init__(self, cog, report_data, att_type):
        self.cog = cog
        self.report_data = report_data
        components = [
            disnake.ui.TextInput(
                label="Суть аттестации",
                placeholder="Опишите суть аттестации",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
                required=True
            ),
            disnake.ui.TextInput(
                label="Итоги",
                placeholder="Опишите итоги аттестации",
                custom_id="results",
                style=disnake.TextInputStyle.paragraph,
                required=True
            ),
        ]
        super().__init__(
            title="Аттестация",
            components=components,
            custom_id="attestation_modal"
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        self.report_data["description"] = interaction.text_values["description"]
        self.report_data["results"] = interaction.text_values["results"]
        await self.cog.submit_report(interaction, self.report_data)

class ReportAttestation(commands.Cog):
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
        if interaction.channel.id != CHANNELS['ATTESTATION_REPORTS']:
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
            "Выберите кого аттестовывали",
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
                content=f"Выбранные участники: {', '.join(current_subjects)}\nВыберите ещё или нажмите 'Завершить выбор'",
                view=view
            )

        async def finish_selection(inter: disnake.MessageInteraction):
            await self.show_attestation_type_selection(inter)

        select.callback = subjects_callback
        view.add_item(select)
        
        # Добавляем кнопку очистки списка
        clear_button = disnake.ui.Button(
            label="Очистить список",
            style=disnake.ButtonStyle.danger,
            custom_id="clear_list"
        )
        
        async def clear_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]['subjects'] = []
            await inter.response.edit_message(
                content="Список участников очищен. Выберите участников:",
                view=view
            )
            
        clear_button.callback = clear_callback
        view.add_item(clear_button)
        
        # Добавляем кнопку завершения выбора
        finish_button = disnake.ui.Button(
            label="Завершить выбор",
            style=disnake.ButtonStyle.success,
            custom_id="finish_selection"
        )
        finish_button.callback = finish_selection
        view.add_item(finish_button)
        
        await interaction.response.edit_message(content="Выберите участников:", view=view)

    async def show_attestation_type_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = disnake.ui.Select(
            placeholder="Выберите вид аттестации",
            options=[
                disnake.SelectOption(label=name, value=value)
                for name, value in ATTESTATION_TYPES.items()
            ]
        )
        
        async def type_callback(inter: disnake.MessageInteraction):
            att_type = select.values[0]
            self.active_reports[inter.author.id]["attestation_type"] = att_type
            
            if att_type == "kpb":
                await self.show_kpb_selection(inter)
            elif att_type == "spec":
                await self.show_spec_selection(inter)
            elif att_type == "rank":
                await self.show_rank_selection(inter)
            else:
                self.active_reports[inter.author.id]["result"] = "+"
                await self.show_attestation_modal(inter)

        select.callback = type_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите вид аттестации:", view=view)

    async def show_kpb_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = disnake.ui.Select(
            placeholder="Выберите КПБ",
            options=[disnake.SelectOption(label=f"КПБ {num}", value=num) for num in KPB_OPTIONS],
            min_values=1,
            max_values=len(KPB_OPTIONS)
        )
        
        async def kpb_callback(inter: disnake.MessageInteraction):
            if 'result' not in self.active_reports[inter.author.id]:
                self.active_reports[inter.author.id]['result'] = []
            
            current_kpb = self.active_reports[inter.author.id]['result']
            for value in select.values:
                if value not in current_kpb:
                    current_kpb.append(value)
            
            await inter.response.edit_message(
                content=f"Выбранные КПБ: {', '.join(current_kpb)}\nВыберите ещё или нажмите 'Завершить выбор'",
                view=view
            )

        async def finish_kpb_selection(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]['result'] = ", ".join(self.active_reports[inter.author.id]['result'])
            await self.show_attestation_modal(inter)

        select.callback = kpb_callback
        view.add_item(select)
        
        # Добавляем кнопку завершения выбора
        finish_button = disnake.ui.Button(
            label="Завершить выбор",
            style=disnake.ButtonStyle.success,
            custom_id="finish_kpb_selection"
        )
        finish_button.callback = finish_kpb_selection
        view.add_item(finish_button)
        
        # Добавляем кнопку очистки списка
        clear_button = disnake.ui.Button(
            label="Очистить список",
            style=disnake.ButtonStyle.danger,
            custom_id="clear_kpb_list"
        )
        
        async def clear_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]['result'] = []
            await inter.response.edit_message(
                content="Список КПБ очищен. Выберите КПБ:",
                view=view
            )
            
        clear_button.callback = clear_callback
        view.add_item(clear_button)
        
        await interaction.response.edit_message(content="Выберите КПБ:", view=view)

    async def show_spec_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        spec_descriptions = {
            "HT": "Heavy Trooper",
            "S": "Scout",
            "D": "Diversionist",
            "P": "Pilot",
            "MI": "Medic Interpreter",
            "M": "Medic",
            "MS": "Medic Specialist",
            "ENG": "Engineer",
            "ARF": "Advanced Recon Force",
            "BCM": "Bacta Company Medic",
            "BCMS": "Bacta Company Medic Specialist"
        }
        select = disnake.ui.Select(
            placeholder="Выберите специализацию",
            options=[
                disnake.SelectOption(
                    label=spec,
                    value=spec,
                    description=spec_descriptions.get(spec, "")
                ) for spec in SPEC_OPTIONS
            ]
        )
        
        async def spec_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["spec"] = select.values[0]
            await self.show_attestation_modal(inter)

        select.callback = spec_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите специализацию:", view=view)

    async def show_rank_selection(self, interaction: disnake.MessageInteraction):
        view = disnake.ui.View()
        select = disnake.ui.Select(
            placeholder="Выберите звание",
            options=[disnake.SelectOption(label=rank, value=rank) for rank in RANK_OPTIONS]
        )
        
        async def rank_callback(inter: disnake.MessageInteraction):
            self.active_reports[inter.author.id]["result"] = select.values[0]
            await self.show_attestation_modal(inter)

        select.callback = rank_callback
        view.add_item(select)
        
        await interaction.response.edit_message(content="Выберите звание:", view=view)

    async def show_attestation_modal(self, interaction: disnake.MessageInteraction):
        await self.cleanup_messages(interaction)
        modal = AttestationModal(self, self.active_reports[interaction.author.id], self.active_reports[interaction.author.id]["attestation_type"])
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
                range=f"'Аттестация'!A:A",
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            current_rows = len(result.get('values', []))
            row_number = current_rows + 1  # Следующая строка

            # Создаем список значений для всех столбцов (A-L)
            row_values = [""] * 12  # 12 столбцов от A до L
            
            # Заполняем базовые значения
            row_values[0] = data['reporter']  # A - Кто докладывает
            row_values[1] = ", ".join(data['subjects'])  # B - Кого аттестовал
            
            # Заполняем соответствующий столбец типа аттестации
            att_type = data['attestation_type']
            if att_type == "jetpack":
                row_values[2] = "+"  # C - JetPack/JumpPack
            elif att_type == "kpb":
                row_values[3] = "+"  # D - КПБ
            elif att_type == "final":
                row_values[4] = "+"  # E - Финальная аттестация
            elif att_type == "spec":
                row_values[5] = data.get('spec', '')  # F - Специализация
            elif att_type == "civil":
                row_values[6] = "+"  # G - Работа с гражданскими
            elif att_type == "city":
                row_values[7] = "+"  # H - Работа в густонаселенных городах
            elif att_type == "rank":
                row_values[8] = data.get('rank', '')  # I - Звание

            row_values[9] = data.get('description', '')  # J - Суть аттестации
            row_values[10] = data.get('results', '')  # K - Итоги
            # L - Одобренно/отказано (будет заполнено при реакции)
            
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'Аттестация'!A:L",
                valueInputOption="RAW",
                body={'values': [row_values]}
            ).execute()

            await self.cleanup_temp_messages(interaction.author.id)

            # Создаем embed для отчета
            report_embed = disnake.Embed(
                title="Отчет об аттестации",
                color=disnake.Color.blue()
            )
            report_embed.add_field(name="Кто докладывает", value=data['reporter'], inline=False)
            report_embed.add_field(name="Кого аттестовывали", value=", ".join(data['subjects']), inline=False)
            report_embed.add_field(name="Вид аттестации", value=att_type, inline=False)
            if att_type == "rank":
                report_embed.add_field(name="Звание", value=data.get('rank', ''), inline=False)
            elif att_type == "spec":
                report_embed.add_field(name="Специализация", value=data.get('spec', ''), inline=False)
            if data.get('description'):
                report_embed.add_field(name="Суть аттестации", value=data['description'], inline=False)
            if data.get('results'):
                report_embed.add_field(name="Итоги", value=data['results'], inline=False)

            # Отправляем embed с пингом роли
            content = f"<@&{ROLES['ADMIN']}>"
            message = await interaction.channel.send(content=content, embed=report_embed)
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Сохраняем информацию о сообщении
            self.bot.report_messages[message.id] = {
                'sheet_row': row_number,
                'type': 'attestation'
            }

            await interaction.edit_original_response(content="Отчет успешно отправлен!")

        except Exception as e:
            await interaction.edit_original_response(content=f"Ошибка при отправке отчета: {str(e)}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.message_id not in self.bot.report_messages:
                return

            report_info = self.bot.report_messages.get(payload.message_id)
            # Проверяем, что это наш тип отчета
            if report_info['type'] != 'attestation':
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
                    range=f"'Аттестация'!L{row_number}",
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
    bot.add_cog(ReportAttestation(bot))
