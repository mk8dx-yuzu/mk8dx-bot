import os
import discord
import pymongo
from discord import slash_command, Option
from discord.ext import commands
from discord.utils import get


class admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient(
            f"mongodb://{os.getenv('MONGODB_HOST')}:27017/"
        )
        self.db = self.client["lounge"]
        self.players = self.db["players"]
        self.history = self.db["history"]

    @slash_command(
        name="edit",
        description="Edit a player's MMR. Wins/Losses and MMR History will be updated accordingly.",
    )
    async def edit(
        self,
        ctx: discord.ApplicationContext,
        name=Option(
            str,
            name="player",
            description="Which player's record to modify",
            required=True,
        ),
        new_mmr=Option(
            int,
            name="mmr",
            description="new MMR value",
            required=True,
        ),
    ):
        player = self.players.find_one({"name": name})
        delta = new_mmr - player["mmr"]
        win = delta >= 0
        self.history.update_one(
            {"player_id": f"{player['_id']}"}, {"$push": {f"history": delta}}
        )
        self.players.update_one(
            {"name": name}, {"$inc": {f"{'wins' if win else 'losses'}": 1}}
        )
        self.players.update_one({"name": name}, {"$set": {f"mmr": new_mmr}})
        await ctx.respond(f"Sucessfully edited {name}s MMR to {new_mmr}")

    @slash_command(name="remove", description="Remove a player from the leaderboard")
    async def remove(
        self,
        ctx: discord.ApplicationContext,
        player=Option(str, description="Name of the player"),
    ):
        user = self.players.find_one({"name": player})
        user_discord = user['discord']
        await ctx.guild.get_member(user_discord).remove_roles(get(ctx.guild.roles, name="Lounge Player"))
        self.players.delete_one({"name": player})
        self.history.delete_one({"player_id": user["_id"]})
        await ctx.respond(f"Successfully deleted {player}s player records")

def setup(bot: commands.Bot):
    bot.add_cog(admin(bot))
