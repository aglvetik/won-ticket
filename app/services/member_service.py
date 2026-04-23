from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from app.config import constants
from app.domain.enums import TicketType
from app.services.logging_service import LoggingService
from app.services.ticket_service import TicketService


class MemberService:
    def __init__(self, ticket_service: TicketService, logging_service: LoggingService) -> None:
        self._ticket_service = ticket_service
        self._logging = logging_service

    def has_application_mod_role(self, member: discord.Member) -> bool:
        role = member.guild.get_role(constants.APPLICATION_MOD_ROLE_ID)
        return bool(role and role in member.roles)

    async def try_delete_command_message(self, ctx: commands.Context) -> None:
        try:
            await ctx.message.delete()
        except Exception:
            pass

    async def temp_warn(self, channel: discord.TextChannel, text: str, seconds: int = 6) -> None:
        try:
            message = await channel.send(f"⚠️ {text}")
            try:
                await message.delete(delay=seconds)
            except Exception:
                pass
        except Exception:
            pass

    async def try_accept_roles_and_nick(
        self,
        guild: discord.Guild,
        member: discord.Member,
    ) -> tuple[bool, str]:
        guest_role = guild.get_role(constants.GUEST_ROLE_ID) if constants.GUEST_ROLE_ID else None
        accept_roles = [guild.get_role(role_id) for role_id in constants.ACCEPT_ROLES_IDS]

        try:
            if guest_role and guest_role in member.roles:
                await member.remove_roles(guest_role, reason="Accepted to clan via ticketbot")

            add_list = [role for role in accept_roles if role and role not in member.roles]
            if add_list:
                await member.add_roles(*add_list, reason="Accepted to clan via ticketbot")
        except Exception as exc:
            return (
                False,
                f"Не смог выдать/снять роли (проверь иерархию ролей и права бота Manage Roles): {exc}",
            )

        try:
            current = member.nick or member.name
            if not current.startswith(constants.CLAN_TAG):
                new_nick = f"{constants.CLAN_TAG} {current}"
                if len(new_nick) > 32:
                    new_nick = new_nick[:32]
                await member.edit(nick=new_nick, reason="Accepted to clan via ticketbot")
        except Exception as exc:
            return (
                True,
                f"Роли ок, но ник не сменился (проверь Manage Nicknames и роль бота): {exc}",
            )

        return True, "Роли и ник обновлены."

    def command_allowed(self, ctx: commands.Context) -> tuple[bool, str]:
        if not isinstance(ctx.channel, discord.TextChannel):
            return False, "Команда работает только в текстовом канале тикета."
        if not ctx.guild:
            return False, "Команда работает только на сервере."
        if not isinstance(ctx.author, discord.Member):
            return False, "Команда работает только для участников сервера."
        if not self.has_application_mod_role(ctx.author):
            return False, f"Нет роли для мод-команд (role id: {constants.APPLICATION_MOD_ROLE_ID})."

        data = self._ticket_service.get_ticket_for_channel(ctx.channel)
        if not data:
            return False, "Не нашёл тикет в БД (ни по имени, ни по channel_id)."
        if data.ticket_type != TicketType.APPLICATION:
            return False, f"Это не тикет-заявка (ticket_type={data.ticket_type.value})."

        opener_id = int(data.opener_id or 0)
        if opener_id <= 0:
            return False, "В БД нет opener_id для этого тикета."
        return True, "OK"

    async def get_opener_from_ticketdata(
        self,
        guild: discord.Guild,
        opener_id: int,
    ) -> Optional[discord.Member]:
        member = guild.get_member(opener_id)
        if member:
            return member
        try:
            return await guild.fetch_member(opener_id)
        except Exception:
            return None

    async def handle_accept_command(self, ctx: commands.Context) -> None:
        await self.try_delete_command_message(ctx)

        ok, reason = self.command_allowed(ctx)
        if not ok:
            await self.temp_warn(ctx.channel, reason)
            return

        data = self._ticket_service.get_ticket_for_channel(ctx.channel)
        if not data:
            await self.temp_warn(ctx.channel, "Не нашёл тикет в БД (повторно).")
            return

        opener = await self.get_opener_from_ticketdata(ctx.guild, int(data.opener_id or 0))
        if not opener:
            await self.temp_warn(
                ctx.channel,
                f"Не смог получить участника opener_id={int(data.opener_id or 0)} (возможно вышел с сервера).",
            )
            return

        await ctx.channel.send(constants.ACCEPT_TEXT_1)
        await ctx.channel.send(constants.ACCEPT_TEXT_2)

        ok2, message = await self.try_accept_roles_and_nick(ctx.guild, opener)
        await self._logging.log_action(
            ctx.guild,
            ctx.channel.name,
            f"Application ACCEPT ({'OK' if ok2 else 'WARN'}): {message}",
            ctx.author,
        )
        if not ok2:
            await self.temp_warn(ctx.channel, message)

    async def handle_reject_command(self, ctx: commands.Context) -> None:
        await self.try_delete_command_message(ctx)

        ok, reason = self.command_allowed(ctx)
        if not ok:
            await self.temp_warn(ctx.channel, reason)
            return

        data = self._ticket_service.get_ticket_for_channel(ctx.channel)
        if not data:
            await self.temp_warn(ctx.channel, "Не нашёл тикет в БД (повторно).")
            return

        opener = await self.get_opener_from_ticketdata(ctx.guild, int(data.opener_id or 0))
        if not opener:
            await self.temp_warn(
                ctx.channel,
                f"Не смог получить участника opener_id={int(data.opener_id or 0)} (возможно вышел с сервера).",
            )
            return

        await ctx.channel.send(constants.DENY_TEXT)
        await self._logging.log_action(ctx.guild, ctx.channel.name, "Application DENY", ctx.author)

    async def accept_from_button(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        ticket_channel: discord.TextChannel,
    ) -> None:
        data = self._ticket_service.get_ticket_for_channel(ticket_channel)
        if not data or data.ticket_type != TicketType.APPLICATION:
            await ticket_channel.send("⚠️ Не смог применить ACCEPT: тикет не найден в БД или это не application.")
            return

        opener = await self.get_opener_from_ticketdata(guild, int(data.opener_id or 0))
        if not opener:
            await ticket_channel.send("⚠️ Не смог применить ACCEPT: участник не найден (возможно вышел).")
            return

        await ticket_channel.send(constants.ACCEPT_TEXT_1)
        await ticket_channel.send(constants.ACCEPT_TEXT_2)

        ok2, message = await self.try_accept_roles_and_nick(guild, opener)
        await self._logging.log_action(
            guild,
            ticket_channel.name,
            f"Application ACCEPT (BUTTON) ({'OK' if ok2 else 'WARN'}): {message}",
            moderator,
        )
        if not ok2:
            await ticket_channel.send(f"⚠️ {message}")

    async def reject_from_button(
        self,
        guild: discord.Guild,
        moderator: discord.Member,
        ticket_channel: discord.TextChannel,
    ) -> None:
        data = self._ticket_service.get_ticket_for_channel(ticket_channel)
        if not data or data.ticket_type != TicketType.APPLICATION:
            await ticket_channel.send("⚠️ Не смог применить DENY: тикет не найден в БД или это не application.")
            return

        await ticket_channel.send(constants.DENY_TEXT)
        await self._logging.log_action(guild, ticket_channel.name, "Application DENY (BUTTON)", moderator)
