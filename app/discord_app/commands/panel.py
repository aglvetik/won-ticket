from __future__ import annotations

from discord.ext import commands

from app.discord_app.container import get_container


def register_panel_command(bot: commands.Bot) -> None:
    @bot.command()
    async def panel(ctx: commands.Context) -> None:
        container = get_container(ctx.bot)
        await container.panel_service.send_panel_command(ctx)
