from __future__ import annotations

from app.config import constants
from app.domain.enums import TicketType
from app.utils.text import format_ticket_number
from tests.fakes import FakeCategory, FakeChannel, FakeGuild


def test_other_ticket_number_padding() -> None:
    assert format_ticket_number(TicketType.OTHER, 38) == "0038"


def test_application_counter_starts_from_seed_when_no_existing_channels(ticket_service) -> None:
    guild = FakeGuild()

    first = ticket_service.get_next_ticket_number(guild, TicketType.APPLICATION)
    second = ticket_service.get_next_ticket_number(guild, TicketType.APPLICATION)

    assert first == constants.TICKET_FIRST_NUMBER[TicketType.APPLICATION.value]
    assert second == first + 1


def test_application_counter_scans_existing_open_and_closed_channels(ticket_service) -> None:
    open_category = FakeCategory(
        id=constants.OPEN_CATEGORY_ID,
        channels=[FakeChannel(id=1, name="join-заявка-300")],
    )
    closed_category = FakeCategory(
        id=constants.CLOSED_CATEGORY_ID,
        channels=[FakeChannel(id=2, name="join-заявка-305")],
    )
    guild = FakeGuild(categories=[open_category, closed_category])

    next_number = ticket_service.get_next_ticket_number(guild, TicketType.APPLICATION)

    assert next_number == 306
