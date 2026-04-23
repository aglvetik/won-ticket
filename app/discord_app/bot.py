from __future__ import annotations

import discord
from discord.ext import commands

from app.discord_app.commands.moderation import register_moderation_commands
from app.discord_app.commands.panel import register_panel_command
from app.discord_app.container import AppContainer, bind_container
from app.discord_app.handlers.errors import register_error_handlers
from app.discord_app.handlers.lifecycle import LifecycleHandler


def create_bot(container: AppContainer) -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    bind_container(bot, container)

    register_panel_command(bot)
    register_moderation_commands(bot)
    register_error_handlers(bot)

    lifecycle = LifecycleHandler(container)
    lifecycle.bind(bot)
    setattr(bot, "lifecycle_handler", lifecycle)

    @bot.event
    async def on_ready() -> None:
        await lifecycle.on_ready()

    return bot
