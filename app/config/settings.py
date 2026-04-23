from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.config import constants


@dataclass(slots=True, frozen=True)
class Settings:
    discord_token: str
    db_path: Path
    log_level: str
    google_credentials_file: Path

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        discord_token = (os.getenv("DISCORD_TOKEN") or "").strip()
        if not discord_token:
            raise RuntimeError("DISCORD_TOKEN пуст. Задай токен в переменную окружения DISCORD_TOKEN.")

        db_path = Path((os.getenv("DB_PATH") or "tickets.db").strip() or "tickets.db")
        log_level = (os.getenv("LOG_LEVEL") or "INFO").strip().upper() or "INFO"
        google_credentials_file = Path(
            (os.getenv("GOOGLE_CREDENTIALS_FILE") or constants.DEFAULT_CREDENTIALS_FILE).strip()
            or constants.DEFAULT_CREDENTIALS_FILE
        )

        return cls(
            discord_token=discord_token,
            db_path=db_path,
            log_level=log_level,
            google_credentials_file=google_credentials_file,
        )
