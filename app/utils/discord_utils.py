from __future__ import annotations

import re
from typing import Optional

import discord

CHANNEL_MENTION_RE = re.compile(r"<#(\d+)>")
BACKTICKED_TICKET_NAME_RE = re.compile(r"`([^`]+)`")


def find_embed_field_value(embed: discord.Embed, field_name: str) -> Optional[str]:
    for field in embed.fields:
        if field.name == field_name:
            return str(field.value)
    return None


def extract_channel_id_from_embeds(message: discord.Message) -> Optional[int]:
    for embed in message.embeds:
        if not embed.description:
            continue
        match = CHANNEL_MENTION_RE.search(embed.description)
        if match:
            return int(match.group(1))
    return None


def extract_ticket_name_from_dm_message(message: discord.Message) -> Optional[str]:
    match = BACKTICKED_TICKET_NAME_RE.search(message.content or "")
    if match:
        return match.group(1)

    for embed in message.embeds:
        ticket_name = find_embed_field_value(embed, "🎫 Тикет")
        if ticket_name:
            return ticket_name.strip()
    return None
