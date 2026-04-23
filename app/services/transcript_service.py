from __future__ import annotations

import io
from collections import defaultdict

import discord

from app.integrations.transcript_exporter import TranscriptExporter
from app.services.ticket_service import TicketService
from app.utils.text import panel_name_from_ticket_type


class TranscriptService:
    def __init__(self, ticket_service: TicketService, exporter: TranscriptExporter) -> None:
        self._ticket_service = ticket_service
        self._exporter = exporter

    async def collect_channel_stats(
        self,
        channel: discord.TextChannel,
    ) -> tuple[int, int, int, dict[int, int]]:
        messages_count = 0
        attachments_saved = 0
        attachments_skipped = 0
        authors: dict[int, int] = {}

        async for message in channel.history(limit=None, oldest_first=True):
            messages_count += 1
            if message.author:
                authors[message.author.id] = authors.get(message.author.id, 0) + 1

        return messages_count, attachments_saved, attachments_skipped, authors

    def format_users_in_transcript(
        self,
        guild: discord.Guild,
        authors_counter: dict[int, int],
        limit: int = 10,
    ) -> str:
        if not authors_counter:
            return "—"

        items = sorted(authors_counter.items(), key=lambda item: item[1], reverse=True)
        lines: list[str] = []
        for user_id, count in items[:limit]:
            member = guild.get_member(user_id)
            if member:
                label = f"{member.mention} - {member}"
            else:
                label = f"<@{user_id}>"
            lines.append(f"{count} - {label}")

        if len(items) > limit:
            lines.append(f"… +{len(items) - limit} users")

        return "\n".join(lines)

    async def auto_save_transcript(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> tuple[bool, str]:
        try:
            guild = interaction.guild
            if guild is None:
                return False, "guild not found"

            ticket_type = self._ticket_service.ticket_type_for_channel(channel)
            transcript_channel_id = self._ticket_service.transcript_channel_id_for_ticket_type(ticket_type)
            if not transcript_channel_id:
                return False, f"transcript channel id not set for ticket_type={ticket_type.value}"

            transcript_channel = guild.get_channel(transcript_channel_id)
            if not isinstance(transcript_channel, discord.TextChannel):
                return False, f"transcript channel not found (id={transcript_channel_id})"

            msg_count, att_saved, att_skipped, authors_counter = await self.collect_channel_stats(channel)
            transcript = await self._exporter.export_channel(channel)
            if transcript is None:
                return False, "chat_exporter returned None"

            filename = f"transcript-{channel.name}.html"
            file = discord.File(io.BytesIO(transcript.encode("utf-8")), filename=filename)

            opener = await self._ticket_service.find_ticket_opener(guild, channel)
            ticket_owner_value = opener.mention if opener else "Unknown"
            panel_name = panel_name_from_ticket_type(ticket_type)

            server_info_text = (
                "<Server-Info>\n"
                f"    Server: [ {guild.name} ] ({guild.id})\n"
                f"    Channel: {channel.name} ({channel.id})\n"
                f"    Messages: {msg_count}\n"
                f"    Attachments Saved: {att_saved}\n"
                f"    Attachments Skipped: {att_skipped} (due maximum file size limits.)\n"
            )
            content_block = f"```{server_info_text}```"

            embed = discord.Embed(color=discord.Color.dark_gray())
            try:
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
            except Exception:
                embed.set_author(name=str(interaction.user))

            embed.add_field(name="Ticket Owner", value=ticket_owner_value, inline=True)
            embed.add_field(name="Ticket Name", value=channel.name, inline=True)
            embed.add_field(name="Panel Name", value=panel_name, inline=True)
            embed.add_field(name="Direct Transcript", value="Auto Saved", inline=True)
            embed.add_field(
                name="Users in transcript",
                value=self.format_users_in_transcript(guild, authors_counter, limit=10),
                inline=False,
            )

            await transcript_channel.send(content=content_block, file=file, embed=embed)
            return True, "ok"
        except Exception as exc:
            return False, str(exc)
