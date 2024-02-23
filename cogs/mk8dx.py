import os
import math
import discord
import pymongo
from discord.ext import commands
from discord import slash_command
from discord import Option

def calcRank(mmr):
        ranks = [
            {"name": "Bronze", "range": (0, 1499)},
            {"name": "Silver", "range": (1400, 2999)},
            {"name": "Gold", "range": (3000, 5099)},
            {"name": "Platinum", "range": (5100, 6999)},
            {"name": "Diamond", "range": (7000, 9499)},
            {"name": "Master", "range": (9500, 99999)}
        ]
        for range_info in ranks:
            start, end = range_info["range"]
            if start <= mmr <= end:
                return range_info['name']
        return "---"

class mk8dx(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient(f"mongodb://{os.getenv('MONGODB_HOST')}:27017/")
        self.db = self.client["lounge"]
        self.collection = self.db["players"]

    def cog_unload(self):
        self.client.close()

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.errors.CommandOnCooldown): 
            await ctx.respond("This command is on cooldown for {:.2f} seconds.".format(ctx.command.get_cooldown_retry_after(ctx)))

    @slash_command(name="mmr", description="Retrieve the MMR of a player")
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def mmr(self, ctx: discord.ApplicationContext, name: str):
        player = self.collection.find_one({"name": name})
        if player:
            await ctx.respond(f"{name}s MMR is {player['mmr']}")
        else:
            await ctx.respond(f"Couldn't find {name}s MMR")

    @slash_command(name="leaderboard", description="Show the leaderboard; sort options: mmr | wins | losses | name")
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def leaderboard(
        self, 
        ctx: discord.ApplicationContext, 
        sort = Option(
            name="sort", 
            description="options: mmr | wins | losses | name", 
            required=False, 
            default='mmr',
        ),
        page = Option(
            int,
            name="page", 
            description="which page number to show. default: 1", 
            required=False, 
            default=1,
        )
        ):
        valid_sorts = ["mmr", "wins", "losses", "name"]
        if sort not in valid_sorts:
            await ctx.respond(f"Invalid sort option. Please choose from: {', '.join(valid_sorts)}", ephemeral=True)
            return

        data = self.collection.find().sort(sort, pymongo.DESCENDING)
        data = list(data)

        items_per_page = 10
        total_pages = int(math.ceil(len(data) / items_per_page))


        if page > total_pages or page < 1:
            raise ValueError("Invalid page number. Please provide a number between 1 and {}".format(total_pages))

        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page

        table_string = ""
        table_string += "```\n"
        table_string += " | Name            |   Rank   |  MMR  | Wins | Losses | Winrate (%) |\n"
        table_string += " |-----------------|----------|-------|------|--------|-------------|\n"
        for player in data[start_index:end_index]:
            games = player['wins']+player['losses']
            table_string += f" | {player['name']:<15} | {calcRank(player['mmr']):>8} | {player['mmr']:>5} | {player['wins']:>4} | {player['losses']:>6} | {(player['wins']/games if games else 0)*100:>11} |\n"
        table_string += f"Page {page}"
        table_string += "```"

        await ctx.respond(table_string)

    @slash_command(name="player", description="Show a player and their stats")
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def player(
            self, 
            ctx: discord.ApplicationContext, 
            name = Option(str, description="Name of the player")
        ):
        player: dict = self.collection.find_one({"name": name})
        if not player:
            return await ctx.respond("Couldn't find that player")
        player_str = f"## {name} \n"
        player_str += "```\n"
        for item in list(player.keys())[2:]:
            player_str += f"{item}: {player[item]} \n"
        games = (player['wins']+player['losses'])
        player_str += f"Winrate: {(player['wins']/games if games else 0)*100}% \n"
        player_str += "```"
        await ctx.respond(player_str)

    @slash_command(name="register", description="Register for playing in the Lounge")
    async def register(interaction: discord.Interaction, ctx: discord.ApplicationContext):
        role = ctx.guild.get_role(1181313896695480321)
        print(role)
        print("ok")
        member = ctx.user
        if role in member.roles:
            await ctx.respond("You already have the Lounge Player role")
            return
        print("wow")
        await member.add_roles(role)
        await ctx.respond(f"{member.name} is now registered for Lounge")
        print("dones")


def setup(bot: commands.Bot):
    bot.add_cog(mk8dx(bot))