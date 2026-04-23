from __future__ import annotations

import discord

from app.config import constants
from app.discord_app.container import get_container
from app.domain.enums import TicketType


class MainPanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label=constants.MAIN_PANEL_APPLY_LABEL,
        style=discord.ButtonStyle.green,
        custom_id=constants.MAIN_PANEL_APPLY_CUSTOM_ID,
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        container = get_container(interaction.client)
        await container.ticket_service.create_ticket(interaction, TicketType.APPLICATION)

    @discord.ui.button(
        label=constants.MAIN_PANEL_QUESTION_LABEL,
        style=discord.ButtonStyle.blurple,
        custom_id=constants.MAIN_PANEL_QUESTION_CUSTOM_ID,
    )
    async def question(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        container = get_container(interaction.client)
        await container.ticket_service.create_ticket(interaction, TicketType.OTHER)

    @discord.ui.button(
        label=constants.MAIN_PANEL_IDEA_LABEL,
        style=discord.ButtonStyle.secondary,
        custom_id=constants.MAIN_PANEL_IDEA_CUSTOM_ID,
    )
    async def idea(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        container = get_container(interaction.client)
        await container.ticket_service.create_ticket(interaction, TicketType.IDEA)
