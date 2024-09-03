import discord, math
from discord import Option, ApplicationContext, slash_command, Interaction
from discord.ext import commands
from discord.utils import get
from discord.ui import View, Modal, InputText

import pymongo
from pymongo import database, collection

import pandas as pd
import dataframe_image as dfi
from matplotlib import colors
from io import BytesIO

import cogs.extras.mmr_algorithm as mmr_alg
from cogs.extras.ranks import calcRank
from cogs.extras.utils import is_mogi_manager

class calc(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.db: database.Database = self.bot.db
        self.players: collection.Collection = self.bot.players

    @slash_command(name="points", description="Use after a mogi - input player points")
    @is_mogi_manager()
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
                inmogi_profiles = list(self.db["players"].find({"discord": {"$in": [player.strip("<@!>") for player in self.bot.mogi["players"]]}}))
                for i, player in enumerate(self.mogi["players"]):
                    if player not in self.mogi["calc"] and count < 4:
                        profile_name = inmogi_profiles[i]["name"]
                        server_name = get(ctx.guild.members, int(player.strip("<@!>")))
                        self.add_item(InputText(label = f"{profile_name} ({server_name})"))
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
        
    @slash_command(name="calc")
    @is_mogi_manager()
    async def calc(self, ctx: ApplicationContext):
        player_mmrs = []

        inmogi_profiles = list(self.players.find({"discord": {"$in": [player.strip("<@!>") for player in self.bot.mogi["players"]]}}))
        for team in self.bot.mogi["teams"]:
            for player in team:
                player_data = [profile for profile in inmogi_profiles if profile.get("discord") == player.strip("<@!>")][0]
                player_mmrs.append(player_data["mmr"])

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

        form = self.bot.mogi['format'][0]

        new_new_ratings = mmr_alg.calculate_mmr(player_mmrs, placements, (int(form) if form != "f" else 1))
        new_new_ratings = [math.ceil(rating * 1.2) if rating > 0 else rating for rating in new_new_ratings]

        for team_delta in new_new_ratings:
            self.bot.mogi["results"].extend([team_delta] * (int(form) if form != "f" else 1))

        if form != "f":
            self.bot.mogi['placements'] = []
            for i in placements:
                self.bot.mogi['placements'].extend([i] * (int(form)))

        await ctx.respond(f"""
            Data has been processed and new mmr has been calculated. Use /table to view and /apply to apply the new mmr
        """)

    @slash_command(name="table")
    @is_mogi_manager()
    async def table(self, ctx: ApplicationContext):
        await ctx.response.defer()
        players = [
            self.players.find_one({"discord": player.strip("<@!>")})["name"]
            for player in self.bot.mogi["players"]
        ]
        current_mmrs = [
            round(self.players.find_one({"discord": player.strip("<@!>")})["mmr"])
            for player in self.bot.mogi["players"]
        ]
        new_mmrs = [current_mmrs[i] + self.bot.mogi["results"][i] for i in range(0, len(players))]

        try:
            data = {
                "Pos.": self.bot.mogi["placements"],
                "Player": players,
                "MMR": current_mmrs,
                "Change": [
                    round(self.bot.mogi["results"][i]) for i in range(0, len(players))
                ],
                "New MMR": new_mmrs,
            }
        except:
            data = {
                "Player": players,
                "MMR": current_mmrs,
                "Change": [
                    round(self.bot.mogi["results"][i]) for i in range(0, len(players))
                ],
                "New MMR": new_mmrs,
            }
        df = pd.DataFrame(data).set_index("Player")
        df = df.sort_values(by="Change", ascending=False)

        if self.bot.mogi["format"] == "ffa":
            df = df.sort_values(by="Pos.", ascending=True)

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

    @slash_command(name="apply", description="Use after a /calc to apply new mmr")
    @is_mogi_manager()
    async def apply(self, ctx: ApplicationContext):
        if not self.bot.mogi["results"]:
            return await ctx.respond("No results to apply or already applied")

        await ctx.response.defer()
        players = self.bot.mogi["players"]
        current_mmrs = [
            self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
            for player in self.bot.mogi["players"]
        ]
        new_mmrs = [current_mmrs[i] + self.bot.mogi["results"][i] for i in range(0, len(players))]
        deltas = self.bot.mogi["results"]

        new_players_data = [{"discord": players[i], "new_mmr": new_mmrs[i], "delta": deltas[i]} for i in range(len(self.bot.mogi["players"]))]
        new_players_data = [player for player in new_players_data if player['discord'] not in self.bot.mogi["subs"] or player["delta"] > 0]

        self.players.bulk_write([
            pymongo.UpdateOne(
                {"discord": player["discord"].strip("<@!>")},
                {
                    "$set": {"mmr": player["new_mmr"]},
                    "$inc": {"losses" if player["delta"] < 0 else "wins": 1},
                    "$push": {"history": {"$each": [player["delta"]], "$slice": -30}},
                },
                upsert=False)
            for player in new_players_data
        ])
        for i, player in enumerate(players):
            if player in self.bot.mogi["subs"] and deltas[i] < 0:
                await ctx.send(f"Excluded {self.bot.get_user(int(player.strip('<@!>'))).mention} because they subbed")
                continue
            current_rank = calcRank(current_mmrs[i])
            new_rank = calcRank(new_mmrs[i])
            if current_rank != new_rank:
                await ctx.send(f"{self.bot.get_user(int(player.strip('<@!>'))).mention} is now in {new_rank}")
                await ctx.guild.get_member(int(player.strip('<@!>'))).remove_roles(get(ctx.guild.roles, name=f"Lounge - {current_rank}"))
                await ctx.guild.get_member(int(player.strip('<@!>'))).add_roles(get(ctx.guild.roles, name=f"Lounge - {new_rank}"))

        self.bot.mogi["locked"] = False

        self.bot.mogi["point_count"] = 0
        self.bot.mogi["input_points"] = []
        self.bot.mogi["points"] = []
        self.bot.mogi["calc"] = []
        self.bot.mogi["results"] = []
        self.bot.mogi["points_user"] = ""

        await ctx.respond("Applied MMR changes ✅")
       
def setup(bot: commands.Bot):
    bot.add_cog(calc(bot))