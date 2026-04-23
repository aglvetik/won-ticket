from __future__ import annotations

import logging

import pytest

from app.db.sqlite import SQLiteDatabase
from app.repositories.counters import CounterRepository
from app.repositories.processed_forms import ProcessedFormsRepository
from app.repositories.tickets import TicketRepository
from app.services.cleanup_service import CleanupService
from app.services.logging_service import LoggingService
from app.services.member_service import MemberService
from app.services.ticket_service import TicketService


@pytest.fixture
def db(tmp_path):
    database = SQLiteDatabase(tmp_path / "tickets.db")
    database.initialize()
    return database


@pytest.fixture
def ticket_repository(db):
    return TicketRepository(db)


@pytest.fixture
def counter_repository(db):
    return CounterRepository(db)


@pytest.fixture
def processed_forms_repository(db):
    return ProcessedFormsRepository(db)


@pytest.fixture
def logger():
    return logging.getLogger("ticketbot-tests")


@pytest.fixture
def logging_service(logger):
    return LoggingService(logger)


@pytest.fixture
def ticket_service(ticket_repository, counter_repository, logging_service, logger):
    return TicketService(ticket_repository, counter_repository, logging_service, logger)


@pytest.fixture
def cleanup_service(ticket_repository):
    return CleanupService(ticket_repository)


@pytest.fixture
def member_service(logging_service):
    return MemberService(ticket_service=object(), logging_service=logging_service)
