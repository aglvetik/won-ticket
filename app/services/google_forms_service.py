from __future__ import annotations

from collections import defaultdict
import logging
from typing import Any, Optional

import discord

from app.config import constants
from app.domain.enums import TicketType
from app.integrations.google_sheets import GoogleSheetsClient
from app.repositories.processed_forms import ProcessedFormsRepository
from app.services.ticket_service import TicketService
from app.utils.text import (
    build_form_signature,
    clean_answer,
    compact_label,
    extract_ticket_number_from_row,
    format_ticket_number,
    kclean,
    steam_profile_url,
    ticket_prefix_sanitized,
)
from app.utils.time import utcnow


class GoogleFormsService:
    def __init__(
        self,
        google_sheets_client: GoogleSheetsClient,
        processed_forms_repository: ProcessedFormsRepository,
        ticket_service: TicketService,
        logger: logging.Logger,
    ) -> None:
        self._google_sheets = google_sheets_client
        self._processed_forms = processed_forms_repository
        self._ticket_service = ticket_service
        self._logger = logger

    async def find_application_ticket_channel_by_number(
        self,
        guild: discord.Guild,
        ticket_number: int,
    ) -> Optional[discord.TextChannel]:
        prefix = ticket_prefix_sanitized(TicketType.APPLICATION)
        wanted_plain = f"{prefix}-{int(ticket_number)}"
        wanted_padded = f"{prefix}-{format_ticket_number(TicketType.APPLICATION, int(ticket_number))}"

        for channel in guild.text_channels:
            name = (channel.name or "").lower()
            if name in {wanted_plain, wanted_padded}:
                return channel

        tail_plain = f"-{int(ticket_number)}"
        tail_padded = f"-{format_ticket_number(TicketType.APPLICATION, int(ticket_number))}"
        for channel in guild.text_channels:
            name = (channel.name or "").lower()
            if prefix in name and (name.endswith(tail_plain) or name.endswith(tail_padded)):
                return channel

        for category_id in (constants.OPEN_CATEGORY_ID, constants.CLOSED_CATEGORY_ID):
            category = guild.get_channel(category_id)
            if not category:
                continue
            for channel in getattr(category, "channels", []):
                if isinstance(channel, discord.TextChannel):
                    name = (channel.name or "").lower()
                    if name in {wanted_plain, wanted_padded} or (
                        prefix in name and (name.endswith(tail_plain) or name.endswith(tail_padded))
                    ):
                        return channel
        return None

    def build_application_embed(
        self,
        row_dict: dict[str, Any],
        ticket_number: int,
        ticket_channel: Optional[discord.TextChannel],
        guild: discord.Guild,
    ) -> discord.Embed:
        raw_items = [(str(key), clean_answer(value)) for key, value in (row_dict or {}).items()]
        items = [(key, value) for key, value in raw_items if value != ""]

        normalized: dict[str, list[str]] = defaultdict(list)
        for key, value in items:
            label = compact_label(key)
            if value and value not in normalized[label]:
                normalized[label].append(value)

        time_val = ""
        for key, value in items:
            normalized_key = kclean(key)
            if "отметка времени" in normalized_key or "timestamp" in normalized_key:
                time_val = value
                break

        def val(label: str) -> str:
            values = normalized.get(label) or []
            text = "\n".join(values).strip()
            return text if text else "—"

        def yesno(value: str) -> str:
            normalized_value = (value or "").strip().lower()
            if normalized_value in ("да", "yes", "y", "true", "есть", "готов", "готова", "конечно", "угу", "ага"):
                return "✅ Да"
            if normalized_value in ("нет", "no", "n", "false", "нету", "не готов", "не готова"):
                return "❌ Нет"
            return value or "—"

        ticket_text = ticket_channel.mention if ticket_channel else "`не найден`"
        steam_id = val("Steam ID")
        steam_url = steam_profile_url(steam_id if steam_id != "—" else "")

        embed = discord.Embed(
            title="🧾 Новая анкета (Google Form)",
            description=(
                f"🎫 **Тикет:** {ticket_text}\n"
                f"🔢 **Номер тикета:** `{ticket_number}`"
            ),
            color=discord.Color.green(),
            timestamp=utcnow(),
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if steam_url:
            embed.add_field(name="🔗 Steam профиль", value=f"[Открыть профиль]({steam_url})", inline=False)

        meta_lines = []
        if time_val:
            meta_lines.append(f"🕒 **Время:** `{time_val}`")
        meta_lines.append(f"🆔 **Steam ID:** `{steam_id}`")
        meta_lines.append(f"🎟️ **№ тикета:** `{ticket_number}`")
        embed.add_field(name="📌 ID / Мета", value="\n".join(meta_lines), inline=False)

        embed.add_field(
            name="👤 Игрок",
            value=(
                f"**Имя:** {val('Имя')}\n"
                f"**Ник:** {val('Ник')}\n"
                f"**Возраст:** {val('Возраст')}"
            ),
            inline=True,
        )

        embed.add_field(
            name="⏱️ Время / Профиль",
            value=(
                f"**Часовой пояс:** {val('Часовой пояс')}\n"
                f"**Squad (часы):** {val('Squad (часы)')}\n"
                f"**Активность/нед.:** {val('Активность/нед.')}"
            ),
            inline=True,
        )

        embed.add_field(name="🏷️ Клановый опыт", value=val("Кланы"), inline=False)

        embed.add_field(
            name="🎙️ Коммуникация",
            value=(
                f"**Микрофон:** {yesno(val('Микрофон'))}\n"
                f"**Дружелюбие:** {yesno(val('Дружелюбие'))}"
            ),
            inline=True,
        )

        embed.add_field(
            name="🎮 Предпочтения",
            value=(
                f"**Сервера:** {val('Сервера')}\n"
                f"**Роль:** {val('Роль')}"
            ),
            inline=True,
        )

        embed.add_field(
            name="📝 Обратная связь",
            value=(
                f"**Откуда узнал:** {val('Откуда узнал')}\n"
                f"**Идея вопроса:** {val('Идея вопроса')}\n"
                f"**Оценка:** {val('Оценка')}"
            ),
            inline=False,
        )

        embed.set_footer(text="WON • Applications")
        return embed

    async def poll_once(self, bot: discord.Client) -> None:
        if not self._google_sheets.is_ready:
            return

        guild = bot.get_guild(constants.GUILD_ID)
        if guild is None:
            return

        admin_channel = guild.get_channel(constants.APPLICATION_ADMIN_CHANNEL_ID)
        if not isinstance(admin_channel, discord.TextChannel):
            return

        try:
            records = self._google_sheets.get_all_records()
            if not records:
                return

            from app.discord_app.views.application_decision import ApplicationDecisionView

            for sheet_row_index, row_dict in enumerate(records, start=2):
                if sheet_row_index <= constants.START_FROM_ROW:
                    continue

                ticket_number = extract_ticket_number_from_row(row_dict)
                if not ticket_number:
                    self._processed_forms.mark_row_processed(sheet_row_index)
                    continue

                signature = build_form_signature(row_dict, ticket_number)
                already_processed = (
                    self._processed_forms.is_row_processed(sheet_row_index)
                    or self._processed_forms.is_signature_processed(signature)
                )
                if already_processed:
                    self._processed_forms.mark_row_processed(sheet_row_index)
                    self._processed_forms.mark_signature_processed(signature)
                    continue

                ticket_channel = await self.find_application_ticket_channel_by_number(guild, ticket_number)
                if not ticket_channel:
                    self._processed_forms.mark_row_processed(sheet_row_index)
                    self._processed_forms.mark_signature_processed(signature)
                    continue

                embed = self.build_application_embed(row_dict, ticket_number, ticket_channel, guild)
                await admin_channel.send(
                    content=f"<@&{constants.SUPPORT_ROLE_ID}>",
                    embed=embed,
                    view=ApplicationDecisionView(),
                )
                self._processed_forms.mark_row_processed(sheet_row_index)
                self._processed_forms.mark_signature_processed(signature)
        except Exception as exc:
            self._logger.exception("Google poll failed: %s", exc)

    async def resolve_ticket_channel_from_admin_message(
        self,
        guild: discord.Guild,
        message: discord.Message,
    ) -> Optional[discord.TextChannel]:
        from app.utils.discord_utils import extract_channel_id_from_embeds

        channel_id = extract_channel_id_from_embeds(message)
        if channel_id is None:
            return None
        channel = guild.get_channel(channel_id)
        return channel if isinstance(channel, discord.TextChannel) else None
