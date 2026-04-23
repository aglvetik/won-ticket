from __future__ import annotations

from discord.ext import commands

from app.discord_app.container import get_container


def register_moderation_commands(bot: commands.Bot) -> None:
    @bot.command(name="accept")
    async def accept_cmd(ctx: commands.Context) -> None:
        container = get_container(ctx.bot)
        await container.member_service.handle_accept_command(ctx)

    @bot.command(name="принять")
    async def accept_cmd_ru(ctx: commands.Context) -> None:
        container = get_container(ctx.bot)
        await container.member_service.handle_accept_command(ctx)

    @bot.command(name="reject")
    async def reject_cmd(ctx: commands.Context) -> None:
        container = get_container(ctx.bot)
        await container.member_service.handle_reject_command(ctx)

    @bot.command(name="отклонить")
    async def reject_cmd_ru(ctx: commands.Context) -> None:
        container = get_container(ctx.bot)
        await container.member_service.handle_reject_command(ctx)
