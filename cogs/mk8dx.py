import os
import math
import discord
import pymongo
from pymongo import collection, database
from discord.ext import commands
from discord.utils import get
from discord import slash_command, Option

from cogs.extras.ranks import calcRank

from cogs.extras.utils import is_lounge_information_channel

class mk8dx(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.db: database.Database = self.bot.db
        self.players: collection.Collection = self.bot.players
        self.archived: collection.Collection = self.bot.archived

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
        history = self.players.find_one({"name": f"{name}"}).get(
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

        data = list(self.players.find().sort(sort, pymongo.DESCENDING))

        items_per_page = 10
        total_pages = int(math.ceil(len(data) / items_per_page))

        if page > total_pages or page < 1:
            page = total_pages

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
        name = Option(str, description="Name of the player", required=False),
    ):
        if not name:
            player: dict = self.players.find_one({"discord": ctx.author.mention.strip("<@!>")})
            if not player:
                return await ctx.respond("Couldn't find that player")
        else:
            player: dict = self.players.find_one({"name": name})
            if not player:
                player: dict = self.players.find_one({"discord": name.strip("<@!>")})
                if not player:
                    return await ctx.respond("Couldn't find that player")

        name = player['name']

        class MyView(discord.ui.View):
            def __init__(self, username):
                super().__init__(timeout=None)  # Timeout set to None to keep the view persistent
                self.add_item(discord.ui.Button(label="Visit Website", style=discord.ButtonStyle.link, url=f"https://mk8dx-yuzu.github.io/{username}"))


        embed = discord.Embed(
            title=f"{name}",
            description="",
            color=discord.Colour.blurple(),
        )
        for item in list(player.keys())[2:]:
            if item == "discord":
                embed.add_field(name=f"{item}", value=f"<@{player[item]}>")
                continue
            if item == "history":
                embed.add_field(name=f"{item}", value=f"{str(player[item])}")
                continue
            embed.add_field(name=f"{item}", value=f"{player[item]}")

        rank = calcRank(player["mmr"])

        embed.add_field(name="Rank", value=f"{rank}")
        embed.add_field(
            name="Winrate",
            value=f"{round(((player['wins']/(player['wins']+player['losses']) if (player['wins']+player['losses']) else 0)*100), 2)}%",
        )

        embed.set_author(
            name="Yuzu-Lounge",
            icon_url="https://raw.githubusercontent.com/mk8dx-yuzu/mk8dx-yuzu.github.io/main/public/favicon/android-icon-192x192.png",
        )
        rank.lower()
        embed.set_thumbnail(
            url=f"https://raw.githubusercontent.com/mk8dx-yuzu/mk8dx-yuzu.github.io/main/public/images/ranks/{rank.lower()}.webp"
        )

        await ctx.respond(f"# {name} - overview", embed=embed, view=MyView(name))

    @slash_command(name="register", description="Register for playing in the Lounge")
    @is_lounge_information_channel()
    async def register(
        self,
        ctx: discord.ApplicationContext
    ):
        tmp = self.players.find_one({"discord": f"{ctx.interaction.user.id}"})
        if tmp:
            return await ctx.respond("An entry for your discord account already exists. If you rejoined the server, ask an admin to give you the Lounge Roles back.", ephemeral=True)
        
        tmp = self.archived.find_one({"discord": f"{ctx.interaction.user.id}"})
        if tmp:
            return await ctx.respond("An entry for your discord account already exists but is archived. Ask a moderator to unarchive it.", ephemeral=True)

        username = ''.join(e for e in ctx.interaction.user.display_name.lower() if e.isalnum())
        if username == "":
            username = ctx.interaction.user.name.lower()

        if self.players.find_one({"name": username}):
            return await ctx.respond("This username is already taken. Try changing your server-nickname or ask a moderator.", ephemeral=True)
        
        role = get(ctx.guild.roles, name="Lounge Player")
        member: discord.Member = ctx.user
        if role in member.roles:
            return await ctx.respond("You already have the Lounge Player role even though you don't have a player role. Please ask a moderator.", ephemeral=True)
        try:
            self.players.insert_one(
                {"name": username, "mmr": 2000, "wins": 0, "losses": 0, "discord": str(member.id), "history": []},
            )
        except:
            return await ctx.respond("Some error occured creating your player record. Please ask a moderator.", ephemeral=True)
        await member.add_roles(get(ctx.guild.roles, name="Lounge Player"))
        await member.add_roles(get(ctx.guild.roles, name="Lounge - Silver"))
        await ctx.respond(f"{member.mention} is now registered for Lounge as {username}\n You can view your profile at https://mk8dx-yuzu.github.io/{username}", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(mk8dx(bot))
