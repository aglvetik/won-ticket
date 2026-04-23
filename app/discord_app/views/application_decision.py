from __future__ import annotations

import discord

from app.config import constants
from app.discord_app.container import get_container


class ApplicationDecisionView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    def _disable_all(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(
        label=constants.APP_DECISION_ACCEPT_LABEL,
        style=discord.ButtonStyle.success,
        custom_id=constants.APP_DECISION_ACCEPT_CUSTOM_ID,
    )
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Ошибка контекста.", ephemeral=True)
            return

        container = get_container(interaction.client)
        if not container.member_service.has_application_mod_role(interaction.user):
            await interaction.response.send_message(
                "Нет доступа (нужна роль модератора заявок).",
                ephemeral=True,
            )
            return

        if interaction.message is None:
            await interaction.response.send_message("Канал тикета не найден.", ephemeral=True)
            return

        ticket_channel = await container.google_forms_service.resolve_ticket_channel_from_admin_message(
            interaction.guild,
            interaction.message,
        )
        if not ticket_channel:
            await interaction.response.send_message("Канал тикета не найден.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await container.member_service.accept_from_button(interaction.guild, interaction.user, ticket_channel)

        self._disable_all()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.followup.send("Готово: игрок принят ✅", ephemeral=True)

    @discord.ui.button(
        label=constants.APP_DECISION_REJECT_LABEL,
        style=discord.ButtonStyle.danger,
        custom_id=constants.APP_DECISION_REJECT_CUSTOM_ID,
    )
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Ошибка контекста.", ephemeral=True)
            return

        container = get_container(interaction.client)
        if not container.member_service.has_application_mod_role(interaction.user):
            await interaction.response.send_message(
                "Нет доступа (нужна роль модератора заявок).",
                ephemeral=True,
            )
            return

        if interaction.message is None:
            await interaction.response.send_message("Канал тикета не найден.", ephemeral=True)
            return

        ticket_channel = await container.google_forms_service.resolve_ticket_channel_from_admin_message(
            interaction.guild,
            interaction.message,
        )
        if not ticket_channel:
            await interaction.response.send_message("Канал тикета не найден.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await container.member_service.reject_from_button(interaction.guild, interaction.user, ticket_channel)

        self._disable_all()
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.followup.send("Готово: игрок отклонён ❌", ephemeral=True)
