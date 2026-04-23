from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.enums import TicketStatus, TicketType


@dataclass(slots=True, frozen=True)
class TicketRecord:
    ticket_id: int
    ticket_name: str
    opener_id: int
    ticket_type: TicketType
    last_channel_id: Optional[int]
    status: TicketStatus
    created_at_utc: str
    closed_at_utc: str
    reopen_until_utc: str


@dataclass(slots=True, frozen=True)
class CleanupCandidate:
    ticket_id: int
    status: TicketStatus
    channel_id: Optional[int]
    created_at_ts: float
