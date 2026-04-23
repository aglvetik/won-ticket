from __future__ import annotations

from enum import Enum


class TicketType(str, Enum):
    APPLICATION = "application"
    IDEA = "idea"
    OTHER = "other"

    @classmethod
    def from_value(cls, value: str) -> "TicketType":
        try:
            return cls(value)
        except ValueError:
            return cls.OTHER


class TicketStatus(str, Enum):
    RESERVED = "reserved"
    OPEN = "open"
    CLOSED = "closed"

    @classmethod
    def from_value(cls, value: str) -> "TicketStatus":
        try:
            return cls(value)
        except ValueError:
            return cls.OPEN
