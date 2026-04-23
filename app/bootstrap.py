from __future__ import annotations

import logging

from app.config.settings import Settings
from app.db.sqlite import SQLiteDatabase
from app.discord_app.bot import create_bot
from app.discord_app.container import AppContainer
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


def configure_logging(level: str) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("ticketbot")


def build_container() -> AppContainer:
    settings = Settings.from_env()
    logger = configure_logging(settings.log_level)

    db = SQLiteDatabase(settings.db_path)
    ticket_repository = TicketRepository(db)
    counter_repository = CounterRepository(db)
    processed_forms_repository = ProcessedFormsRepository(db)

    google_sheets_client = GoogleSheetsClient(settings.google_credentials_file, logger)
    transcript_exporter = TranscriptExporter()

    logging_service = LoggingService(logger)
    ticket_service = TicketService(ticket_repository, counter_repository, logging_service, logger)
    reopen_service = ReopenService(ticket_repository, ticket_service, logging_service)
    transcript_service = TranscriptService(ticket_service, transcript_exporter)
    google_forms_service = GoogleFormsService(
        google_sheets_client,
        processed_forms_repository,
        ticket_service,
        logger,
    )
    member_service = MemberService(ticket_service, logging_service)
    panel_service = PanelService()
    cleanup_service = CleanupService(ticket_repository)

    return AppContainer(
        settings=settings,
        db=db,
        ticket_repository=ticket_repository,
        counter_repository=counter_repository,
        processed_forms_repository=processed_forms_repository,
        google_sheets_client=google_sheets_client,
        transcript_exporter=transcript_exporter,
        logging_service=logging_service,
        ticket_service=ticket_service,
        reopen_service=reopen_service,
        transcript_service=transcript_service,
        google_forms_service=google_forms_service,
        member_service=member_service,
        panel_service=panel_service,
        cleanup_service=cleanup_service,
    )


def create_application():
    container = build_container()
    return create_bot(container)
