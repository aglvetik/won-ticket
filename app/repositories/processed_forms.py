from __future__ import annotations

from app.db.sqlite import SQLiteDatabase
from app.utils.time import utcnow


class ProcessedFormsRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def is_row_processed(self, sheet_row_index: int) -> bool:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT sheet_row FROM processed_forms WHERE sheet_row=?",
            (int(sheet_row_index),),
        ).fetchone()
        return bool(row)

    def mark_row_processed(self, sheet_row_index: int) -> None:
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_forms(sheet_row, processed_at_utc) VALUES(?, ?)",
                (int(sheet_row_index), utcnow().isoformat()),
            )

    def is_signature_processed(self, signature: str) -> bool:
        conn = self._db.get_connection()
        row = conn.execute(
            "SELECT signature FROM processed_form_signatures WHERE signature=?",
            (signature,),
        ).fetchone()
        return bool(row)

    def mark_signature_processed(self, signature: str) -> None:
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_form_signatures(signature, processed_at_utc) VALUES(?, ?)",
                (signature, utcnow().isoformat()),
            )
