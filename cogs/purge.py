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
        await ctx.interaction.response.defer()

        players_with_no_mogis = list(self.players.find({"mmr": 2000, "wins": 0, "losses": 0, "history": []}))
        self.players.update_many({"mmr": 8458}, {"$set": {"inactive": True}})

        for player in players_with_no_mogis:
            user = await self.bot.fetch_user(int(player["discord"]))
            await user.send(f"""
                You've registered for Mario Kart Lounge on Yuzu-Online as {player['name']}.
                However you haven't played any events yet. We try to keep the leaderboard clean from inactive players, 
                so therefore we marked your account as 'inactive'. \n
                If you don't want your account deleted, simply use the '/reactivate' slash command here or in the server. 
                That tells us that you still want to play."
                Otherwise, any accounts marked for deletion will be removed from the leaderboard and deleted after about 2 days. \n
                Don't worry, even if this happens, you can always just re-register in #lounge-information later.
            """)

        await ctx.respond(f"Marked {len(players_with_no_mogis)} accounts as inactive and DMed users.")

    @slash_command(name="reactivate")
    async def reactivate(self, ctx: ApplicationContext):
        self.players.update_one({"discord": ctx.interaction.user.id}, {"$unset": {"inactive": ""}})
        await ctx.respond("Successfully unmarked your account from being inactive!")
        
def setup(bot: commands.Bot):
    bot.add_cog(purge(bot))