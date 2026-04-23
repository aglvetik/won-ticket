from __future__ import annotations

from app.domain.enums import TicketType


def test_ticket_repository_enforces_single_active_ticket_per_user(ticket_repository) -> None:
    first_id = ticket_repository.reserve_ticket(1001, TicketType.APPLICATION)
    second_id = ticket_repository.reserve_ticket(1001, TicketType.OTHER)

    assert first_id is not None
    assert second_id is None


def test_ticket_repository_finalizes_and_reads_back_ticket(ticket_repository) -> None:
    ticket_id = ticket_repository.reserve_ticket(2002, TicketType.IDEA)
    assert ticket_id is not None

    ticket_repository.finalize_ticket_open(ticket_id, "idea-креатив-1", 555)
    by_channel = ticket_repository.get_ticket_by_channel_id(555)
    by_name = ticket_repository.get_ticket_by_name("idea-креатив-1")

    assert by_channel is not None
    assert by_name is not None
    assert by_channel.ticket_id == ticket_id
    assert by_channel.ticket_name == "idea-креатив-1"
    assert by_name.last_channel_id == 555
