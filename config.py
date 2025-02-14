# Токен бота
BOT_TOKEN = ""
TEST_GUILDS = [1334403880590770176]

# ID каналов
CHANNELS = {
    'WELCOME': 1334403881345744928,
    'LOG': 1334528486521573446,
    'COMBAT_REPORTS': 1334403882872475707,    # Боевые вылеты
    'TRAINING_REPORTS': 1334403883455221784,  # Тренировки
    'HOLIDAY_REPORTS': 1334403883455221783,   # Отпуска
    'RANK_REPORTS': 1334403883455221780,      # Повышения/понижения
    'REPRIMAND_REPORTS': 1334403883455221781, # Выговоры
    'ATTESTATION_REPORTS': 1334403883455221782, # Аттестации
    'RECOMMENDATION_REPORTS': 1339213240814801028,  # Рекомендации
}

# Для обратной совместимости
LOG_CHANNEL_ID = CHANNELS['LOG']
WELCOME_CHANNEL_ID = CHANNELS['WELCOME']

# ID ролей
ROLES = {
    'ADMIN': 1334403880800358460,
    'MUTE': 1334845457217748992,
    'DEFAULT': [
        1334403880800358463,
        1334403880800358458,
        1334403880800358456,
        1334403880745959449,
        1334403880640974899,
        1334403880640974890,
        1334403880590770182,
        1334403880590770181
    ],
    'WARNINGS': {
        'FIRST': [1334403880590770185],
        'SECOND': [1334403880590770184],
        'THIRD': [1334403880590770183]
    },
    'COMMAND': [
        1334403880850559020, #-----Командование----
        1334403880850559019, # КМД Корпуса
        1334403880850559018, # Зам КМД Корпуса
        1334403880800358464  # Командир отряда
    ],
    'POSITIONS': [
        1334403880800358463, # -----Должность-----
        1334403880800358462, # Главный инструктор
        1334403880800358461, # Инструтоктор
        1334403880800358460, # Ответсвенный за таблицу
        1334403880800358459  # Верховное командование
    ],
    'SPECIAL': [
        1334403880800358458, # -----Спец.Отряд-----
        1334403880800358457  # DeathWatch
    ],
    'COMPOSITION': [
        1334403880800358456, # -----Состав-----
        1334403880800358455, # Джедай
        1334403880745959454, # Основной состав
        1334403880745959453, # Ст. Офицерский состав
        1334403880745959452, # Мл. Офицерский состав
        1334403880745959451, # Сержансткий состав
        1334403880745959450  # Рядовой состав
    ],
    'RANKS': [
        1334403880745959449, # -----Звание-----
        1334403880745959448, # CT
        1334403880745959447, # PVT
        1334403880745959446, # PFC
        1334403880745959445, # CS
        1334403880686981139, # CPL
        1334403880686981138, # SGT
        1334403880686981137, # SSG
        1334403880686981136, # SGM
        1334403880686981135, # LT
        1334403880686981134, # SLT
        1334403880686981133, # SPLT
        1334403880686981132, # CPT
        1334403880686981131, # MAJ
        1334403880686981130  # COM
    ],
    'SPECIALIZATIONS': [
        1334403880640974899, # -----Специализации-----
        1334403880640974898, # ARC
        1334403880640974897, # ARF
        1334403880640974896, # Marksman
        1334403880640974895, # Medic
        1334403880640974894, # Diversonist
        1334403880640974893, # Heavy Trooper
        1334403880640974892, # Rifleman
        1334403880640974891  # Pilot
    ],
    'PUNISHMENT': [
        1334403880640974890, # -----Наказание-----
        1334403880590770185, # Слабый шапакляк
        1334403880590770184, # Средний шапакляк
        1334403880590770183  # Сильный шапакляк
    ],
    'OTHER': [
        1334403880590770182, # -----Медали-----
        1334403880590770181, # -----Другое-----
        1334403880590770179, # Админ проекта
        1334403880590770178, # Гость
        1334403880590770177  # Тех.Админ
    ]
}

# Для обратной совместимости
ROLE_MUTE_ID = ROLES['MUTE']
DEFAULT_ROLES_IDS = ROLES['DEFAULT']
FIRST_WARNING_ROLE_ID = ROLES['WARNINGS']['FIRST']
SECOND_WARNING_ROLE_ID = ROLES['WARNINGS']['SECOND']
THIRD_WARNING_ROLE_ID = ROLES['WARNINGS']['THIRD']

