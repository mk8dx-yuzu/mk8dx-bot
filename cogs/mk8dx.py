import discord
import pymongo
from discord.ext import commands
from discord import slash_command
from discord import Option

class mk8dx(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient("mongodb://raspberrypi:27017/")
        self.db = self.client["admin"]
        self.collection = self.db["mk8dx"]

    def cog_unload(self):
        self.client.close()

    """ def calcRank(mmr):
        ranks = [
            {"name": "Bronze", "range": (0, 1400)},
            {"name": "Silver", "range": (1401, 2900)},
            {"name": "High", "range": (2901, 5000)},
            {"name": "High", "range": (5001, 6900)},
            {"name": "High", "range": (6901, 9400)},
            {"name": "High", "range": (51, 100)}
        ]
        for range_info in ranks:
            start, end = range_info["range"]
            if start <= mmr <= end:
                return f"{mmr} falls in the {range_info['name']} range"
        return "Out of range" """

    @slash_command(name="mmr", description="Retrieve the MMR of a player")
    async def mk8dx(self, ctx: discord.ApplicationContext, name: str):
        player = self.collection.find_one({"name": name})
        if player:
            await ctx.respond(f"{name}s MMR is {player['mmr']}")
        else:
            await ctx.respond(f"Couldn't find {name}s MMR")

    @slash_command(name="leaderboard", description="Show the leaderboard; sort options: mmr | wins | losses | name")
    async def leaderboard(
        self, 
        ctx: discord.ApplicationContext, 
        sort = Option(
            name="sort", 
            description="options: mmr | wins | losses | name", 
            required=False, 
            default='mmr',
        )):
        valid_sorts = ["mmr", "wins", "losses", "name"]
        if sort not in valid_sorts:
            await ctx.respond(f"Invalid sort option. Please choose from: {', '.join(valid_sorts)}", ephemeral=True)
            return

        data = self.collection.find().sort(sort, pymongo.DESCENDING)

        table_string = ""
        table_string += "```\n"
        table_string += " | Name            | Rank  |  MMR  | Wins | Losses | Winrate (%) |\n"
        table_string += " |-----------------|-------|-------|------|--------|-------------|\n"
        for player in data:
            games = player['wins']+player['losses']
            table_string += f" | {player['name']:<15} | {"---"} | {player['mmr']:>5} | {player['wins']:>4} | {player['losses']:>6} | {(player['wins']/games if games else 0)*100:>11} |\n"
        table_string += "```" #calcRank(player['mmr']):>5

        await ctx.respond(table_string)

    @slash_command(name="player", description="Show a player and their stats")
    async def player(self, ctx: discord.ApplicationContext, name: str):
        player: dict = self.collection.find_one({"name": name})
        if not player:
            return ctx.respond("Couldn't find that player")
        player_str = ""
        for item in list(player.keys())[1:]:
            player_str += f"{item}: {player[item]} \n"
        games = (player['wins']+player['losses'])
        player_str += f"Winrate: {(player['wins']/games if games else 0)*100}% \n"
        await ctx.respond(player_str)

    @commands.command()
    async def testing(self, ctx: commands.Context):
        await ctx.send("test")
        #documents = collection.find()
        #for doc in documents:
        #    print(doc)

        # Example: Insert a new document
        #new_document = {"name": "New Item", "value": 10}
        #collection.insert_one(new_document)

        # Example: Update a document
        #collection.update_one({"name": "Existing Item"}, {"$set": {"value": 20}})

        # Example: Delete a document
        #collection.delete_one({"name": "Item to Delete"})

    # admin commands
    @slash_command(name="add", description="(other stats can be added/modified trough the /edit method)")
    async def add(
        self, 
        ctx: discord.ApplicationContext, 
        name = Option(
            name="player", 
            description="What's the name of the new player?", 
            required=True,
        ),
        mmr = Option(
            name="mmr", 
            description="starting MMR", 
            required=False,
            default=None
        ),
        wins = Option(
            name="wins", 
            description="amount of won events", 
            required=False,
            default=None
        ),
        losses = Option(
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

    @slash_command(name="edit")
    async def edit(
        self, 
        ctx: discord.ApplicationContext, 
        player = Option(
            name="player", 
            description="Which player's data to modify", 
            required=True,
        ),
        stat = Option(
            name="stat", 
            description="Which stat to change", 
            required=True,
        ),
        new = Option(
            name="newvalue", 
            description="The new value to overwrite", 
            required=True,
        )
        ):
        self.collection.update_one({"name": player}, {"$set": {f"{stat}": f"{new}"}})
        await ctx.respond(f"Sucessfully edited {player}s {stat} to {new}")

def setup(bot: commands.Bot):
    bot.add_cog(mk8dx(bot))