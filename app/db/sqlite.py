from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.db.schema import ensure_schema


class SQLiteDatabase:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._local = threading.local()

    @property
    def path(self) -> Path:
        return self._path

    def get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            if self._path.parent and not self._path.parent.exists():
                self._path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self._path, isolation_level=None, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            self._local.conn = conn
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def initialize(self) -> None:
        ensure_schema(self.get_connection())