# Все роли в одном списке для проверок
ALL_ROLE_IDS = (
    ROLES['COMMAND'] +
    ROLES['POSITIONS'] +
    ROLES['SPECIAL'] +
    ROLES['COMPOSITION'] +
    ROLES['RANKS'] +
    ROLES['SPECIALIZATIONS'] +
    ROLES['PUNISHMENT'] +
    ROLES['OTHER']
)

# Настройки для отчетов
CHANNEL_TO_REPORT = {
    CHANNELS['COMBAT_REPORTS']: 'COMBAT',
    CHANNELS['TRAINING_REPORTS']: 'TRAINING',
    CHANNELS['HOLIDAY_REPORTS']: 'HOLIDAY',
    CHANNELS['RANK_REPORTS']: 'RANK',
    CHANNELS['ATTESTATION_REPORTS']: 'ATTESTATION',
    CHANNELS['RECOMMENDATION_REPORTS']: 'RECOMMENDATION',
    CHANNELS['REPRIMAND_REPORTS']: 'REPRIMAND'
}

REPORTS = {
    'COMBAT': {
        'label': "⚔️ Отправить отчет",
        'custom_id': "report_combat_button",
        'command': "report_op",
        'title': "Боевой вылет",
        'description': "Нажмите на кнопку, чтобы отправить отчет о боевом вылете"
    },
    'TRAINING': {
        'label': "🎯 Отправить отчет",
        'custom_id': "report_training_button",
        'command': "report_training",
        'title': "Тренировка/Симуляция",
        'description': "Нажмите на кнопку, чтобы отправить отчет о тренировке/симуляции"
    },
    'HOLIDAY': {
        'label': "🏖️ Запросить отпуск",
        'custom_id': "report_holiday_button",
        'command': "report_holiday",
        'title': "Отпуск",
        'description': "Нажмите на кнопку, чтобы отправить запрос на отпуск"
    },
    'RANK': {
        'label': "⭐ Отчет повышение/понижение",
        'custom_id': "report_rank_button",
        'command': "report_rank",
        'title': "Повышение/понижение",
        'description': "Нажмите на кнопку, чтобы отправить запрос на повышение/понижение"
    },
    'ATTESTATION': {
        'label': "📋 Отправить отчет об аттестации",
        'custom_id': "report_attestation_button",
        'command': "report_attestation",
        'title': "Аттестация",
        'description': "Нажмите на кнопку, чтобы отправить отчет об аттестации"
    },
    'RECOMMENDATION': {
        'label': "👍 Отправить рекомендацию",
        'custom_id': "report_recommendation_button",
        'command': "report_recommendation",
        'title': "Рекомендация",
        'description': "Нажмите на кнопку, чтобы отправить рекомендацию"
    },
    'REPRIMAND': {
        'label': "⚠️ Отправить выговор",
        'custom_id': "report_reprimand_button",
        'command': "report_reprimand",
        'title': "Выговор",
        'description': "Нажмите на кнопку, чтобы отправить выговор"
    }
}

# Настройки для аттестации
ATTESTATION_TYPES = {
    "JetPack/JumpPack": "jetpack",
    "КПБ": "kpb",
    "Финальная аттестация": "final",
    "Специализация": "spec",
    "Работа с гражданскими": "civil",
    "Работа в густонаселенных городах": "city",
    "Звание": "rank"
}

KPB_OPTIONS = [str(i) for i in range(1, 18)]
SPEC_OPTIONS = ["HT", "S", "D", "P", "M", "ENG", "ARF", "BC"]
RANK_OPTIONS = ["PVT", "PFC", "CS", "CPL", "SGT", "SSG", "SGM", "LT", "SLT", "SPLT", "CPT"]

# Google Sheets настройки
SPREADSHEET_ID = '10bUeIRVHd-0IgOyiSWp4UWoi1_RPP2LwoJCiL7e_t2I'
SHEETS = {
    'COMBAT': {'name': 'Боевой вылет', 'id': '1214628575', 'sheet_index': 1},
    'HOLIDAY': {'name': 'Мороз', 'id': '1204643197', 'sheet_index': 2},
    'TRAINING': {'name': 'Треня', 'id': '13767602', 'sheet_index': 3},
    'RANK': {'name': 'Ранг', 'id': '1603232079', 'sheet_index': 4},
    'ATTESTATION': {'name': 'Аттестация', 'id': '2038404776', 'sheet_index': 5},
    'RECOMMENDATION': {'name': 'Рекомендация', 'id': '1628475350', 'sheet_index': 6},
    'REPRIMAND': {'name': 'Выговор', 'id': '1600519154', 'sheet_index': 7}
}

# Запрещенные слова
CENSORED_WORDS = ["маму ебал"]