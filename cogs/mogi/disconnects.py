import discord
from discord import slash_command, SlashCommandGroup, ApplicationContext, Option
from discord.ext import commands

import pymongo
from pymongo import collection

from cogs.extras.utils import is_mogi_manager

class disconnects(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.players: collection.Collection = self.bot.players

    dc = SlashCommandGroup(name = "dc", description = "edit player disconnections records")

    @dc.command(
        name="add",
        description="Add a dc record to a player",
        player = Option(str, name="player", description="@ mention", required=True),
    )
    @is_mogi_manager()
    async def add(self, ctx: ApplicationContext, player = Option(str, name="player", description="@ mention", required=True)):
        await ctx.interaction.response.defer()
        player_data = self.players.find_one_and_update(
            {"discord": player.strip("<@!>")},
            {"$inc": {"dc": 1}},
            return_document=pymongo.ReturnDocument.AFTER
        )

        if player_data is None:
            return await ctx.respond("Player not found")

        await ctx.respond(f"Updated dc count for {player} to {player_data['dc']}")
        
    @dc.command(
        name="set",
        description="Set a dc record to a player",
        player = Option(str, name="player", description="@ mention", required=True),
        count = Option(int, name="count", description="new dc count", required=True),
    )
    @is_mogi_manager()
    async def set(self, ctx: ApplicationContext, player: str, count: int):
        await ctx.interaction.response.defer()
        player_data = self.players.find_one_and_update(
            {"discord": player.strip("<@!>")},
            {"$set": {"dc": count}},
            return_document=pymongo.ReturnDocument.AFTER
        )

        if player_data is None:
            return await ctx.respond("Player not found")

        await ctx.respond(f"Updated dc count for {player} to {player_data['dc']}")

def setup(bot: commands.Bot):
    bot.add_cog(disconnects(bot))