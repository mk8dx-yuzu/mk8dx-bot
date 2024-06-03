import discord, math
from discord import Option, ApplicationContext, slash_command, Interaction
from discord.ext import commands
from discord.utils import get
from discord.ui import View, Modal, InputText

import pymongo
from pymongo import database, collection

import trueskill
from trueskill import Rating, rate, global_env

import pandas as pd
import dataframe_image as dfi
from matplotlib import colors
from io import BytesIO

import cogs.extras.mmr_algorithm as mmr_alg
from cogs.extras.ranks import calcRank

class calc(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.db: database.Database = self.bot.db
        self.players: collection.Collection = self.bot.players

    @slash_command(name="points", description="Use after a mogi - input player points", guild_only=True)
    async def points(self, ctx: ApplicationContext):
        if not self.bot.mogi["running"]:
            return await ctx.respond("No running mogi")
        if self.bot.mogi["points_user"] and self.bot.mogi["points_user"] != ctx.interaction.user.id:
            return await ctx.respond("Someone is already doing points", ephemeral=True)

        self.bot.mogi["points_user"] = ctx.interaction.user.id

        class MogiModal(discord.ui.Modal):
            def __init__(self, mogi, db, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.db = db
                self.mogi = mogi

                count = 0
                for player in self.mogi["players"]:
                    if player not in self.mogi["calc"] and count < 4:
                        mentioned_user = db["players"].find_one(
                            {"discord": player.strip("<@!>")}
                        )["name"]
                        self.add_item(InputText(label = mentioned_user))
                        self.mogi["calc"].append(player)
                        count += 1

            async def callback(
                self: Modal = Modal,
                interaction: Interaction = Interaction,
                mogi=self.bot.mogi,
            ):
                for i in range(0, len(self.children)):
                    mogi["input_points"].append(int(self.children[i].value))
                    mogi["point_count"] += 1
                        
                if mogi["format"] == "ffa":
                    for i in range(0, len(self.children)):
                        mogi["points"].append([int(self.children[i].value)])
                else:
                    size = int(mogi["format"][0])
                    if len(mogi["input_points"]) % size == 0:
                        for i in range(0, len(mogi["input_points"]), size):
                            mogi["points"].append(mogi["input_points"][i : i + size])
                        mogi["input_points"].clear()

                await interaction.response.send_message(
                    """
                    Points have been collected. 
                    Use this command again until all players' points have been collected.
                    Then use /calc to calculate results
                """,
                    ephemeral=True,
                )

        if len(self.bot.mogi["players"]) > len(self.bot.mogi["calc"]):
            modal = MogiModal(
                mogi=self.bot.mogi, db=self.db, title="Input player points after match"
            )
            await ctx.send_modal(modal)
        else:
            return await ctx.respond("Already got all calcs")
        
    @slash_command(
        name="calc", description="Use after using /points to calculate new mmr", guild_only=True
    )
    async def calc(self, ctx: discord.ApplicationContext):
        if not len(self.bot.mogi["calc"]):
            return ctx.respond(
                "There doesn't seem to be data to make calculations with"
            )

        global_env()
        trueskill.setup(
            mu=2000,
            sigma=100,
            beta=9000,
            tau=950,
            draw_probability=0.01,
            backend=None,
            env=None,
        )

        new_algo_players = []

        calc_teams = []
        for team in self.bot.mogi["teams"]:
            calc_team = []
            for player in team:
                mmr = self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
                calc_team.append(Rating(mmr, 100))
                new_algo_players.append(mmr)
            calc_teams.append(calc_team)
        scores = []
        for team_point_arr in self.bot.mogi["points"]:
            scores.append([sum(team_point_arr)])
        
        ranks_dict = {}
        placements = []
        for i, score in enumerate(sorted(scores, reverse=True)):
            ranks_dict[score[0]] = i + 1
        for score in scores:
            placements.append(ranks_dict[score[0]])
        self.bot.mogi["placements"] = placements

        new_ratings = rate(calc_teams, placements)

        form = self.bot.mogi['format'][0]
        new_new_ratings = mmr_alg.calculate_mmr(new_algo_players, placements, int(form) if form != "f" else 1 )

        for team in new_ratings:
            self.bot.mogi["results"].append([round(player.mu) for player in team])

        debug_string = "# Debug:\n Points:\n"
        for scoring in self.bot.mogi['points']:
            debug_string += f"{scoring}\n"
        debug_string += "\n Current MMR:"
        for team in calc_teams:
            debug_string += f"{team}\n"
        debug_string += "\n New MMR:"
        for new in self.bot.mogi["results"]:
            debug_string+= f"{new}\n"

        await ctx.respond(
            f'Data has been processed and new mmr has been calculated. Use /table to view and /apply to apply the new mmr \n {calc_teams} {placements} \n {debug_string}',
            ephemeral=True,
        )

    @slash_command(name="table", description="Use after a /calc to view the results", guild_only=True)
    async def table(self, ctx: discord.ApplicationContext):
        players = [
            self.players.find_one({"discord": player.strip("<@!>")})["name"]
            for player in self.bot.mogi["players"]
        ]
        current_mmr = [
            round(self.players.find_one({"discord": player.strip("<@!>")})["mmr"])
            for player in self.bot.mogi["players"]
        ]
        new_mmr = [val for sublist in self.bot.mogi["results"] for val in sublist]

        data = {
            "Player": players,
            "MMR": current_mmr,
            "Change": [
                round(new_mmr[i] - current_mmr[i]) for i in range(0, len(players))
            ],
            "New MMR": new_mmr,
        }
        df = pd.DataFrame(data).set_index("Player")
        df = df.sort_values(by="Change", ascending=False)
        buffer = BytesIO()
        dfi.export(
            df.style.set_table_styles(
                [
                    {
                        "selector": "tr:nth-child(even)",
                        "props": [("background-color", "#363f4f"), ("color", "white")],
                    },
                    {
                        "selector": "tr:nth-child(odd)",
                        "props": [("background-color", "#1d2735"), ("color", "white")],
                    },
                ]
            ).background_gradient(
                cmap=colors.LinearSegmentedColormap.from_list(
                    "", ["red", "red", "white", "green", "green"]
                ),
                low=0.3,
                high=0.2,
                subset=["Change"],
            ),
            buffer,
        )

        buffer.seek(0)
        file = discord.File(buffer, filename="table.png")
        await ctx.respond(content="Here's the table:", file=file)

    @slash_command(name="apply", description="Use after a /calc to apply new mmr", guild_only=True)
    async def apply(self, ctx: ApplicationContext):
        await ctx.response.defer()
        players = self.bot.mogi["players"]
        current_mmr = [
            self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
            for player in self.bot.mogi["players"]
        ]
        new_mmr = [element for sublist in self.bot.mogi["results"] for element in sublist]
        deltas = [new_mmr[i] - current_mmr[i] for i in range(0, len(players))]

        for i, player in enumerate(players):
            if player in self.bot.mogi["subs"] and deltas[i] < 0:
                await ctx.send(f"Excluded {self.bot.get_user(int(player.strip('<@!>'))).mention} because they subbed")
                continue
            self.players.update_one(
                {"discord": player.strip("<@!>")}, 
                {"$set": {
                    "mmr": new_mmr[i]
                      if new_mmr[i] > 1 or get(ctx.guild.roles, name="WoodLover") in get(ctx.guild.members, id=int(player.strip("<@!>"))).roles 
                      else 1
                    }
                }
            )
            self.players.update_one(
                {"discord": player.strip("<@!>")},
                {"$push": {"history": deltas[i]}},
                False,
            )
            self.players.update_one(
                {"discord": player.strip("<@!>")},
                {
                    "$set": {
                        "history": self.players.find_one(
                            {"discord": player.strip("<@!>")}
                        )["history"][-10:]
                    }
                },
            )
            self.players.update_one(
                {"discord": player.strip("<@!>")},
                {"$inc": {"losses" if deltas[i] < 0 else "wins": 1}},
            )
            current_rank = calcRank(current_mmr[i])
            new_rank = calcRank(new_mmr[i])
            if current_rank != new_rank:
                await ctx.send(f"{self.bot.get_user(int(player.strip('<@!>'))).mention} is now in {new_rank}")

        self.bot.mogi["locked"] = False

        await ctx.respond("Applied MMR changes ✅")


    @slash_command(name="calc_test", guild_only=True)
    async def calc_test(
        self,
        ctx: ApplicationContext,
        format = Option(str, choices = ["1v1", "2v2", "3v3", "4v4", "5v5", "6v6"]),
        players = Option(str, description = "by lounge username"),
        placements = Option(str, description = "array"),
        upscale = Option(str, description = "multiply gains by 1.3x", required = True, choices = ["y", "n"])
    ):
        await ctx.response.defer()

        all_players = players.split(", ")
        player_mmrs = []
        for player in all_players:
            player_mmrs.append(self.players.find_one({"name": player})['mmr'])

        deltas = mmr_alg.calculate_mmr(player_mmrs, placements.split(", "), int(format[0]))
        if upscale == "y":
            deltas = [math.ceil(1.3 * score) if score > 0 else score for score in deltas]

        await ctx.send(f"{player_mmrs}; {[int(spot) for spot in placements.split(', ')]}; {int(format[0])}")
        await ctx.send(f"{deltas}")

        deltas = [element for element in deltas for _ in range(int(format[0]))]

        data = {
            "Player": all_players,
            "MMR": player_mmrs,
            "Change": deltas,
            "New MMR": [player_mmrs[i] + deltas[i] for i in range(0, len(all_players))],
        }
        df = pd.DataFrame(data).set_index("Player")
        df = df.sort_values(by="Change", ascending=False)
        buffer = BytesIO()
        dfi.export(
            df.style.set_table_styles(
                [
                    {
                        "selector": "tr:nth-child(even)",
                        "props": [("background-color", "#363f4f"), ("color", "white")],
                    },
                    {
                        "selector": "tr:nth-child(odd)",
                        "props": [("background-color", "#1d2735"), ("color", "white")],
                    },
                ]
            ).background_gradient(
                cmap=colors.LinearSegmentedColormap.from_list(
                    "", ["red", "red", "white", "green", "green"]
                ),
                low=0.3,
                high=0.2,
                subset=["Change"],
            ),
            buffer,
        )

        buffer.seek(0)
        file = discord.File(buffer, filename="table.png")
        await ctx.respond(content="Here's the table:", file=file)
        
def setup(bot: commands.Bot):
    bot.add_cog(calc(bot))