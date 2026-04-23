from __future__ import annotations

from datetime import datetime
import logging
from typing import Optional

import discord

from app.config import constants
from app.domain.enums import TicketType
from app.domain.models import TicketRecord
from app.repositories.counters import CounterRepository
from app.repositories.tickets import TicketRepository
from app.services.logging_service import LoggingService
from app.utils.text import (
    detect_ticket_type_from_name,
    extract_ticket_number_for_type,
    format_ticket_number,
    panel_name_from_ticket_type,
    sanitize_channel_name,
)
from app.utils.time import utcnow


class TicketService:
    def __init__(
        self,
        ticket_repository: TicketRepository,
        counter_repository: CounterRepository,
        logging_service: LoggingService,
        logger: logging.Logger,
    ) -> None:
        self._tickets = ticket_repository
        self._counters = counter_repository
        self._logging = logging_service
        self._logger = logger

    def application_form_message(self, opener_mention: str) -> str:
        return constants.APPLICATION_FORM_MESSAGE_TEMPLATE.format(
            opener_mention=opener_mention,
            google_form_url=constants.GOOGLE_FORM_URL,
        )

    def build_ticket_texts(
        self,
        guild: discord.Guild,
        opener: discord.Member,
        ticket_type: TicketType,
    ) -> tuple[str, str, discord.Color]:
        if ticket_type == TicketType.APPLICATION:
            roles_to_mention = [guild.get_role(role_id) for role_id in constants.APPLICATION_ROLES]
            main_message_text = (
                f"{opener.mention} Приветствую! "
                f"{' '.join([role.mention for role in roles_to_mention if role])} "
                f"ответят вам в ближайшее время! Ожидайте."
            )
            embed_message_text = "Пожалуйста, дождитесь ответа от Оратора, он свяжется с вами в ближайшее время."
            embed_color = discord.Color.green()
        elif ticket_type == TicketType.IDEA:
            roles_to_mention = [guild.get_role(role_id) for role_id in constants.IDEA_ROLES]
            main_message_text = (
                f"{opener.mention} Спасибо за вашу инициативу! "
                f"{' '.join([role.mention for role in roles_to_mention if role])} "
                f"рассмотрят вашу идею в ближайшее время."
            )
            embed_message_text = (
                "💡 **Опишите вашу идею максимально подробно.**\n"
                "Администрация обязательно её рассмотрит и даст ответ."
            )
            embed_color = discord.Color.gold()
        else:
            roles_to_mention = [guild.get_role(role_id) for role_id in constants.OTHER_ROLES]
            main_message_text = (
                f"{opener.mention} Жалоба принята. "
                f"{' '.join([role.mention for role in roles_to_mention if role])} "
                f"рассмотрят её в ближайшее время."
            )
            embed_message_text = (
                "🚨 **Жалоба на игрока**\n"
                "Пожалуйста, укажите:\n"
                "• Ник/ID игрока\n"
                "• Что произошло (по фактам)\n"
                "• Время/сервер/место (если важно)\n"
                "• Скрины/видео (если есть)\n"
            )
            embed_color = discord.Color.red()

        return main_message_text, embed_message_text, embed_color

    async def render_ticket_as_normal(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        opener: discord.Member,
        ticket_type: TicketType,
    ) -> None:
        from app.discord_app.views.close import CloseTicketView

        main_message_text, embed_message_text, embed_color = self.build_ticket_texts(guild, opener, ticket_type)
        await channel.send(main_message_text)

        embed = discord.Embed(
            title="Тикет создан",
            description=embed_message_text,
            color=embed_color,
        )
        await channel.send(embed=embed, view=CloseTicketView())

    async def get_opener_member_from_db(self, guild: discord.Guild, ticket_name: str) -> Optional[discord.Member]:
        data = self._tickets.get_ticket_by_name(ticket_name)
        if not data:
            return None
        opener_id = int(data.opener_id or 0)
        if opener_id <= 0:
            return None
        member = guild.get_member(opener_id)
        if member:
            return member
        try:
            return await guild.fetch_member(opener_id)
        except Exception:
            return None

    def bot_member_in_guild(self, guild: discord.Guild) -> Optional[discord.Member]:
        if guild.me:
            return guild.me
        if guild._state.user is None:
            return None
        return guild.get_member(guild._state.user.id)

    def is_support_member(self, member: discord.Member, channel: discord.TextChannel) -> bool:
        support_role = member.guild.get_role(constants.SUPPORT_ROLE_ID)
        if support_role and support_role in member.roles:
            return True
        return channel.permissions_for(member).manage_channels

    async def find_ticket_opener(
        self,
        guild: discord.Guild,
        ticket_channel: discord.TextChannel,
    ) -> Optional[discord.Member]:
        data = self._tickets.get_ticket_by_channel_id(ticket_channel.id)
        if data:
            opener_id = int(data.opener_id or 0)
            if opener_id > 0:
                member = guild.get_member(opener_id)
                if member:
                    return member
                try:
                    return await guild.fetch_member(opener_id)
                except Exception:
                    pass

        opener = await self.get_opener_member_from_db(guild, ticket_channel.name)
        if opener:
            return opener

        support_role = guild.get_role(constants.SUPPORT_ROLE_ID)
        for target, perms in ticket_channel.overwrites.items():
            if isinstance(target, discord.Member) and perms.view_channel:
                if support_role and support_role in target.roles:
                    continue
                if target.bot:
                    continue
                return target
        return None

    def _next_notes_name(self, base: str, existing_names: set[str]) -> str:
        if base not in existing_names:
            return base
        index = 2
        while True:
            candidate = f"{base}-{index}"
            if candidate not in existing_names:
                return candidate
            index += 1

    async def create_staff_notes_channel(
        self,
        interaction: discord.Interaction,
        ticket_channel: discord.TextChannel,
    ) -> tuple[bool, str]:
        from app.discord_app.views.notes import NotesDeleteView

        guild = interaction.guild
        if guild is None:
            return False, "Ошибка: сервер не найден."

        if not self.is_support_member(interaction.user, ticket_channel):
            return False, constants.ACCESS_DENIED_TEXT

        support_role = guild.get_role(constants.SUPPORT_ROLE_ID)
        if not support_role:
            return False, "SUPPORT_ROLE_ID не найден."

        opener = await self.find_ticket_opener(guild, ticket_channel)
        opener_tag = sanitize_channel_name(opener.display_name if opener else "unknown")
        base_name = f"🔒-notes-{opener_tag}"
        category = ticket_channel.category

        existing: set[str] = set()
        if category:
            for channel in getattr(category, "channels", []):
                if isinstance(channel, discord.TextChannel):
                    existing.add(channel.name)
        else:
            existing = {channel.name for channel in guild.text_channels}

        notes_name = self._next_notes_name(base_name, existing)
        bot_member = self.bot_member_in_guild(guild)

        overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if opener:
            overwrites[opener] = discord.PermissionOverwrite(view_channel=False)
        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )

        notes_channel = await guild.create_text_channel(
            notes_name,
            category=category,
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title="📝 Заметки персонала",
            description=(
                f"Приватный канал для саппортов по тикету: {ticket_channel.mention}\n"
                f"Создатель тикета сюда не имеет доступа."
            ),
            color=discord.Color.dark_gray(),
        )
        embed.add_field(name="🎫 Тикет", value=ticket_channel.name, inline=True)
        embed.add_field(name="👤 Создал заметки", value=interaction.user.mention, inline=True)
        if opener:
            embed.add_field(name="🧑‍💼 Создатель тикета", value=opener.mention, inline=True)

        await notes_channel.send(embed=embed, view=NotesDeleteView())
        await self._logging.log_action(guild, ticket_channel.name, f"Notes Created -> {notes_channel.name}", interaction.user)
        return True, f"Канал заметок создан: {notes_channel.mention}"

    def counter_key(self, ticket_type: TicketType) -> str:
        return f"ticket_counter:{ticket_type.value}"

    def scan_max_ticket_number_for_type(self, guild: discord.Guild, ticket_type: TicketType) -> tuple[int, bool]:
        max_num = 0
        found_any = False
        for category_id in (constants.OPEN_CATEGORY_ID, constants.CLOSED_CATEGORY_ID):
            category = guild.get_channel(category_id)
            if not category:
                continue
            for channel in getattr(category, "channels", []):
                number = extract_ticket_number_for_type(channel.name, ticket_type)
                if number is not None:
                    found_any = True
                    max_num = max(max_num, number)
        return max_num, found_any

    def get_next_ticket_number(self, guild: discord.Guild, ticket_type: TicketType) -> int:
        key = self.counter_key(ticket_type)

        def seed_factory() -> int:
            max_num, found_any = self.scan_max_ticket_number_for_type(guild, ticket_type)
            if found_any:
                return max_num
            first = int(constants.TICKET_FIRST_NUMBER.get(ticket_type.value, 1))
            return first - 1

        return self._counters.next_value(key, seed_factory)

    def get_ticket_for_channel(self, channel: discord.TextChannel) -> Optional[TicketRecord]:
        data = self._tickets.get_ticket_by_channel_id(channel.id)
        if data:
            return data
        return self._tickets.get_ticket_by_name(channel.name)

    def ticket_type_for_channel(self, channel: discord.TextChannel) -> TicketType:
        data = self._tickets.get_ticket_by_channel_id(channel.id)
        if data:
            return data.ticket_type

        data_by_name = self._tickets.get_ticket_by_name(channel.name)
        if data_by_name:
            return data_by_name.ticket_type

        return detect_ticket_type_from_name(channel.name)

    def transcript_channel_id_for_ticket_type(self, ticket_type: TicketType) -> int:
        if ticket_type == TicketType.APPLICATION:
            return int(constants.TRANSCRIPT_CHANNEL_ID_APPLICATION or 0)
        if ticket_type == TicketType.IDEA:
            return int(constants.TRANSCRIPT_CHANNEL_ID_IDEA or 0)
        return int(constants.TRANSCRIPT_CHANNEL_ID_OTHER or 0)

    def resolve_active_ticket_channel(self, guild: discord.Guild, opener_id: int) -> Optional[discord.TextChannel]:
        row = self._tickets.get_active_ticket_for_user(opener_id)
        if row is None:
            return None

        if row.last_channel_id:
            channel = guild.get_channel(int(row.last_channel_id))
            if isinstance(channel, discord.TextChannel):
                if not (channel.category and channel.category.id == constants.OPEN_CATEGORY_ID):
                    try:
                        self._tickets.mark_ticket_closed_by_channel(
                            channel.id,
                            row.ticket_type,
                            opener_id,
                            utcnow(),
                            ticket_name=channel.name,
                        )
                    except Exception:
                        pass
                    return None
                return channel

        if row.ticket_name:
            for channel in guild.text_channels:
                if channel.name == row.ticket_name and isinstance(channel, discord.TextChannel):
                    if not (channel.category and channel.category.id == constants.OPEN_CATEGORY_ID):
                        try:
                            self._tickets.mark_ticket_closed_by_channel(
                                channel.id,
                                row.ticket_type,
                                opener_id,
                                utcnow(),
                                ticket_name=channel.name,
                            )
                        except Exception:
                            pass
                        return None
                    return channel
        return None

    async def open_overwrites_for_ticket(
        self,
        guild: discord.Guild,
        opener: discord.Member,
    ) -> dict[discord.abc.Snowflake, discord.PermissionOverwrite]:
        bot_member = self.bot_member_in_guild(guild)
        support_role = guild.get_role(constants.SUPPORT_ROLE_ID)
        overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            opener: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            )
        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )
        return overwrites

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: TicketType) -> None:
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if guild is None:
            await interaction.followup.send("Ошибка: сервер не найден.", ephemeral=True)
            return

        open_category = guild.get_channel(constants.OPEN_CATEGORY_ID)
        if not open_category:
            await interaction.followup.send("Ошибка: категория OPEN не найдена.", ephemeral=True)
            return

        existing_channel = self.resolve_active_ticket_channel(guild, interaction.user.id)
        if existing_channel:
            await interaction.followup.send(f"У тебя уже есть открытый тикет: {existing_channel.mention}", ephemeral=True)
            return

        ticket_id = self._tickets.reserve_ticket(interaction.user.id, ticket_type)
        if ticket_id is None:
            existing_channel = self.resolve_active_ticket_channel(guild, interaction.user.id)
            if existing_channel:
                await interaction.followup.send(
                    f"У тебя уже есть открытый тикет: {existing_channel.mention}",
                    ephemeral=True,
                )
                return
            await interaction.followup.send("У тебя уже есть открытый тикет.", ephemeral=True)
            return

        ticket_counter = self.get_next_ticket_number(guild, ticket_type)
        number_text = format_ticket_number(ticket_type, ticket_counter)
        prefix = constants.TICKET_NAME_PREFIX.get(ticket_type.value, constants.TICKET_NAME_PREFIX[TicketType.OTHER.value])
        ticket_name = f"{prefix}-{number_text}"
        topic = f"{constants.TICKET_TOPIC_TITLE.get(ticket_type.value, '🆘 help-помогите')}-{number_text}"
        overwrites = await self.open_overwrites_for_ticket(guild, interaction.user)

        try:
            channel = await guild.create_text_channel(
                ticket_name,
                category=open_category,
                overwrites=overwrites,
                topic=topic,
            )
            self._tickets.finalize_ticket_open(ticket_id, channel.name, channel.id)
        except Exception as exc:
            self._tickets.rollback_reserved_ticket(ticket_id)
            await interaction.followup.send(
                f"Ошибка создания тикета. Попробуй ещё раз. ({exc})",
                ephemeral=True,
            )
            return

        await self.render_ticket_as_normal(guild, channel, interaction.user, ticket_type)
        await self._logging.log_action(guild, channel.name, "Created", interaction.user)

        if ticket_type == TicketType.APPLICATION:
            try:
                await channel.send(self.application_form_message(interaction.user.mention))
            except Exception:
                pass

        await interaction.followup.send(f"Тикет создан: {channel.mention}", ephemeral=True)

    async def close_ticket_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> tuple[bool, str]:
        guild = interaction.guild
        if guild is None:
            return False, "Ошибка: сервер не найден."

        closed_category = guild.get_channel(constants.CLOSED_CATEGORY_ID)
        if not closed_category:
            return False, "Категория CLOSED не найдена."

        await channel.edit(category=closed_category)

        opener = await self.find_ticket_opener(guild, channel)
        if opener:
            try:
                await channel.set_permissions(opener, overwrite=discord.PermissionOverwrite(view_channel=False))
            except Exception:
                pass

        ticket_type = self.ticket_type_for_channel(channel)
        opener_id = opener.id if opener else 0
        closed_at = utcnow()

        try:
            self._tickets.mark_ticket_closed_by_channel(channel.id, ticket_type, opener_id, closed_at, ticket_name=channel.name)
        except Exception as exc:
            self._logger.exception("DB close failed: %s", exc)

        if opener:
            await self._send_close_dm(guild, interaction.user, opener, channel, ticket_type)

        await self._logging.log_action(guild, channel.name, "Closed", interaction.user)
        return True, "ok"

    async def _send_close_dm(
        self,
        guild: discord.Guild,
        actor: discord.abc.User,
        opener: discord.Member,
        channel: discord.TextChannel,
        ticket_type: TicketType,
    ) -> None:
        from app.discord_app.views.reopen_dm import DMReopenView

        try:
            now_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            content_text = f"📩 Ваш тикет `{channel.name}` был закрыт!\nСпасибо за обращение 💙"

            embed = discord.Embed(
                title="Информация о закрытии тикета",
                color=discord.Color.green(),
                timestamp=utcnow(),
            )
            icon_url = guild.icon.url if guild.icon else None
            if icon_url:
                embed.set_author(name="[WON] | Ticket BOT", icon_url=icon_url)
            else:
                embed.set_author(name="[WON] | Ticket BOT")
            embed.add_field(name="🎫 Тикет", value=channel.name, inline=True)
            embed.add_field(name="👤 Закрыл", value=actor.mention, inline=True)
            embed.add_field(name="⏰ Время закрытия", value=now_time, inline=False)
            embed.add_field(name="Тип тикета", value=ticket_type.value, inline=True)
            embed.set_footer(text="Ticket System • Сегодня")

            await opener.send(content=content_text, embed=embed, view=DMReopenView())
        except Exception:
            pass
