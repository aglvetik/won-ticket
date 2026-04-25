# WON Ticket Bot

Кастомный тикет-бот для Discord, написан под клан WON (Squad).

Основной упор — заявки в клан: создание тикета → заполнение анкеты → принятие/отклонение → выдача ролей и изменение ника.

## Возможности

- Система тикетов (application / idea / other)
- Один активный тикет на пользователя
- Автоматическая нумерация

### Заявки в клан

- Интеграция с Google Forms
- Отправка анкеты в Discord
- Кнопки принятия / отклонения

Команды:
- !accept / !принять
- !reject / !отклонить

При принятии:
- Выдача ролей
- Снятие роли гостя
- Добавление тега к нику

- Переоткрытие тикетов (до 5 часов)
- Приватные каналы заметок для персонала
- Автосохранение транскриптов при удалении тикета

### Google Sheets

- Защита от дублей
- Обработка заявок

### База данных

- SQLite (WAL)
- Статусы: reserved / open / closed

### Сохранено без изменений

- Все ID
- Роли
- Кнопки (custom_id)
- Тексты
- Логика работы
## Project Tree

```text
.
├── .env.example
├── README.md
├── app
│   ├── __init__.py
│   ├── bootstrap.py
│   ├── main.py
│   ├── config
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   └── settings.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   └── sqlite.py
│   ├── discord_app
│   │   ├── __init__.py
│   │   ├── bot.py
│   │   ├── container.py
│   │   ├── commands
│   │   │   ├── __init__.py
│   │   │   ├── moderation.py
│   │   │   └── panel.py
│   │   ├── handlers
│   │   │   ├── __init__.py
│   │   │   ├── errors.py
│   │   │   └── lifecycle.py
│   │   └── views
│   │       ├── __init__.py
│   │       ├── after_close.py
│   │       ├── application_decision.py
│   │       ├── close.py
│   │       ├── notes.py
│   │       ├── panel.py
│   │       └── reopen_dm.py
│   ├── domain
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   └── models.py
│   ├── integrations
│   │   ├── __init__.py
│   │   ├── google_sheets.py
│   │   └── transcript_exporter.py
│   ├── repositories
│   │   ├── __init__.py
│   │   ├── counters.py
│   │   ├── processed_forms.py
│   │   └── tickets.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── cleanup_service.py
│   │   ├── google_forms_service.py
│   │   ├── logging_service.py
│   │   ├── member_service.py
│   │   ├── panel_service.py
│   │   ├── reopen_service.py
│   │   ├── ticket_service.py
│   │   └── transcript_service.py
│   └── utils
│       ├── __init__.py
│       ├── discord_utils.py
│       ├── hashing.py
│       ├── text.py
│       └── time.py
├── requirements.txt
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── fakes.py
│   ├── test_accept_flow.py
│   ├── test_cleanup.py
│   ├── test_form_signature.py
│   ├── test_numbering.py
│   ├── test_reopen_window.py
│   └── test_repositories.py
├── ticket.py
└── won-ticketbot.service
```
