from __future__ import annotations

from app.domain.enums import TicketType
from tests.fakes import FakeChannel, FakeGuild


def test_cleanup_removes_stale_reserved_and_missing_open_tickets(db, ticket_repository, cleanup_service) -> None:
    reserved_id = ticket_repository.reserve_ticket(3001, TicketType.APPLICATION)
    open_id = ticket_repository.reserve_ticket(3002, TicketType.OTHER)
    keep_id = ticket_repository.reserve_ticket(3003, TicketType.IDEA)

    assert reserved_id is not None and open_id is not None and keep_id is not None

    ticket_repository.finalize_ticket_open(open_id, "help-помогите-0038", 9001)
    ticket_repository.finalize_ticket_open(keep_id, "idea-креатив-1", 9002)

    conn = db.get_connection()
    conn.execute("UPDATE tickets SET created_at_ts=0 WHERE ticket_id IN (?, ?, ?)", (reserved_id, open_id, keep_id))

    guild = FakeGuild(channels=[FakeChannel(id=9002, name="idea-креатив-1")])
    removed = cleanup_service.cleanup_stale_reservations(guild, ttl_seconds=600)

    assert removed == 2
    assert ticket_repository.get_active_ticket_for_user(3001) is None
    assert ticket_repository.get_active_ticket_for_user(3002) is None
    assert ticket_repository.get_active_ticket_for_user(3003) is not None
