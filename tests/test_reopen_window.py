from __future__ import annotations

from datetime import timedelta

from app.domain.enums import TicketType
from app.utils.time import parse_iso_datetime_any, utcnow


def test_reopen_window_is_five_hours_from_close(ticket_repository, db) -> None:
    ticket_id = ticket_repository.reserve_ticket(4001, TicketType.APPLICATION)
    assert ticket_id is not None

    ticket_repository.finalize_ticket_open(ticket_id, "join-заявка-246", 777)
    closed_at = utcnow()
    ticket_repository.mark_ticket_closed_by_channel(777, TicketType.APPLICATION, 4001, closed_at, ticket_name="join-заявка-246")

    record = ticket_repository.get_latest_reopenable_ticket_for_user(4001)

    assert record is not None
    reopen_until = parse_iso_datetime_any(record.reopen_until_utc)
    assert reopen_until is not None
    assert reopen_until == closed_at + timedelta(hours=5)

    conn = db.get_connection()
    conn.execute(
        "UPDATE tickets SET reopen_until_utc=? WHERE ticket_id=?",
        ((utcnow() - timedelta(seconds=1)).isoformat(), ticket_id),
    )

    assert ticket_repository.get_latest_reopenable_ticket_for_user(4001) is None
