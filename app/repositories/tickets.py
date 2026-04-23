from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import constants
from app.db.sqlite import SQLiteDatabase
from app.domain.enums import TicketStatus, TicketType
from app.domain.models import CleanupCandidate, TicketRecord
from app.utils.time import now_ts, parse_iso_datetime_any, utcnow


def _row_to_ticket_record(row: sqlite3.Row) -> TicketRecord:
    return TicketRecord(
        ticket_id=int(row["ticket_id"]),
        ticket_name=str(row["ticket_name"] or ""),
        opener_id=int(row["opener_id"]),
        ticket_type=TicketType.from_value(str(row["ticket_type"])),
        last_channel_id=int(row["channel_id"]) if row["channel_id"] is not None else None,
        status=TicketStatus.from_value(str(row["status"])),
        created_at_utc=str(row["created_at_utc"] or ""),
        closed_at_utc=str(row["closed_at_utc"] or ""),
        reopen_until_utc=str(row["reopen_until_utc"] or ""),
    )


class TicketRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self._db = db

    def reserve_ticket(self, opener_id: int, ticket_type: TicketType) -> Optional[int]:
        try:
            with self._db.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO tickets(
                        ticket_name,
                        opener_id,
                        ticket_type,
                        channel_id,
                        status,
                        created_at_ts,
                        created_at_utc,
                        closed_at_utc,
                        reopen_until_utc
                    )
                    VALUES(NULL, ?, ?, NULL, 'reserved', ?, ?, NULL, NULL)
                    """,
                    (int(opener_id), ticket_type.value, now_ts(), utcnow().isoformat()),
                )
                ticket_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
                return int(ticket_id)
        except sqlite3.IntegrityError:
            return None

    def rollback_reserved_ticket(self, ticket_id: int) -> None:
        conn = self._db.get_connection()
        conn.execute("DELETE FROM tickets WHERE ticket_id=? AND status='reserved'", (int(ticket_id),))

    def finalize_ticket_open(self, ticket_id: int, ticket_name: str, channel_id: int) -> None:
        with self._db.transaction() as conn:
            conn.execute(
                """
                UPDATE tickets
                SET ticket_name=?, channel_id=?, status='open'
                WHERE ticket_id=? AND status='reserved'
                """,
                (ticket_name, int(channel_id), int(ticket_id)),
            )

    def mark_ticket_closed_by_channel(
        self,
        channel_id: int,
        ticket_type: TicketType,
        opener_id: int,
        closed_at_dt: datetime,
        ticket_name: Optional[str] = None,
    ) -> bool:
        del ticket_type

        closed_at_dt = closed_at_dt.astimezone(timezone.utc)
        reopen_until = closed_at_dt + timedelta(hours=constants.REOPEN_WINDOW_HOURS)

        with self._db.transaction() as conn:
            cur = conn.execute(
                """
                UPDATE tickets
                SET status='closed',
                    closed_at_utc=?,
                    reopen_until_utc=?
                WHERE channel_id=? AND status IN ('open','reserved')
                """,
                (closed_at_dt.isoformat(), reopen_until.isoformat(), int(channel_id)),
            )
            if (cur.rowcount or 0) > 0:
                return True

            if ticket_name:
                cur2 = conn.execute(
                    """
                    UPDATE tickets
                    SET status='closed',
                        closed_at_utc=?,
                        reopen_until_utc=?
                    WHERE ticket_name=? AND status IN ('open','reserved')
                    """,
                    (closed_at_dt.isoformat(), reopen_until.isoformat(), str(ticket_name)),
                )
                if (cur2.rowcount or 0) > 0:
                    return True

            if opener_id:
                cur3 = conn.execute(
                    """
                    UPDATE tickets
                    SET status='closed',
                        closed_at_utc=?,
                        reopen_until_utc=?
                    WHERE opener_id=? AND status IN ('open','reserved')
                    """,
                    (closed_at_dt.isoformat(), reopen_until.isoformat(), int(opener_id)),
                )
                if (cur3.rowcount or 0) > 0:
                    return True

        return False

    def reopen_ticket_record(
        self,
        ticket_id: int,
        channel_id: Optional[int] = None,
        ticket_name: Optional[str] = None,
    ) -> None:
        with self._db.transaction() as conn:
            if channel_id is not None and ticket_name is not None:
                conn.execute(
                    """
                    UPDATE tickets
                    SET status='open',
                        channel_id=?,
                        ticket_name=?,
                        closed_at_utc=NULL,
                        reopen_until_utc=NULL
                    WHERE ticket_id=? AND status='closed'
                    """,
                    (int(channel_id), str(ticket_name), int(ticket_id)),
                )
            else:
                conn.execute(
                    """
                    UPDATE tickets
                    SET status='open',
                        closed_at_utc=NULL,
                        reopen_until_utc=NULL
                    WHERE ticket_id=? AND status='closed'
                    """,
                    (int(ticket_id),),
                )

    def reopen_ticket_by_channel(self, channel_id: int) -> None:
        with self._db.transaction() as conn:
            conn.execute(
                """
                UPDATE tickets
                SET status='open',
                    closed_at_utc=NULL,
                    reopen_until_utc=NULL
                WHERE channel_id=? AND status='closed'
                """,
                (int(channel_id),),
            )

    def get_ticket_by_name(self, ticket_name: str) -> Optional[TicketRecord]:
        conn = self._db.get_connection()
        row = conn.execute(
            """
            SELECT ticket_id, ticket_name, opener_id, ticket_type, channel_id, status, created_at_utc, closed_at_utc, reopen_until_utc
            FROM tickets
            WHERE ticket_name=?
            ORDER BY ticket_id DESC
            LIMIT 1
            """,
            (ticket_name,),
        ).fetchone()
        return _row_to_ticket_record(row) if row else None

    def get_ticket_by_channel_id(self, channel_id: int) -> Optional[TicketRecord]:
        conn = self._db.get_connection()
        row = conn.execute(
            """
            SELECT ticket_id, ticket_name, opener_id, ticket_type, channel_id, status, created_at_utc, closed_at_utc, reopen_until_utc
            FROM tickets
            WHERE channel_id=?
            ORDER BY ticket_id DESC
            LIMIT 1
            """,
            (int(channel_id),),
        ).fetchone()
        return _row_to_ticket_record(row) if row else None

    def get_active_ticket_for_user(self, opener_id: int) -> Optional[TicketRecord]:
        conn = self._db.get_connection()
        row = conn.execute(
            """
            SELECT ticket_id, ticket_name, opener_id, ticket_type, channel_id, status, created_at_utc, closed_at_utc, reopen_until_utc
            FROM tickets
            WHERE opener_id=? AND status IN ('reserved','open')
            ORDER BY ticket_id DESC
            LIMIT 1
            """,
            (int(opener_id),),
        ).fetchone()
        return _row_to_ticket_record(row) if row else None

    def list_reopenable_closed_tickets(self) -> list[str]:
        conn = self._db.get_connection()
        rows = conn.execute(
            """
            SELECT ticket_name, reopen_until_utc
            FROM tickets
            WHERE status='closed'
              AND reopen_until_utc IS NOT NULL
              AND reopen_until_utc <> ''
              AND ticket_name IS NOT NULL
              AND ticket_name <> ''
            """
        ).fetchall()

        now = utcnow()
        output: list[str] = []
        for row in rows:
            until = parse_iso_datetime_any(str(row["reopen_until_utc"] or ""))
            if until and now <= until:
                output.append(str(row["ticket_name"]))
        return output

    def get_latest_reopenable_ticket_for_user(
        self,
        opener_id: int,
        preferred_ticket_name: Optional[str] = None,
    ) -> Optional[TicketRecord]:
        conn = self._db.get_connection()
        now = utcnow()

        if preferred_ticket_name:
            row = conn.execute(
                """
                SELECT ticket_id, ticket_name, opener_id, ticket_type, channel_id, status, created_at_utc, closed_at_utc, reopen_until_utc
                FROM tickets
                WHERE opener_id=? AND status='closed' AND ticket_name=?
                ORDER BY ticket_id DESC
                LIMIT 1
                """,
                (int(opener_id), preferred_ticket_name),
            ).fetchone()
            if row:
                until = parse_iso_datetime_any(str(row["reopen_until_utc"] or ""))
                if until and now <= until:
                    return _row_to_ticket_record(row)

        rows = conn.execute(
            """
            SELECT ticket_id, ticket_name, opener_id, ticket_type, channel_id, status, created_at_utc, closed_at_utc, reopen_until_utc
            FROM tickets
            WHERE opener_id=? AND status='closed'
            ORDER BY ticket_id DESC
            """,
            (int(opener_id),),
        ).fetchall()

        for row in rows:
            until = parse_iso_datetime_any(str(row["reopen_until_utc"] or ""))
            if until and now <= until:
                return _row_to_ticket_record(row)
        return None

    def list_active_cleanup_candidates(self) -> list[CleanupCandidate]:
        conn = self._db.get_connection()
        rows = conn.execute(
            """
            SELECT ticket_id, status, channel_id, created_at_ts
            FROM tickets
            WHERE status IN ('reserved','open')
            """
        ).fetchall()
        return [
            CleanupCandidate(
                ticket_id=int(row["ticket_id"]),
                status=TicketStatus.from_value(str(row["status"])),
                channel_id=int(row["channel_id"]) if row["channel_id"] is not None else None,
                created_at_ts=float(row["created_at_ts"] or 0),
            )
            for row in rows
        ]

    def delete_ticket_if_status(self, ticket_id: int, status: TicketStatus) -> None:
        conn = self._db.get_connection()
        conn.execute(
            "DELETE FROM tickets WHERE ticket_id=? AND status=?",
            (int(ticket_id), status.value),
        )
