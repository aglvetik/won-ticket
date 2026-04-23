from __future__ import annotations

from discord.ext import commands, tasks

from app.config import constants
from app.discord_app.container import AppContainer
from app.discord_app.views.application_decision import ApplicationDecisionView
from app.discord_app.views.after_close import AfterCloseView
from app.discord_app.views.close import CloseConfirmationView, CloseTicketView
from app.discord_app.views.notes import NotesDeleteView
from app.discord_app.views.panel import MainPanelView
from app.discord_app.views.reopen_dm import DMReopenView


class LifecycleHandler:
    def __init__(self, container: AppContainer) -> None:
        self._container = container
        self._bot: commands.Bot | None = None
        self._views_registered = False

    def bind(self, bot: commands.Bot) -> None:
        self._bot = bot

    def register_views(self) -> None:
        if self._bot is None or self._views_registered:
            return
        self._bot.add_view(MainPanelView())
        self._bot.add_view(CloseTicketView())
        self._bot.add_view(CloseConfirmationView())
        self._bot.add_view(AfterCloseView())
        self._bot.add_view(NotesDeleteView())
        self._bot.add_view(DMReopenView())
        self._bot.add_view(ApplicationDecisionView())
        self._views_registered = True

    @tasks.loop(seconds=constants.GS_POLL_SECONDS)
    async def google_forms_poll_task(self) -> None:
        if self._bot is None:
            return
        await self._container.google_forms_service.poll_once(self._bot)

    @tasks.loop(minutes=constants.CLEANUP_INTERVAL_MINUTES)
    async def cleanup_task(self) -> None:
        if self._bot is None:
            return

        guild = self._bot.get_guild(constants.GUILD_ID)
        if guild is None:
            return

        try:
            removed = self._container.cleanup_service.cleanup_stale_reservations(
                guild,
                ttl_seconds=constants.CLEANUP_TTL_SECONDS,
            )
            if removed:
                self._container.logging_service.logger.warning(
                    "Cleanup removed stale active tickets: %s",
                    removed,
                )
        except Exception as exc:
            self._container.logging_service.logger.exception("Cleanup failed: %s", exc)

    async def on_ready(self) -> None:
        if self._bot is None:
            return

        self._container.db.initialize()
        self._container.google_sheets_client.initialize()

        self._container.logging_service.logger.info("%s готов. Бот онлайн!", self._bot.user)

        guild = self._bot.get_guild(constants.GUILD_ID)
        if guild:
            try:
                removed = self._container.cleanup_service.cleanup_stale_reservations(
                    guild,
                    ttl_seconds=constants.CLEANUP_TTL_SECONDS,
                )
                if removed:
                    self._container.logging_service.logger.warning(
                        "Startup cleanup removed stale active tickets: %s",
                        removed,
                    )
            except Exception as exc:
                self._container.logging_service.logger.exception("Startup cleanup failed: %s", exc)

        if not self.cleanup_task.is_running():
            self.cleanup_task.start()

        if self._container.google_sheets_client.is_ready and not self.google_forms_poll_task.is_running():
            self.google_forms_poll_task.start()

        self.register_views()
        await self._container.panel_service.republish_panel(self._bot)
