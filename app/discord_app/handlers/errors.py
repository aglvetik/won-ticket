from __future__ import annotations

from discord.ext import commands

from app.discord_app.container import get_container


def register_error_handlers(bot: commands.Bot) -> None:
    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception) -> None:
        container = get_container(ctx.bot)
        container.logging_service.logger.exception("Command error: %s", error)

    @bot.event
    async def on_error(event: str, *args, **kwargs) -> None:
        del args, kwargs
        container = get_container(bot)
        container.logging_service.logger.exception("Unhandled error in event: %s", event)
