from __future__ import annotations

from typing import Optional

import chat_exporter
import discord


class TranscriptExporter:
    async def export_channel(self, channel: discord.TextChannel) -> Optional[str]:
        return await chat_exporter.export(channel, limit=None)
