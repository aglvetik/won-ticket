from __future__ import annotations

import discord
from discord.ext import commands

from app.config import constants


class PanelService:
    def build_command_panel_embed(self) -> discord.Embed:
        return discord.Embed(
            title=constants.PANEL_COMMAND_EMBED_TITLE,
            description=constants.PANEL_COMMAND_EMBED_DESCRIPTION,
            color=discord.Color.blue(),
        )

    def build_startup_panel_embed(self) -> discord.Embed:
        return discord.Embed(
            title=constants.PANEL_EMBED_TITLE,
            description=constants.PANEL_EMBED_DESCRIPTION,
            color=discord.Color.blue(),
        )

    async def send_panel_command(self, ctx: commands.Context) -> None:
        from app.discord_app.views.panel import MainPanelView

        if ctx.channel.id != constants.ALLOWED_CHANNEL_ID:
            return
        if not any(role.id in constants.ALLOWED_ROLES for role in ctx.author.roles):
            return

        await ctx.send(embed=self.build_command_panel_embed(), view=MainPanelView())

    async def republish_panel(self, bot: discord.Client) -> None:
        from app.discord_app.views.panel import MainPanelView

        panel_channel = bot.get_channel(constants.TICKET_PANEL_CHANNEL_ID)
        if not isinstance(panel_channel, discord.TextChannel):
            return

        try:
            async for message in panel_channel.history(limit=50):
                if message.author == bot.user and message.embeds:
                    await message.delete()
        except Exception:
            pass

        await panel_channel.send(embed=self.build_startup_panel_embed(), view=MainPanelView())
