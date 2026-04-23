# WON Ticket Bot

Полный модульный rebuild Discord ticket bot с сохранением поведения старого `ticket.py`.

Что сохранено:

- SQLite c `WAL`, `busy_timeout`, `reserved | open | closed` семантикой и уникальным активным тикетом на пользователя.
- Prefix-команды `!accept`, `!принять`, `!reject`, `!отклонить`.
- Все Discord ID, роли, категории, custom_id кнопок, тексты, numbering rules, reopen flow, transcript flow и Google Sheets flow.
- Google Sheets авторизация через файл `credentials.json` по умолчанию.
- Единственное бизнес-изменение: Google Forms polling пропускает строки до `145` включительно и начинает обработку с `146`.

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

`ticket.py` оставлен как исходный reference-файл старой реализации.

## Configuration

Скопируйте `.env.example` в `.env` и заполните:

```env
DISCORD_TOKEN=your_discord_bot_token
DB_PATH=tickets.db
LOG_LEVEL=INFO
GOOGLE_CREDENTIALS_FILE=credentials.json
```

Примечания:

- `GOOGLE_CREDENTIALS_FILE` по умолчанию указывает на `credentials.json`.
- Можно указать абсолютный путь до файла сервисного аккаунта Google.
- Если `DB_PATH` относительный, он считается относительно `WorkingDirectory`.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

## Tests

```bash
pytest -q
```

Покрыты:

- numbering seed/scan logic
- SQLite repository semantics
- form signature dedup
- cleanup semantics
- reopen window
- accept-role/nickname flow

## Deploy On Ubuntu/Debian

Пример production-раскладки:

```bash
sudo useradd --system --home /opt/won-ticketbot --shell /usr/sbin/nologin wonbot
sudo mkdir -p /opt/won-ticketbot
sudo chown -R wonbot:wonbot /opt/won-ticketbot
```

Далее:

```bash
sudo -u wonbot python3 -m venv /opt/won-ticketbot/.venv
sudo -u wonbot /opt/won-ticketbot/.venv/bin/pip install -r /opt/won-ticketbot/requirements.txt
sudo -u wonbot cp /opt/won-ticketbot/.env.example /opt/won-ticketbot/.env
```

Положите `credentials.json` в `/opt/won-ticketbot/` или пропишите абсолютный путь в `.env`.

Установка сервиса:

```bash
sudo cp won-ticketbot.service /etc/systemd/system/won-ticketbot.service
sudo systemctl daemon-reload
sudo systemctl enable won-ticketbot
sudo systemctl start won-ticketbot
sudo systemctl status won-ticketbot
```

## Service Notes

- `EnvironmentFile` читается из `/opt/won-ticketbot/.env`
- бот стартует через `/opt/won-ticketbot/.venv/bin/python -m app.main`
- рабочая директория сервиса: `/opt/won-ticketbot`
- при падении сервис автоматически перезапускается
