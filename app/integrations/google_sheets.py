from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from app.config import constants


class GoogleSheetsClient:
    def __init__(self, credentials_file: Path, logger: logging.Logger) -> None:
        self._credentials_file = Path(credentials_file)
        self._logger = logger
        self._client: gspread.Client | None = None
        self._sheet: gspread.Worksheet | None = None

    @property
    def is_ready(self) -> bool:
        return self._sheet is not None

    def initialize(self) -> None:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                str(self._credentials_file),
                constants.GOOGLE_SCOPES,
            )
            self._client = gspread.authorize(creds)
            self._sheet = self._client.open(constants.GOOGLE_SHEET_NAME).sheet1
            self._logger.info("Google Sheets подключен: %s", constants.GOOGLE_SHEET_NAME)
        except Exception as exc:
            self._client = None
            self._sheet = None
            self._logger.warning("Google Sheets НЕ подключен: %s", exc)

    def get_all_records(self) -> list[dict[str, Any]]:
        if self._sheet is None:
            return []
        return self._sheet.get_all_records()
