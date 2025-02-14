import disnake
from disnake.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
from config import SPREADSHEET_ID

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = './credentials/cc-5052-bly-e24abd47118d.json'

class PersonalFile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_user_data(self, username):
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Battalion Roster!C2:K100',
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            values = result.get('values', [])
            
            # Извлекаем позывной из полного формата имени
            username_parts = username.split()
            callsign_to_find = username_parts[-1]
            print(f"[DEBUG] Ищем позывной: {callsign_to_find}")
            
            user_data = None
            for row in values:
                if len(row) < 3:
                    continue
                    
                # Очищаем позывной от квадратных скобок и получаем только имя
                full_callsign = row[0].replace('[', '').replace(']', '')
                callsign = full_callsign.split()[-1]
                
                if callsign == callsign_to_find:
                    # Парсим специализацию
                    spec_info = row[0].split('|')
                    spec = 'R'  # По умолчанию Rifleman
                    unit = None
                    
                    if len(spec_info) > 1:
                        spec_raw = spec_info[1].strip()
                        if spec_raw == 'STF':
                            spec = 'Спец. отряд'
                            unit = row[3] if len(row) > 3 else 'Не указан'
                        else:
                            spec = spec_raw
                    else:
                        # Если нет | в позывном, проверяем специализацию в отдельном столбце
                        spec = row[4] if len(row) > 4 and row[4] else 'R'
                    
                    user_data = {
                        'callsign': callsign,
                        'rank': row[2],      # Звание в столбце E
                        'number': row[1],    # Номер в столбце D
                        'spec': spec,        # Специализация из парсинга или столбца
                        'unit': unit,        # Отряд (если есть)
                        'join_date': row[8] if len(row) > 8 else 'Не указана'  # Дата зачисления в столбце K
                    }
                    break
            
            print(f"[DEBUG] Поиск пользователя {username}")
            print(f"[DEBUG] Найденные данные: {user_data}")
            print(f"[DEBUG] Всего строк в таблице: {len(values)}")
            
            return user_data
        except Exception as e:
            print(f"Ошибка при получении данных: {str(e)}")
            return None

    def get_activity_stats(self, username):
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Battalion Roster!C2:T100',
                valueRenderOption='FORMATTED_VALUE'
            ).execute()
            values = result.get('values', [])
            
            # Извлекаем позывной для поиска
            username_parts = username.split()
            callsign_to_find = username_parts[-1]
            
            stats = None
            for row in values:
                if len(row) < 3:
                    continue
                    
                # Очищаем позывной от квадратных скобок и получаем только имя
                full_callsign = row[0].replace('[', '').replace(']', '')
                callsign = full_callsign.split()[-1]
                
                if callsign == callsign_to_find:
                    stats = {
                        'combat_missions': row[12] if len(row) > 12 else '0',    # Столбец O - Боевые вылеты
                        'commands': row[13] if len(row) > 13 else '0',           # Столбец P - Командование
                        'reports': row[14] if len(row) > 14 else '0',            # Столбец Q - Доклады
                        'activities_led': row[15] if len(row) > 15 else '0',     # Столбец R - Проведенные активности
                        'activities': row[16] if len(row) > 16 else '0',         # Столбец S - Участие в активностях
                        'recommendations': row[17] if len(row) > 17 else '0'     # Столбец T - Рекомендации
                    }
                    break
            
            return stats
        except Exception as e:
            print(f"Ошибка при получении статистики: {str(e)}")
            return None

    def calculate_days_in_service(self, join_date):
        try:
            date_obj = datetime.strptime(join_date, '%d.%m.%Y')
            days = (datetime.now() - date_obj).days
            return days
        except:
            return 0

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id == "personal_file":
            # Отвечаем на взаимодействие сразу, чтобы кнопка не "зависала"
            await interaction.response.defer(ephemeral=True)
            
            if interaction.channel.id != 1339829150113992745:
                await interaction.edit_original_response(
                    content="Эта кнопка работает только в канале личных дел!"
                )
                return

            username = interaction.user.display_name
            user_data = self.get_user_data(username)
            
            if not user_data:
                await interaction.edit_original_response(
                    content="Не удалось найти ваши данные в таблице."
                )
                return
            
            stats = self.get_activity_stats(username)
            days_in_service = self.calculate_days_in_service(user_data['join_date'])
            
            embed = disnake.Embed(
                title=f"Личное дело: {username}",
                color=disnake.Color.blue()
            )
            
            # Основная информация
            embed.add_field(name="Номер", value=user_data['number'], inline=True)
            embed.add_field(name="Звание", value=user_data['rank'], inline=True)
            if user_data['unit']:  # Если есть отряд
                embed.add_field(name="Отряд", value=user_data['unit'], inline=True)
            embed.add_field(name="Специализация", value=user_data['spec'], inline=True)
            embed.add_field(name="Дата зачисления", value=user_data['join_date'], inline=True)
            embed.add_field(name="Дней в строю", value=str(days_in_service), inline=True)
            
            # Статистика
            if stats:
                embed.add_field(
                    name="Статистика",
                    value=f"Боевых вылетов: {stats['combat_missions']}\n"
                          f"Командование: {stats['commands']}\n"
                          f"Проведено активностей: {stats['activities_led']}\n"
                          f"Участие в активностях: {stats['activities']}\n"
                          f"Докладов: {stats['reports']}\n"
                          f"Рекомендаций: {stats['recommendations']}",
                    inline=False
                )
            
            # Отправляем сообщение с личным делом под кнопкой
            await interaction.channel.send(
                embed=embed,
                delete_after=600  # 600 секунд = 10 минут
            )
            
            # Скрываем сообщение о том, что кнопка нажата
            await interaction.edit_original_response(content="Личное дело отправлено!")

def setup(bot):
    bot.add_cog(PersonalFile(bot))
