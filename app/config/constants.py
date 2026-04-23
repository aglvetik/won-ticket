from __future__ import annotations

from typing import Final

GUILD_ID: Final = 1299219026517426256
LOG_CHANNEL_ID: Final = 1473832784085651576

TRANSCRIPT_CHANNEL_ID_APPLICATION: Final = 1474443506834735352
TRANSCRIPT_CHANNEL_ID_OTHER: Final = 1478006269217603685
TRANSCRIPT_CHANNEL_ID_IDEA: Final = 1478006230743253054

OPEN_CATEGORY_ID: Final = 1453150638207664218
CLOSED_CATEGORY_ID: Final = 1473832608315211888
TICKET_PANEL_CHANNEL_ID: Final = 1473841177248792829
SUPPORT_ROLE_ID: Final = 1473833178727977152

APPLICATION_ROLES: Final[list[int]] = [1473833178727977152]
OTHER_ROLES: Final[list[int]] = [1473833178727977152]
IDEA_ROLES: Final[list[int]] = [1473833178727977152]

ALLOWED_ROLES: Final[list[int]] = [1473833178727977152]
ALLOWED_CHANNEL_ID: Final = TICKET_PANEL_CHANNEL_ID

APPLICATION_MOD_ROLE_ID: Final = 1341827898809782364
GUEST_ROLE_ID: Final = 1300256509279866975
ACCEPT_ROLES_IDS: Final[list[int]] = [1341561712930983989, 1425134554238419177]
CLAN_TAG: Final = "[rWON]"
GOOGLE_FORM_URL: Final = (
    "https://docs.google.com/forms/d/e/1FAIpQLSd4Wd3DNlDVldPQp2yNzAmhmuH7tF7B9WBEbV_f6gyVa_XiXA/viewform"
)
APPLICATION_ADMIN_CHANNEL_ID: Final = 1478099343662911640
START_FROM_ROW: Final = 145
GS_POLL_SECONDS: Final = 30
GOOGLE_SHEET_NAME: Final = "опросник для  WON (Ответы)"
DEFAULT_CREDENTIALS_FILE: Final = "credentials.json"

GOOGLE_SCOPES: Final[list[str]] = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

TICKET_NAME_PREFIX: Final[dict[str, str]] = {
    "application": "🧾 join-заявка",
    "idea": "💡 idea-креатив",
    "other": "🆘 help-помогите",
}

TICKET_TOPIC_TITLE: Final[dict[str, str]] = {
    "application": "🧾 join-заявка",
    "idea": "💡 idea-креатив",
    "other": "🆘 help-помогите",
}

TICKET_FIRST_NUMBER: Final[dict[str, int]] = {
    "application": 246,
    "other": 38,
    "idea": 0,
}

TICKET_NUMBER_PAD: Final[dict[str, int]] = {
    "other": 4,
}

MAIN_PANEL_APPLY_LABEL: Final = "📩 Подать заявку на вступление"
MAIN_PANEL_APPLY_CUSTOM_ID: Final = "panel_apply"
MAIN_PANEL_QUESTION_LABEL: Final = "🚨 Подать жалобу на игрока"
MAIN_PANEL_QUESTION_CUSTOM_ID: Final = "panel_question"
MAIN_PANEL_IDEA_LABEL: Final = "💡 Предложить идею"
MAIN_PANEL_IDEA_CUSTOM_ID: Final = "panel_idea"

TICKET_CLOSE_LABEL: Final = "🔒 Закрыть тикет"
TICKET_CLOSE_CUSTOM_ID: Final = "ticket_close"
TICKET_STAFF_NOTES_LABEL: Final = "📝 Заметки персонала"
TICKET_STAFF_NOTES_CUSTOM_ID: Final = "ticket_staff_notes"

TICKET_CLOSE_CONFIRM_LABEL: Final = "Да, закрыть"
TICKET_CLOSE_CONFIRM_CUSTOM_ID: Final = "ticket_close_confirm"
TICKET_CLOSE_CANCEL_LABEL: Final = "Отмена"
TICKET_CLOSE_CANCEL_CUSTOM_ID: Final = "ticket_close_cancel"

TICKET_DELETE_LABEL: Final = "🗑️ Удалить тикет"
TICKET_DELETE_CUSTOM_ID: Final = "ticket_delete"
TICKET_REOPEN_MOD_LABEL: Final = "🔓 Переоткрыть тикет"
TICKET_REOPEN_MOD_CUSTOM_ID: Final = "ticket_reopen_mod"

