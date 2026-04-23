from __future__ import annotations

from dataclasses import dataclass

import discord

from app.config.settings import Settings
from app.db.sqlite import SQLiteDatabase
from app.integrations.google_sheets import GoogleSheetsClient
from app.integrations.transcript_exporter import TranscriptExporter
from app.repositories.counters import CounterRepository
from app.repositories.processed_forms import ProcessedFormsRepository
from app.repositories.tickets import TicketRepository
from app.services.cleanup_service import CleanupService
from app.services.google_forms_service import GoogleFormsService
from app.services.logging_service import LoggingService
from app.services.member_service import MemberService
from app.services.panel_service import PanelService
from app.services.reopen_service import ReopenService
from app.services.ticket_service import TicketService
from app.services.transcript_service import TranscriptService


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    db: SQLiteDatabase
    ticket_repository: TicketRepository
    counter_repository: CounterRepository
    processed_forms_repository: ProcessedFormsRepository
    google_sheets_client: GoogleSheetsClient
    transcript_exporter: TranscriptExporter
    logging_service: LoggingService
    ticket_service: TicketService
    reopen_service: ReopenService
    transcript_service: TranscriptService
    google_forms_service: GoogleFormsService
    member_service: MemberService
    panel_service: PanelService
    cleanup_service: CleanupService


def bind_container(client: discord.Client, container: AppContainer) -> None:
    setattr(client, "app_container", container)


def get_container(client: discord.Client) -> AppContainer:
    container = getattr(client, "app_container", None)
    if not isinstance(container, AppContainer):
        raise RuntimeError("Discord client is missing app_container.")
    return container
