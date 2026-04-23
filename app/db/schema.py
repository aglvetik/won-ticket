from __future__ import annotations

import sqlite3


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_name TEXT,
            opener_id INTEGER NOT NULL,
            ticket_type TEXT NOT NULL,
            channel_id INTEGER,
            status TEXT NOT NULL,
            created_at_ts REAL NOT NULL,
            created_at_utc TEXT NOT NULL,
            closed_at_utc TEXT,
            reopen_until_utc TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_ticket_per_user
        ON tickets(opener_id)
        WHERE status IN ('reserved', 'open')
        """
    )

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_channel_id_unique
        ON tickets(channel_id)
        WHERE channel_id IS NOT NULL
        """
    )

    conn.execute("CREATE INDEX IF NOT EXISTS ix_tickets_status ON tickets(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_tickets_created_ts ON tickets(created_at_ts)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_tickets_opener ON tickets(opener_id)")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_forms (
            sheet_row INTEGER PRIMARY KEY,
            processed_at_utc TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_form_signatures (
            signature TEXT PRIMARY KEY,
            processed_at_utc TEXT NOT NULL
        )
        """
    )