DM_REOPEN_LABEL: Final = "🔓 Переоткрыть тикет"
DM_REOPEN_CUSTOM_ID: Final = "dm_reopen_generic"

NOTES_DELETE_LABEL: Final = "🗑 Удалить заметки"
NOTES_DELETE_CUSTOM_ID: Final = "notes_delete"

APP_DECISION_ACCEPT_LABEL: Final = "✅ Принять игрока"
APP_DECISION_ACCEPT_CUSTOM_ID: Final = "app_decision_accept"
APP_DECISION_REJECT_LABEL: Final = "❌ Отклонить игрока"
APP_DECISION_REJECT_CUSTOM_ID: Final = "app_decision_reject"

PANEL_EMBED_TITLE: Final = "⚔️ **WON** ⚔️ | Центр поддержки"
PANEL_EMBED_DESCRIPTION: Final = (
    "📩 **Заявка** — Хочу вступить в клан\n\n"
    "🚨 **Жалоба** — Подать жалобу на игрока\n\n"
    "💡 **Идеи** — Есть предложение"
)

PANEL_COMMAND_EMBED_TITLE: Final = "Система заявок"
PANEL_COMMAND_EMBED_DESCRIPTION: Final = "Выберите нужный вариант ниже."

APPLICATION_FORM_MESSAGE_TEMPLATE: Final = (
    "## Приветствую, {opener_mention}!\n"
    "### Чтобы вступить, заполни короткую анкету по ссылке:\n"
    "### {google_form_url}\n"
    "## Как заполнишь — напиши сюда"
)

ACCEPT_TEXT_1: Final = """## Отлично,вы приняты

## - 1. Добавление тега в игре
В меню Игры [Настройки] → [Игра] → [Префикс имени игрока] и добавьте тег **[rWON]**
Если возникнут проблемы, вот подробная инструкция:
→ [Перейти к руководству](https://discord.com/channels/1299219026517426256/1358286626865807471)

## - 2. Ознакомление с правилами и информацией клана
Обязательно изучите канал #clan-info:
→ [Перейти в #clan-info](https://discord.com/channels/1299219026517426256/1341845834844606464)

## - 3. Рекомендуемые каналы для ознакомления
•  *Полезная информация по игре*: [Перейти](https://discord.com/channels/1299219026517426256/1341845710638944409)
•  *Выбор ролей*: [Перейти](https://discord.com/channels/1299219026517426256/1364202376080130080)
•  *Правила клана*: [Перейти](https://discord.com/channels/1299219026517426256/1341845834844606464)
•  *Активные новости клана*: [Перейти](https://discord.com/channels/1299219026517426256/1447248895104258248)
•  *Запрос* ClanVIP: [Перейти](https://discord.com/channels/1299219026517426256/1429515476349878413)
•  *Игровая Статистика*: [Перейти](https://discord.com/channels/1299219026517426256/1447255644959936593)
•  *Канал Где можно предложить свою идею*: [Перейти](https://discord.com/channels/1299219026517426256/1343221022572286094)
•  *Канал Отпуск*: [Перейти](https://discord.com/channels/1299219026517426256/1403212258099724369)
•  *Новости клана*: [Перейти](https://discord.com/channels/1299219026517426256/1341807950154432635)
•  *Канал с игровыми инвентами*: [Перейти](https://discord.com/channels/1299219026517426256/1341845992428929227)
"""

ACCEPT_TEXT_2: Final = """### Когда всё будет понятно и вы будете готовы — просто закройте тикет в любое удобное время.
### Если появятся вопросы — пишите без стеснения.
### Добро пожаловать в [WON]!
"""

DENY_TEXT: Final = """## Спасибо за заявку! К сожалению, сейчас мы не готовы принять вас в клан.

Это не значит “навсегда”: вы можете подать заявку позже.
Если хотите — напишите пару слов о вашем опыте и стиле игры, и мы подскажем, что улучшить.
"""

ACCESS_DENIED_TEXT: Final = "Нехуй тебе туда лезть!"

REOPEN_WINDOW_HOURS: Final = 5
CLEANUP_INTERVAL_MINUTES: Final = 10
CLEANUP_TTL_SECONDS: Final = 600
