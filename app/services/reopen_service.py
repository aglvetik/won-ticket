from __future__ import annotations

from typing import Optional

import discord

from app.config import constants
from app.domain.enums import TicketType
from app.repositories.tickets import TicketRepository
from app.services.logging_service import LoggingService
from app.services.ticket_service import TicketService


class ReopenService:
    def __init__(
        self,
        ticket_repository: TicketRepository,
        ticket_service: TicketService,
        logging_service: LoggingService,
    ) -> None:
        self._tickets = ticket_repository
        self._ticket_service = ticket_service
        self._logging = logging_service

    async def restore_or_recreate_ticket_channel(
        self,
        guild: discord.Guild,
        data,
        actor: discord.abc.User,
    ) -> tuple[bool, str, Optional[discord.TextChannel]]:
        open_category = guild.get_channel(constants.OPEN_CATEGORY_ID)
        if not open_category:
            return False, "Категория OPEN не найдена.", None

        opener_id = int(data.opener_id or 0)
        if opener_id <= 0:
            return False, "Не найден opener_id.", None

        opener = guild.get_member(opener_id)
        if not opener:
            try:
                opener = await guild.fetch_member(opener_id)
            except Exception:
                opener = None
        if not opener:
            return False, "Не найден участник-автор тикета.", None

        if data.last_channel_id:
            channel = guild.get_channel(int(data.last_channel_id))
            if isinstance(channel, discord.TextChannel):
                if not (channel.category and channel.category.id == constants.OPEN_CATEGORY_ID):
                    await channel.edit(category=open_category)
                try:
                    await channel.set_permissions(
                        opener,
                        overwrite=discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                    )
                except Exception:
                    pass
                self._tickets.reopen_ticket_record(data.ticket_id)
                await channel.send(f"🔓 Тикет переоткрыт по запросу {getattr(actor, 'mention', str(actor))}.")
                return True, "ok", channel

        ticket_type = data.ticket_type
        ticket_name = data.ticket_name or "reopened-ticket"
        topic = f"{constants.TICKET_TOPIC_TITLE.get(ticket_type.value, '🆘 help-помогите')}-reopened"
        overwrites = await self._ticket_service.open_overwrites_for_ticket(guild, opener)

        try:
            new_channel = await guild.create_text_channel(
                ticket_name,
                category=open_category,
                overwrites=overwrites,
                topic=topic,
            )
            self._tickets.reopen_ticket_record(data.ticket_id, channel_id=new_channel.id, ticket_name=new_channel.name)
            await self._ticket_service.render_ticket_as_normal(guild, new_channel, opener, ticket_type)
            await new_channel.send("🔓 Тикет был восстановлен после закрытия.")
            return True, "ok", new_channel
        except Exception as exc:
            return False, str(exc), None

    async def reopen_closed_channel_by_moderator(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> tuple[bool, str]:
        guild = interaction.guild
        if guild is None:
            return False, "Ошибка: сервер не найден."

        if channel.category and channel.category.id == constants.OPEN_CATEGORY_ID:
            return False, "Тикет уже открыт ✅"

        open_category = guild.get_channel(constants.OPEN_CATEGORY_ID)
        if not open_category:
            return False, "Категория OPEN не найдена."

        await channel.edit(category=open_category)

        opener = await self._ticket_service.find_ticket_opener(guild, channel)
        if opener:
            try:
                await channel.set_permissions(
                    opener,
                    overwrite=discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                )
            except Exception:
                pass

        self._tickets.reopen_ticket_by_channel(channel.id)
        await channel.send(f"🔓 Тикет переоткрыт модератором {interaction.user.mention}.")
        await self._logging.log_action(guild, channel.name, "Reopened (Mod)", interaction.user)
        return True, "Тикет переоткрыт ✅"

    async def reopen_from_dm(
        self,
        interaction: discord.Interaction,
        preferred_ticket_name: Optional[str] = None,
    ) -> tuple[bool, str, Optional[discord.TextChannel]]:
        data = self._tickets.get_latest_reopenable_ticket_for_user(
            interaction.user.id,
            preferred_ticket_name=preferred_ticket_name,
        )
        if not data:
            return (
                False,
                "Не найден закрытый тикет для переоткрытия или время уже истекло (5 часов).",
                None,
            )

        client = interaction.client
        if not isinstance(client, discord.Client):
            return False, "Не найден сервер (бот не видит сервер).", None

        guild = client.get_guild(constants.GUILD_ID)
        if guild is None:
            return False, "Не найден сервер (бот не видит сервер).", None

        ok, message, channel = await self.restore_or_recreate_ticket_channel(guild, data, interaction.user)
        if ok and channel:
            await self._logging.log_action(guild, channel.name, "Reopened (DM)", interaction.user)
            return True, f"Тикет переоткрыт: {channel.mention}", channel
        return False, f"Не смог переоткрыть тикет: {message}", None
