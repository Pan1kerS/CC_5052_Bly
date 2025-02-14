import disnake
from disnake.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import SPREADSHEET_ID
from datetime import datetime
import asyncio
import googleapiclient

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials/cc-5052-bly-e24abd47118d.json'

class NewSoldierModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Позывной",
                placeholder="Вписать позывной, если нету, то номер",
                custom_id="callsign",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=True
            ),
            disnake.ui.TextInput(
                label="Номер",
                placeholder="Например: 1543 или 02-1234",
                custom_id="number",
                style=disnake.TextInputStyle.short,
                max_length=10,
                required=True
            ),
            disnake.ui.TextInput(
                label="Звание",
                placeholder="Пишите CT",
                custom_id="rank",
                style=disnake.TextInputStyle.short,
                max_length=10,
                required=True
            ),
            disnake.ui.TextInput(
                label="Время",
                placeholder="Например: МСК+2 или МСК-1 или МСК",
                custom_id="time",
                style=disnake.TextInputStyle.short,
                max_length=10,
                required=True
            ),
            disnake.ui.TextInput(
                label="Дата зачисления",
                placeholder="Формат: ДД.ММ.ГГГГ",
                custom_id="join_date",
                style=disnake.TextInputStyle.short,
                max_length=10,
                required=True
            )
        ]
        super().__init__(
            title="Добавление нового бойца",
            components=components,
            custom_id="new_soldier_modal"
        )

# Добавляем новый класс для модального окна изменения данных
class EditDataModal(disnake.ui.Modal):
    def __init__(self, field_name: str):
        self.field_name = field_name
        components = [
            disnake.ui.TextInput(
                label="Позывной",
                placeholder="Введите свой текущий позывной",
                custom_id="current_callsign",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=True
            ),
            disnake.ui.TextInput(
                label=f"Текущее {field_name}",
                placeholder=f"Введите текущее {field_name.lower()}",
                custom_id="current_value",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=True
            ),
            disnake.ui.TextInput(
                label=f"Новое {field_name}",
                placeholder=f"Введите новое {field_name.lower()}",
                custom_id="new_value",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=True
            )
        ]
        super().__init__(
            title=f"Изменение {field_name}",
            components=components,
            custom_id=f"edit_{field_name.lower()}_modal"
        )

