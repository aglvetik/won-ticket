from __future__ import annotations

import discord

from app.config import constants
from app.discord_app.container import get_container
from app.utils.discord_utils import extract_ticket_name_from_dm_message


class DMReopenView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label=constants.DM_REOPEN_LABEL,
        style=discord.ButtonStyle.green,
        custom_id=constants.DM_REOPEN_CUSTOM_ID,
    )
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        preferred_ticket_name = None
        if interaction.message is not None:
            preferred_ticket_name = extract_ticket_name_from_dm_message(interaction.message)

        container = get_container(interaction.client)
        ok, message, channel = await container.reopen_service.reopen_from_dm(
            interaction,
            preferred_ticket_name=preferred_ticket_name,
        )
        if ok and channel:
            await interaction.response.send_message(message, ephemeral=True)
            return
        await interaction.response.send_message(message, ephemeral=True)
