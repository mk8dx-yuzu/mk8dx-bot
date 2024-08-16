import discord
from discord import ApplicationContext, slash_command, Option
from discord.ext import commands

import pymongo
from pymongo import collection, database

from cogs.extras.utils import is_admin

class purge(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.players: collection.Collection = self.bot.players

    @slash_command(name="purge_leaderboard", description="flag accounts with no mogis played for deletion, dm them with an option to prevent")
    @is_admin()
    async def purge_leaderboard(self, ctx: ApplicationContext):
        players_with_no_mogis = self.players.find({"mmr": 2000, "wins": 0, "losses": 0, "history": []})
        await ctx.respond(player['name'] for player in list(players_with_no_mogis))
        
def setup(bot: commands.Bot):
    bot.add_cog(purge(bot))