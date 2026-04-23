from __future__ import annotations

from collections.abc import Callable

from app.db.sqlite import SQLiteDatabase


class CounterRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def next_value(self, name: str, seed_factory: Callable[[], int]) -> int:
        with self._db.transaction() as conn:
            row = conn.execute("SELECT value FROM counters WHERE name=?", (name,)).fetchone()
            if row is None:
                seed = int(seed_factory())
                conn.execute("INSERT INTO counters(name, value) VALUES(?, ?)", (name, seed))
                current = seed
            else:
                current = int(row["value"])

            new_value = current + 1
            conn.execute("UPDATE counters SET value=? WHERE name=?", (new_value, name))
            return new_value
