from __future__ import annotations

import discord

from app.config import constants
from app.discord_app.container import get_container


class NotesDeleteView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label=constants.NOTES_DELETE_LABEL,
        style=discord.ButtonStyle.danger,
        custom_id=constants.NOTES_DELETE_CUSTOM_ID,
    )
    async def delete_notes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Ошибка: канал не найден.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Ошибка: сервер не найден.", ephemeral=True)
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(constants.ACCESS_DENIED_TEXT, ephemeral=True)
            return

        container = get_container(interaction.client)
        channel = interaction.channel
        if not container.ticket_service.is_support_member(interaction.user, channel):
            await interaction.response.send_message(constants.ACCESS_DENIED_TEXT, ephemeral=True)
            return

        if not channel.name.startswith("🔒-notes-"):
            await interaction.response.send_message(
                "Эта кнопка работает только в канале заметок.",
                ephemeral=True,
            )
            return

        await container.logging_service.log_action(guild, channel.name, "Notes Deleted", interaction.user)
        await interaction.response.send_message("Заметки удаляются ✅", ephemeral=True)
        await channel.delete()
