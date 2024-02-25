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
        {"name": "Master", "range": (9500, 99999)},
    ]
    for range_info in ranks:
        start, end = range_info["range"]
        if start <= mmr <= end:
            return range_info["name"]
    return "---"


class mk8dx(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient(
            f"mongodb://{os.getenv('MONGODB_HOST')}:27017/"
        )
        self.db = self.client["lounge"]
        self.players = self.db["players"]
        self.history = self.db["history"]

    def cog_unload(self):
        self.client.close()

    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.respond(
                "This command is on cooldown for {:.2f} seconds.".format(
                    ctx.command.get_cooldown_retry_after(ctx)
                )
            )

    @slash_command(name="mmr", description="Retrieve the MMR history of a player")
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def mmr(self, ctx: discord.ApplicationContext, name: str):
        player = self.players.find_one({"name": name})
        history = self.history.find_one({"player_id": f"{player['_id']}"}).get(
            "history"
        )
        if player["mmr"]:
            await ctx.respond(
                f"""
                # {name}
                current MMR: {player['mmr']}
                History: {history}
            """
            )
        else:
            await ctx.respond(f"Couldn't find {name}s MMR")

    @slash_command(
        name="leaderboard",
        description="Show the leaderboard; sort options: mmr | wins | losses | name",
    )
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def leaderboard(
        self,
        ctx: discord.ApplicationContext,
        sort=Option(
            name="sort",
            description="options: mmr | wins | losses | name",
            required=False,
            default="mmr",
        ),
        page=Option(
            int,
            name="page",
            description="which page number to show. default: 1",
            required=False,
            default=1,
        ),
    ):
        valid_sorts = ["mmr", "wins", "losses", "name"]
        if sort not in valid_sorts:
            await ctx.respond(
                f"Invalid sort option. Please choose from: {', '.join(valid_sorts)}",
                ephemeral=True,
            )
            return

        data = self.players.find().sort(sort, pymongo.DESCENDING)
        data = list(data)

        items_per_page = 10
        total_pages = int(math.ceil(len(data) / items_per_page))

        if page > total_pages or page < 1:
            raise ValueError(
                "Invalid page number. Please provide a number between 1 and {}".format(
                    total_pages
                )
            )

        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page

        table_string = ""
        table_string += "```\n"
        table_string += " |  #  | Name            |   Rank   |  MMR  | Wins | Losses | Winrate (%) |\n"
        table_string += " |-----|-----------------|----------|-------|------|--------|-------------|\n"
        for player in data[start_index:end_index]:
            name, mmr, wins, losses = (
                player["name"],
                player["mmr"],
                player["wins"],
                player["losses"]
            )
            index = data.index(player) + 1
            rank = calcRank(player["mmr"])
            games = player["wins"] + player["losses"]
            winrate = round(((player["wins"] / games if games else 0) * 100), 2)

            table_string += f" | {index:<3} | {name:<15} | {rank:>8} | {mmr:>5} | {wins:>4} | {losses:>6} | {winrate:>11} |\n"
        table_string += f"Page {page}"
        table_string += "```"

        await ctx.respond(table_string)

    @slash_command(name="player", description="Show a player and their stats")
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def player(
        self,
        ctx: discord.ApplicationContext,
        name=Option(str, description="Name of the player"),
    ):
        player: dict = self.players.find_one({"name": name})
        if not player:
            return await ctx.respond("Couldn't find that player")

        embed = discord.Embed(
            title=f"{name}",
            description="",
            color=discord.Colour.blurple(),
        )
        for item in list(player.keys())[2:]:
            embed.add_field(name=f"{item}", value=f"{player[item]}")

        rank = calcRank(player["mmr"])

        embed.add_field(name="Rank", value=f"{rank}")
        embed.add_field(
            name="Winrate",
            value=f"{(player['wins']/(player['wins']+player['losses']) if (player['wins']+player['losses']) else 0)*100}%",
        )

        embed.set_author(
            name="Yuzu-Lounge",
            icon_url="https://raw.githubusercontent.com/mk8dx-yuzu/mk8dx-yuzu.github.io/main/favicon/android-icon-192x192.png",
        )
        embed.set_thumbnail(
            url=f"https://raw.githubusercontent.com/mk8dx-yuzu/mk8dx-yuzu.github.io/main/images/ranks/{rank.lower()}.webp"
        )

        await ctx.respond(f"# {name} - overview", embed=embed)

    @slash_command(name="register", description="Register for playing in the Lounge")
    async def register(
        self,
        ctx: discord.ApplicationContext,
        username=Option(
            str,
            description="Your username to show up on the leaderboard",
            required=True,
        ),
    ):
        role = ctx.guild.get_role(1181313896695480321)
        member = ctx.user
        if role in member.roles:
            await ctx.respond("You already have the Lounge Player role")
            return
        await member.add_roles(role)
        player_id = self.players.insert_one(
            {"name": username, "mmr": 2000, "wins": 0, "losses": 0}
        ).inserted_id
        self.history.insert_one({player_id: player_id, "history": []})
        await ctx.respond(f"{member.name} is now registered for Lounge as {username}")


def setup(bot: commands.Bot):
    bot.add_cog(mk8dx(bot))
