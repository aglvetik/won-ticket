from __future__ import annotations

import discord

from app.config import constants
from app.discord_app.container import get_container


class AfterCloseView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label=constants.TICKET_DELETE_LABEL,
        style=discord.ButtonStyle.danger,
        custom_id=constants.TICKET_DELETE_CUSTOM_ID,
    )
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Ошибка: канал не найден.", ephemeral=True)
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(constants.ACCESS_DENIED_TEXT, ephemeral=True)
            return

        container = get_container(interaction.client)
        channel = interaction.channel
        if not container.ticket_service.is_support_member(interaction.user, channel):
            await interaction.response.send_message(constants.ACCESS_DENIED_TEXT, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        ok, message = await container.transcript_service.auto_save_transcript(interaction, channel)
        if ok:
            await container.logging_service.log_action(
                interaction.guild,
                channel.name,
                "Transcript Auto Saved (before delete)",
                interaction.user,
            )
        else:
            await container.logging_service.log_action(
                interaction.guild,
                channel.name,
                f"Transcript Auto Save FAILED: {message}",
                interaction.user,
            )

        await container.logging_service.log_action(interaction.guild, channel.name, "Deleted", interaction.user)
        await interaction.followup.send("Тикет удаляется ✅", ephemeral=True)
        await channel.delete()

    @discord.ui.button(
        label=constants.TICKET_REOPEN_MOD_LABEL,
        style=discord.ButtonStyle.success,
        custom_id=constants.TICKET_REOPEN_MOD_CUSTOM_ID,
    )
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Ошибка: канал не найден.", ephemeral=True)
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(constants.ACCESS_DENIED_TEXT, ephemeral=True)
            return

        container = get_container(interaction.client)
        channel = interaction.channel
        if not container.ticket_service.is_support_member(interaction.user, channel):
            await interaction.response.send_message(constants.ACCESS_DENIED_TEXT, ephemeral=True)
            return

        ok, message = await container.reopen_service.reopen_closed_channel_by_moderator(interaction, channel)
        if ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
        await interaction.response.send_message(message, ephemeral=True)
