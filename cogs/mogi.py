import os, discord, pymongo, math, random

from discord import ApplicationContext, Interaction, Option, slash_command
from discord.ui import View, Modal, InputText
from discord.utils import get
from discord.ext import commands

import trueskill
from trueskill import Rating, rate, global_env

import pandas as pd
import dataframe_image as dfi
from matplotlib import colors
from io import BytesIO


class mogi(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient(
            f"mongodb://{os.getenv('MONGODB_HOST')}:27017/"
        )
        self.db = self.client["lounge"]
        self.players = self.db["players"]
        self.mogi = {
            "status": 0,
            "running": 0,
            "players": [],
            "teams": [],
            "calc": [],
            "points": [],
            "format": "",
            "results": [],
            "placements": [],
        }

    @slash_command(name="open", description="Start a new mogi")
    async def open(self, ctx: ApplicationContext):
        if self.mogi["status"]:
            return await ctx.respond("A mogi is already open")
        self.mogi["status"] = 1
        await ctx.respond("# Started a new mogi! Use /join to participate!")

    @slash_command(name="join", description="Join the current mogi")
    async def join(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("Currently no mogi open")
        if ctx.author.mention in self.mogi["players"]:
            return await ctx.respond("You are already in the mogi")
        if len(self.mogi["players"]) >= 12:
            return await ctx.respond("The mogi is already full")
        if ctx.author.mention not in self.mogi["players"]:
            self.mogi["players"].append(ctx.author.mention)
        if get(ctx.guild.roles, name="InMogi") not in ctx.author.roles:
            await ctx.user.add_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond(
            f"{ctx.author.name} joined the mogi!\n{len(self.mogi['players'])} players are in!"
        )

    @slash_command(name="leave", description="Leave the current mogi")
    async def leave(self, ctx: ApplicationContext):
        if ctx.author.mention not in self.mogi["players"]:
            return await ctx.respond("You are not in the mogi")
        self.mogi["players"].remove(ctx.author.mention)
        await ctx.user.remove_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond(
            f"{ctx.author.mention} left the mogi!\n{len(self.mogi['players'])} players are in!"
        )

    @slash_command(name="l", description="List all players in the current mogi")
    async def l(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("Currently no open mogi")
        if not self.mogi["players"]:
            return await ctx.respond("Current mogi: \n No players")
        list = "Current mogi:\n"
        for index, player in enumerate(self.mogi["players"]):
            name = get(ctx.guild.members, id=int(player.strip("<@!>"))).name
            list += f"*{index+1}.* {name}\n"
        await ctx.respond(list, allowed_mentions = discord.AllowedMentions(users=False))

    @slash_command(name="close", description="Stop the current Mogi if running")
    async def close(self, ctx: ApplicationContext):
        self.mogi = {
            "status": 0,
            "running": 0,
            "players": [],
            "teams": [],
            "calc": [],
            "points": [],
            "format": "",
            "results": [],
            "placements": [],
        }
        for member in ctx.guild.members:
            if get(ctx.guild.roles, name="InMogi") in member.roles:
                await member.remove_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond("# The mogi has been closed")

    @slash_command(name="status", description="See current state of mogi")
    async def status(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("No running mogi")
        await ctx.respond(f"Currently open mogi: {len(self.mogi['players'])} players")

    @slash_command(
        name="start", description="Randomize teams, vote format and start playing"
    )
    async def start(self, ctx: ApplicationContext):
        if not any(role.name == "InMogi" for role in ctx.author.roles):
            return await ctx.respond(
                "You can't start a mogi you aren't in", ephemeral=True
            )
        if len(self.mogi["players"]) < 3:
            return await ctx.respond("Can't start a mogi with less than 3 players")
        if self.mogi["running"]:
            return await ctx.respond("Mogi is already in play")

        players_len = len(self.mogi["players"])
        options = []
        options.append(discord.SelectOption(label=f"FFA", value=f"ffa"))
        if players_len % 2 == 0:
            for size in range(2, players_len // 2 + 1):
                if players_len % size == 0:
                    options.append(
                        discord.SelectOption(label=f"{size}v{size}", value=f"{size}v{size}")
                    )

        class FormatView(View):
            def __init__(self, mogi):
                super().__init__()
                self.mogi = mogi
                self.voters = []
                self.votes = {
                    "ffa": 0,
                    "2v2": 0,
                    "3v3": 0,
                    "4v4": 0,
                    "5v5": 0,
                    "6v6": 0,
                }

            @discord.ui.select(options=options)
            async def select_callback(self, select, interaction: discord.Interaction):
                await interaction.response.defer()
                if self.mogi["running"]:
                    return await ctx.send("Mogi already decided, voting is closed")
                if not any(role.name == "InMogi" for role in ctx.author.roles):
                    return await ctx.send(
                        "You can't vote if you aren't in the mogi", ephemeral=True
                    )
                selected_option = select.values[0]
                if interaction.user.name in self.voters:
                    return await interaction.response.send_message(
                        "You already voted", ephemeral=True
                    )
                self.voters.append(interaction.user.name)
                self.votes[selected_option] += 1
                await interaction.followup.send(f"+1 vote for *{selected_option}*", ephemeral=True)
                if len(self.voters) >= math.ceil(
                    len(self.mogi["players"]) / 2
                ):
                    format = max(self.votes, key=self.votes.get)
                    self.mogi["format"] = format
                    lineup_str = ""
                    if players_len % 2 != 0 or format == "ffa":
                        for i, player in enumerate(self.mogi["players"]):
                            lineup_str += f"`{i+1}:` {player}\n"
                            self.mogi["teams"].append([player])
                    else:
                        random.shuffle(self.mogi["players"])
                        teams = []
                        for i in range(0, len(self.mogi["players"]), int(format[0])):
                            teams.append(self.mogi["players"][i : i + int(format[0])])
                        self.mogi["teams"] = teams
                        for i, item in enumerate(teams):
                            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

                    await ctx.send(
                        f"""
                        # Mogi starting!
                        ## Format: {format}
                        ### Lineup:
                        \n{lineup_str}
                    """
                    )
                    self.votes = {key: 0 for key in self.votes}
                    self.mogi["running"] = 1
                else:
                    pass

        view = FormatView(self.mogi)
        await ctx.respond(
            f"{get(ctx.guild.roles, name='InMogi').mention} \nBeginning Mogi\nVote for a format:",
            view=view,
        )

    @slash_command(name="force_start", description="When voting did not work - force start the mogi with a given format")
    async def force_start(
        self, 
        ctx: ApplicationContext, 
        format = Option(
            str,
            name="format",
            description="format to play",
            required=True,
            choices=[
                "ffa",
                "2v2",
                "3v3",
                "4v4",
                "5v5",
                "6v6"
            ],
        ),):
        lineup_str = "# Lineup"

        if format == "ffa":
            for i, player in enumerate(self.mogi["players"]):
                lineup_str += f"`{i+1}:` {player}\n"
                self.mogi["teams"].append([player])
                return await ctx.respond(lineup_str)

        random.shuffle(self.mogi["players"])
        teams = []
        for i in range(0, len(self.mogi["players"]), int(format[0])):
            teams.append(self.mogi["players"][i : i + int(format[0])])
        self.mogi["teams"] = teams
        for i, item in enumerate(teams):
            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

        self.mogi["running"] = 1
        self.mogi["format"] = format
        await ctx.respond(lineup_str)

    @slash_command(name="points", description="Use after a mogi - input player points")
    async def points(self, ctx: ApplicationContext):
        if not self.mogi["running"]:
            return await ctx.respond("No running mogi")

        class MogiModal(discord.ui.Modal):
            def __init__(self, mogi, db, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.mogi = mogi

                count = 0
                for player in mogi['players']:
                    if player not in mogi['calc'] and count < 4:
                        mentioned_user = db["players"].find_one(
                        {"discord": player.strip("<@!>")})["name"]
                        self.add_item(InputText(label=mentioned_user))
                        mogi["calc"].append(player)
                        count += 1

            async def callback(
                self: Modal = Modal,
                interaction: Interaction = Interaction,
                mogi=self.mogi,
            ):
                if mogi["format"] == "ffa":
                    for i in range(0, len(self.children)):
                        mogi["points"].append([int(self.children[i].value)])
                else:
                    size = int(mogi["format"][0])
                    points = []
                    for i in range(0, len(self.children)):
                        points.append(int(self.children[i].value))
                    for i in range(0, len(points), size):
                        mogi["points"].append(points[i : i + size])
                await interaction.response.send_message(
                    """
                    Points have been collected. 
                    Use this command again until all players' points have been collected.
                    Then use /calc to calculate results
                """,
                    ephemeral=True,
                )

        if len(self.mogi["players"]) > len(self.mogi["calc"]):
            modal = MogiModal(
                self.mogi, self.db, title="Input player points after match"
            )
            await ctx.send_modal(modal)
        else:
            return await ctx.respond("Already got all calcs")

    @slash_command(name="test")
    async def test(self, ctx: ApplicationContext):
        players = ["probablyjassin", "MITSIKU", "-wolf-", "MintCheetah", "Kevnkkm", "NotNiall", "KaramTNC", "ujuj"]
        current_mmr = [2258, 2616, 3460, 2141, 2731, 1416, 2177, 1945]
        new_mmr = [2358, 2716, 3452, 2133, 2724, 1409, 2092, 1860]
        data = {
                    #"#": [1, 2, 3, 4, 5, 6, 7, 8],
                    "Player": players,
                    "MMR": current_mmr,
                    "Change": [new_mmr[i] - current_mmr[i] for i in range(0, len(players))],
                    "New MMR": new_mmr
                }
        buffer = BytesIO()
        df = pd.DataFrame(data)
        #df = df.sort_values(by='#', ascending=True)
        dfi.export(df.style.background_gradient(cmap=colors.LinearSegmentedColormap.from_list("", ["red", "white", "green"]), low=0, high=0.2, subset=["Change"]), buffer)
        buffer.seek(0)
        file = discord.File(buffer, filename="table.png")
        await ctx.respond(content="Here's the table:", file=file)


    @slash_command(
        name="calc", description="Use after using /points to calculate new mmr"
    )
    async def calc(self, ctx: discord.ApplicationContext):
        if not len(self.mogi["calc"]):
            return ctx.respond(
                "There doesn't seem to be data to make calculations with"
            )

        global_env()
        trueskill.setup(
            mu=2000,
            sigma=200,
            beta=1200,
            tau=350,
            draw_probability=0.05,
            backend=None,
            env=None,
        )

        calc_teams = []
        for team in self.mogi["teams"]:
            calc_team = []
            for player in team:
                mmr = self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
                calc_team.append(Rating(mmr, 400))
            calc_teams.append(calc_team)

        scores = []
        for team_point_arr in self.mogi["points"]:
            scores.append([sum(team_point_arr)])

        ranks_dict = {}
        placements = []
        for i, score in enumerate(sorted(scores, reverse=True)):
            ranks_dict[score[0]] = i + 1
        for score in scores:
            placements.append(ranks_dict[score[0]])
        self.mogi["placements"] = placements

        new_ratings = rate(calc_teams, placements)

        for team in new_ratings:
            self.mogi["results"].append([round(player.mu) for player in team])

        await ctx.respond(
            "Data has been processed and new mmr has been calculated. Use /table to view and /apply to apply the new mmr"
        )

    @slash_command(name="table", description="Use after a /calc to view the results")
    async def table(self, ctx: discord.ApplicationContext):
        players = [
            self.players.find_one({"discord": player.strip("<@!>")})["name"]
            for player in self.mogi["players"]
        ]
        current_mmr = [
            self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
            for player in self.mogi["players"]
        ]
        new_mmr = [val for sublist in self.mogi["results"] for val in sublist]

        data = {
            "Player": players,
            "MMR": current_mmr,
            "Change": [new_mmr[i] - current_mmr[i] for i in range(0, len(players))],
            "New MMR": new_mmr,
        }
        df = pd.DataFrame(data)
        df.index = range(1, len(df) + 1)

        buffer = BytesIO()
        df = df.sort_values(by="Change", ascending=False)
        dfi.export(
            df.style.background_gradient(
                cmap=colors.LinearSegmentedColormap.from_list(
                    "", ["red", "white", "green"]
                ),
                low=0,
                high=0.2,
                subset=["Change"],
            ),
            buffer,
        )

        buffer.seek(0)
        file = discord.File(buffer, filename="table.png")
        await ctx.respond(content="Here's the table:", file=file)

    @slash_command(name="apply", description="Use after a /calc to apply new mmr")
    async def apply(self, ctx: discord.ApplicationContext):
        players = self.mogi["players"]
        current_mmr = [
            self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
            for player in self.mogi["players"]
        ]
        new_mmr = [val for sublist in self.mogi["results"] for val in sublist]

        print(players, current_mmr, new_mmr)

        deltas = [new_mmr[i] - current_mmr[i] for i in range(0, len(players))]

        for i, player in enumerate(players):
            id = self.players.update_one(
                {"player": player.strip("<@!>")}, {"$set": {"mmr": new_mmr}}
            ).upserted_id
            self.players.update_one(
                {"player_id": id},
                {"$push": {"history": deltas[i]}},
                False,
            )
            self.players.update_one(
                {"player": player}, {"$inc": {"losses" if deltas[i] < 0 else "wins": 1}}
            )
            
        await ctx.respond("Updated every racers mmr")

def setup(bot: commands.Bot):
    bot.add_cog(mogi(bot))
