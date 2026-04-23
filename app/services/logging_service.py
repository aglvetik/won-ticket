from __future__ import annotations

import logging

import discord

from app.config import constants
from app.utils.time import utcnow


class LoggingService:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def log_action(
        self,
        guild: discord.Guild,
        ticket: str,
        action: str,
        user: discord.abc.User,
    ) -> None:
        log_channel = guild.get_channel(constants.LOG_CHANNEL_ID)
        if not isinstance(log_channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title="📑 Logged Info",
            color=discord.Color.orange(),
            timestamp=utcnow(),
        )
        embed.add_field(name="🎫 Ticket", value=f"{ticket}", inline=True)
        embed.add_field(name="⚙ Action", value=f"{action}", inline=True)
        embed.add_field(name="👤 By", value=getattr(user, "mention", str(user)), inline=True)
        embed.set_footer(text="Ticket System Logger")
        await log_channel.send(embed=embed)