class TableButtons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)

    @commands.slash_command(
        name="setup_table_buttons",
        description="Настроить кнопки для работы с таблицей"
    )
    @commands.has_permissions(administrator=True)
    async def setup_table_buttons(self, interaction: disnake.ApplicationCommandInteraction):
        # Очищаем канал от старых сообщений, кроме кнопок
        async for message in interaction.channel.history(limit=100):
            if not message.components:
                await message.delete()

        # Проверяем, есть ли уже кнопки
        has_buttons = False
        async for message in interaction.channel.history(limit=1):
            if message.components:
                has_buttons = True
                break

        if not has_buttons:
            view = disnake.ui.View(timeout=None)
            
            # Кнопка "Новый боец"
            new_soldier_button = disnake.ui.Button(
                style=disnake.ButtonStyle.success,
                label="➕ Новый боец",
                custom_id="new_soldier"
            )
            view.add_item(new_soldier_button)
            
            # Кнопка "Изменить данные"
            edit_data_button = disnake.ui.Button(
                style=disnake.ButtonStyle.primary,
                label="📝 Изменить данные",
                custom_id="edit_data"
            )
            view.add_item(edit_data_button)

            embed = disnake.Embed(
                title="Управление таблицей",
                description="Используйте кнопки ниже для работы с таблицей личного состава",
                color=disnake.Color.blue()
            )
            await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "Кнопки управления таблицей настроены!",
            ephemeral=True
        )

    def validate_timezone(self, time_str):
        """Проверяет формат временной зоны"""
        # Приводим к верхнему регистру
        time_str = time_str.upper()
        
        if time_str == "МСК":
            return True
        
        # Убираем все пробелы между МСК и знаком +/-
        time_str = time_str.replace("МСК ", "МСК")
        
        if time_str.startswith("МСК+") or time_str.startswith("МСК-"):
            try:
                # Убираем все пробелы после знака +/- и конвертируем в число
                offset = int(time_str[4:].strip())
                return -12 <= offset <= 12  # проверяем, что смещение в разумных пределах
            except ValueError:
                return False
        
        return False

    async def add_new_soldier(self, interaction: disnake.ModalInteraction):
        try:
            # Получаем значения из формы
            callsign = interaction.text_values["callsign"]
            number = interaction.text_values["number"]
            rank = interaction.text_values["rank"]
            time = interaction.text_values["time"].upper()
            join_date = interaction.text_values["join_date"]

            # Проверяем формат даты
            try:
                datetime.strptime(join_date, '%d.%m.%Y')
            except ValueError:
                await interaction.edit_original_response(
                    content="Неверный формат даты. Используйте ДД.ММ.ГГГГ"
                )
                return

            # Проверяем формат временной зоны
            if not self.validate_timezone(time):
                await interaction.edit_original_response(
                    content="Неверный формат времени. Используйте: МСК, МСК +1, МСК+ 1, МСК +2, МСК-1 и т.п."
                )
                return

            # Подготавливаем данные для записи
            values = [[
                callsign,
                number,
                rank,
                'Regular',  # Колонка D
                'R',        # Колонка E
                time,
                join_date,
                'Активен'   # Колонка H
            ]]

            # Находим первую пустую строку и записываем данные
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='АКТУАЛЬНЫЕТЕСТ!A2:A'
            ).execute()
            next_row = len(result.get('values', [])) + 2

            self.service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'АКТУАЛЬНЫЕТЕСТ!A{next_row}:H{next_row}',
                valueInputOption='RAW',
                body={'values': values}
            ).execute()

            # Сразу записываем статус "Ожидается решение"
            self.service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'АКТУАЛЬНЫЕТЕСТ!I{next_row}',
                valueInputOption='RAW',
                body={'values': [["Ожидается решение"]]}
            ).execute()

            # Создаем embed с данными
            embed = disnake.Embed(
                title="Новый боец",
                color=disnake.Color.green()
            )
            embed.add_field(name="Позывной", value=callsign, inline=False)
            embed.add_field(name="Номер", value=number, inline=False)
            embed.add_field(name="Звание", value=rank, inline=False)
            embed.add_field(name="Формирование", value="Regular", inline=False)
            embed.add_field(name="Специализация", value="R", inline=False)
            embed.add_field(name="Время", value=time, inline=False)
            embed.add_field(name="Дата зачисления", value=join_date, inline=False)
            embed.add_field(name="Статус", value="Активен", inline=False)

            # Отправляем сообщение и добавляем реакции
            await interaction.edit_original_response(
                content=f"<@&1334403880800358460>",
                embed=embed
            )
            message = await interaction.original_message()
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Ждем реакцию от администратора
            def check(reaction, user):
                return (
                    reaction.message.id == message.id and
                    str(reaction.emoji) in ['✅', '❌'] and
                    any(role.id == 1334403880800358460 for role in user.roles)
                )

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                status = "Одобрено" if str(reaction.emoji) == '✅' else "Отклонено"
                
                # Обновляем статус в таблице
                self.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'АКТУАЛЬНЫЕТЕСТ!I{next_row}',
                    valueInputOption='RAW',
                    body={'values': [[status]]}
                ).execute()

                # Обновляем embed
                embed.add_field(
                    name="Статус",
                    value=f"{status} - {user.display_name}",
                    inline=False
                )
                await message.edit(embed=embed)

            except asyncio.TimeoutError:
                # Если никто не отреагировал
                self.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'АКТУАЛЬНЫЕТЕСТ!I{next_row}',
                    valueInputOption='RAW',
                    body={'values': [["Ожидается решение"]]}
                ).execute()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Произошла ошибка: {str(e)}"
            )

    async def edit_field_in_table(self, interaction: disnake.ModalInteraction, field_name: str):
        try:
            # Получаем значения из формы
            callsign = interaction.text_values["current_callsign"]
            current_value = interaction.text_values["current_value"]
            new_value = interaction.text_values["new_value"]

            # Получаем данные из таблицы
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='АКТУАЛЬНЫЕТЕСТ!A:I'
            ).execute()
            values = result.get('values', [])

            # Ищем строку с нужным позывным
            row_index = None
            for i, row in enumerate(values):
                if row and row[0] == callsign:
                    row_index = i + 1  # +1 потому что индексация в таблице начинается с 1
                    break

            if row_index is None:
                await interaction.edit_original_response(
                    content="Позывной не найден в таблице!"
                )
                return

            # Определяем колонку для изменения
            column_mapping = {
                "Звание": "C",
                "Специализация": "E",
                "Формирование": "D",
                "Время": "F",
                "Номер": "B",
                "Позывной": "A"
            }

            column = column_mapping.get(field_name)
            if not column:
                await interaction.edit_original_response(
                    content="Неизвестное поле для изменения!"
                )
                return

            # Обновляем значение в таблице
            self.service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'АКТУАЛЬНЫЕТЕСТ!{column}{row_index}',
                valueInputOption='RAW',
                body={'values': [[new_value]]}
            ).execute()

            # Сразу записываем статус "Ожидается решение"
            self.service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'АКТУАЛЬНЫЕТЕСТ!J{row_index}',
                valueInputOption='RAW',
                body={'values': [["Ожидается решение"]]}
            ).execute()

            # Создаем embed с информацией об изменении
            embed = disnake.Embed(
                title="Запрос на изменение данных",
                color=disnake.Color.yellow()
            )
            embed.add_field(name="Позывной", value=callsign, inline=False)
            embed.add_field(name="Поле для изменения", value=field_name, inline=False)
            embed.add_field(name="Текущее значение", value=current_value, inline=False)
            embed.add_field(name="Новое значение", value=new_value, inline=False)

            # Отправляем сообщение и добавляем реакции
            await interaction.edit_original_response(
                content=f"<@&1334403880800358460>",
                embed=embed
            )
            message = await interaction.original_message()
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            # Ждем реакцию от администратора
            def check(reaction, user):
                return (
                    reaction.message.id == message.id and
                    str(reaction.emoji) in ['✅', '❌'] and
                    any(role.id == 1334403880800358460 for role in user.roles)
                )

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                status = "Одобрено" if str(reaction.emoji) == '✅' else "Отклонено"

                # Обновляем статус в таблице
                self.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'АКТУАЛЬНЫЕТЕСТ!J{row_index}',
                    valueInputOption='RAW',
                    body={'values': [[status]]}
                ).execute()

                # Обновляем embed
                embed.add_field(
                    name="Статус",
                    value=f"{status} - {user.display_name}",
                    inline=False
                )
                await message.edit(embed=embed)

                if str(reaction.emoji) == '❌':
                    # Если отклонено, возвращаем старое значение
                    self.service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f'АКТУАЛЬНЫЕТЕСТ!{column}{row_index}',
                        valueInputOption='RAW',
                        body={'values': [[current_value]]}
                    ).execute()

            except asyncio.TimeoutError:
                embed.add_field(
                    name="Статус",
                    value="Время ожидания истекло. Изменения отменены.",
                    inline=False
                )
                await message.edit(embed=embed)
                # Возвращаем старое значение
                self.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'АКТУАЛЬНЫЕТЕСТ!{column}{row_index}',
                    valueInputOption='RAW',
                    body={'values': [[current_value]]}
                ).execute()

        except Exception as e:
            await interaction.edit_original_response(
                content=f"Произошла ошибка: {str(e)}"
            )

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id == "new_soldier":
            await interaction.response.send_modal(NewSoldierModal())
            
        elif interaction.component.custom_id == "edit_data":
            # Создаем выпадающее меню
            select = disnake.ui.Select(
                placeholder="Выберите, что нужно изменить",
                options=[
                    disnake.SelectOption(label="Звание", value="Звание"),
                    disnake.SelectOption(label="Специализация", value="Специализация"),
                    disnake.SelectOption(label="Формирование", value="Формирование"),
                    disnake.SelectOption(label="Время", value="Время"),
                    disnake.SelectOption(label="Номер", value="Номер"),
                    disnake.SelectOption(label="Позывной", value="Позывной")
                ]
            )

            async def select_callback(select_interaction: disnake.MessageInteraction):
                field_name = select_interaction.values[0]
                await select_interaction.response.send_modal(EditDataModal(field_name))

            select.callback = select_callback
            view = disnake.ui.View(timeout=60)
            view.add_item(select)
            
            await interaction.response.send_message(
                "Что нужно изменить?",
                view=view,
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_modal_submit(self, interaction: disnake.ModalInteraction):
        if interaction.custom_id == "new_soldier_modal":
            await interaction.response.defer(ephemeral=False)
            await self.add_new_soldier(interaction)
        elif interaction.custom_id.startswith("edit_"):
            await interaction.response.defer(ephemeral=False)
            field_name = interaction.custom_id.replace("edit_", "").replace("_modal", "").title()
            await self.edit_field_in_table(interaction, field_name)

def setup(bot):
    bot.add_cog(TableButtons(bot)) 