import os
import discord
from discord.ext import commands
from discord import slash_command
from discord import Option
import pymongo

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient(f"mongodb://{os.getenv("MONGODB_HOST")}:27017/")
        self.db = self.client["lounge"]
        self.collection = self.db["players"]

    @slash_command(name="add", description="(other stats can be added/modified trough the /edit method)")
    async def add(
        self, 
        ctx: discord.ApplicationContext, 
        name = Option(
            str,
            name="player", 
            description="What's the name of the new player?", 
            required=True,
        ),
        mmr = Option(
            int,
            name="mmr", 
            description="starting MMR", 
            required=False,
            default=None
        ),
        wins = Option(
            int,
            name="wins", 
            description="amount of won events", 
            required=False,
            default=None
        ),
        losses = Option(
            int,
            name="losses", 
            description="amount of lost events", 
            required=False,
            default=None
        ),
        ):
        self.collection.insert_one({
            "name": name,
            "mmr": mmr,
            "wins": wins,
            "losses": losses
        })
        await ctx.respond(f"Sucessfully created user {name}")

    @slash_command(name="edit", description="Edit a player's data. Will add record to player's mmr history (in the future)")
    async def edit(
        self, 
        ctx: discord.ApplicationContext, 
        player = Option(
            str,
            name="player", 
            description="Which player's data to modify", 
            required=True,
        ),
        stat = Option(
            str,
            name="stat", 
            description="Which stat to change", 
            required=True,
            choices=[
                "name",
                "mmr",
                "wins",
                "losses"
            ],
        ),
        new = Option(
            name="newvalue", 
            description="The new value to overwrite", 
            required=True,
        )
        ):
        if (stat != 'name') and (not new.isnumeric()):
            return await ctx.respond("invalid input")
        if stat != "name":
            new = int(new)
        self.collection.update_one({"name": player}, {"$set": {f"{stat}": f"{new}"}})
        await ctx.respond(f"Sucessfully edited {player}s {stat} to {new}")

    @slash_command(name="remove", description="Remove a player from the leaderboard")
    async def remove(self, ctx: discord.ApplicationContext, player=Option(str, description="Name of the player")):
        self.collection.delete_one({"name": player})
        await ctx.respond(f"Successfully deleted {player}s player records")

def setup(bot: commands.Bot):
    bot.add_cog(admin(bot))