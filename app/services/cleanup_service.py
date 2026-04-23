from __future__ import annotations

import discord

from app.domain.enums import TicketStatus
from app.repositories.tickets import TicketRepository
from app.utils.time import now_ts


class CleanupService:
    def __init__(self, ticket_repository: TicketRepository) -> None:
        self._tickets = ticket_repository

    def cleanup_stale_reservations(self, guild: discord.Guild, ttl_seconds: int = 600) -> int:
        now = now_ts()
        removed = 0

        for ticket in self._tickets.list_active_cleanup_candidates():
            age = now - float(ticket.created_at_ts or 0)

            if ticket.status == TicketStatus.RESERVED:
                if age >= ttl_seconds:
                    self._tickets.delete_ticket_if_status(ticket.ticket_id, TicketStatus.RESERVED)
                    removed += 1
                continue

            if ticket.status == TicketStatus.OPEN:
                if ticket.channel_id is None:
                    if age >= ttl_seconds:
                        self._tickets.delete_ticket_if_status(ticket.ticket_id, TicketStatus.OPEN)
                        removed += 1
                    continue

                exists = guild.get_channel(int(ticket.channel_id)) is not None
                if (not exists) and age >= ttl_seconds:
                    self._tickets.delete_ticket_if_status(ticket.ticket_id, TicketStatus.OPEN)
                    removed += 1

        return removed
