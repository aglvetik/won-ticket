from __future__ import annotations

import discord

from app.config import constants
from app.discord_app.container import get_container


async def _cleanup_confirmation_message(message: discord.Message) -> None:
    try:
        await message.delete()
    except Exception:
        try:
            await message.edit(view=None)
        except Exception:
            pass


class CloseTicketView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label=constants.TICKET_CLOSE_LABEL,
        style=discord.ButtonStyle.red,
        custom_id=constants.TICKET_CLOSE_CUSTOM_ID,
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        embed = discord.Embed(
            title="Подтверждение",
            description="Вы уверены, что хотите закрыть тикет?",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, view=CloseConfirmationView(), ephemeral=False)

    @discord.ui.button(
        label=constants.TICKET_STAFF_NOTES_LABEL,
        style=discord.ButtonStyle.secondary,
        custom_id=constants.TICKET_STAFF_NOTES_CUSTOM_ID,
    )
    async def staff_notes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await interaction.response.defer(ephemeral=True)

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.followup.send("Ошибка: канал не найден.", ephemeral=True)
            return

        if interaction.guild is None:
            await interaction.followup.send("Ошибка: сервер не найден.", ephemeral=True)
            return

        container = get_container(interaction.client)
        ok, message = await container.ticket_service.create_staff_notes_channel(interaction, interaction.channel)
        await interaction.followup.send(message, ephemeral=True)


class CloseConfirmationView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label=constants.TICKET_CLOSE_CONFIRM_LABEL,
        style=discord.ButtonStyle.red,
        custom_id=constants.TICKET_CLOSE_CONFIRM_CUSTOM_ID,
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await interaction.response.defer()
        confirm_message = interaction.message

        if not isinstance(interaction.channel, discord.TextChannel):
            await _cleanup_confirmation_message(confirm_message)
            await interaction.followup.send("Ошибка: канал не найден.", ephemeral=True)
            return

        if interaction.guild is None:
            await _cleanup_confirmation_message(confirm_message)
            await interaction.followup.send("Ошибка: сервер не найден.", ephemeral=True)
            return

        container = get_container(interaction.client)
        ok, message = await container.ticket_service.close_ticket_channel(interaction, interaction.channel)
        if not ok:
            await _cleanup_confirmation_message(confirm_message)
            await interaction.followup.send(message, ephemeral=True)
            return

        mod_embed = discord.Embed(
            title="Тикет закрыт",
            description="Действия для модератора:",
            color=discord.Color.dark_gray(),
        )
        await interaction.channel.send(embed=mod_embed, view=AfterCloseView())

        await interaction.followup.send("Тикет закрыт ✅", ephemeral=True)
        await _cleanup_confirmation_message(confirm_message)

    @discord.ui.button(
        label=constants.TICKET_CLOSE_CANCEL_LABEL,
        style=discord.ButtonStyle.gray,
        custom_id=constants.TICKET_CLOSE_CANCEL_CUSTOM_ID,
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await interaction.response.defer(ephemeral=True)
        await _cleanup_confirmation_message(interaction.message)
        await interaction.followup.send("Закрытие тикета отменено ✅", ephemeral=True)


from app.discord_app.views.after_close import AfterCloseView
