import os, discord, pymongo, math, random, asyncio
from copy import deepcopy

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

import cogs.extras.mmr_algorithm as mmr_alg

def calcRank(mmr):
    ranks = [
        {"name": "Wood", "range": (-math.inf, 0)},
        {"name": "Bronze", "range": (0, 1499)},
        {"name": "Silver", "range": (1400, 2999)},
        {"name": "Gold", "range": (3000, 5099)},
        {"name": "Platinum", "range": (5100, 6999)},
        {"name": "Diamond", "range": (7000, 9499)},
        {"name": "Master", "range": (9500, math.inf)},
    ]
    for range_info in ranks:
        start, end = range_info["range"]
        if start <= mmr <= end:
            return range_info["name"]
    return "---"

default_mogi_state = {
    "status": 0,
    "voting": 0,
    "running": 0,
    "password": None,
    "locked": False,
    "players": [],
    "subs": [],
    "teams": [],
    "calc": [],
    "points": [],
    "input_points": [],
    "point_count": 0,
    "format": "",
    "results": [],
    "placements": [],
    "voters": [],
    "votes": { "ffa": 0, "2v2": 0, "3v3": 0, "4v4": 0, "5v5": 0, "6v6": 0}
}

class mogi(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.client = pymongo.MongoClient(
            f"mongodb://{os.getenv('MONGODB_HOST')}:27017/"
        )
        self.db = self.client["lounge"]
        self.players = self.db["players"]
        self.mogi = deepcopy(default_mogi_state)

        self.join_sem = asyncio.Semaphore(1)

    @slash_command(name="debug", description="print all data in order to debug")
    async def debug(self, ctx: ApplicationContext):
        await ctx.respond(f"{self.mogi}")

    @slash_command(name="open", description="Start a new mogi", guild_only=True)
    async def open(self, ctx: ApplicationContext):
        if self.mogi["status"]:
            return await ctx.respond("A mogi is already open")
        self.mogi["status"] = 1
        await ctx.respond("# Started a new mogi! Use /join to participate!")

    @slash_command(name="lock", description="Lock the current mogi from being closed", guild_only=True)
    async def lock(self, ctx: ApplicationContext):
        self.mogi["locked"] = (not self.mogi["locked"])
        await ctx.respond(f"New mogi locking state: {self.mogi['locked']}")

    @slash_command(name="join", description="Join the current mogi", guild_only=True)
    async def join(self, ctx: ApplicationContext):
        async with self.join_sem:
            if not self.mogi["status"]:
                return await ctx.respond("Currently no mogi open")
            if self.mogi["locked"]:
                return await ctx.respond("The mogi is locked, no joining, leaving or closing until it is unlocked")
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

    @slash_command(name="leave", description="Leave the current mogi", guild_only=True)
    async def leave(self, ctx: ApplicationContext):
        if ctx.author.mention not in self.mogi["players"]:
            return await ctx.respond("You are not in the mogi")
        if self.mogi["locked"]:
            return await ctx.respond("The mogi is locked, no joining, leaving or closing until it is unlocked")
        self.mogi["players"].remove(ctx.author.mention)
        await ctx.user.remove_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond(
            f"{ctx.author.mention} left the mogi!\n{len(self.mogi['players'])} players are in!"
        )

    @slash_command(name="l", description="List all players in the current mogi", guild_only=True)
    async def l(self, ctx: ApplicationContext, 
                table = Option(
                    name="table", 
                    description="Omit numbers to copy and paste into a table maker",
                    required=False,
                    choices = ["y"]
                    )):
        if not self.mogi["status"]:
            return await ctx.respond("Currently no open mogi")
        if not self.mogi["players"]:
            return await ctx.respond("Current mogi: \n No players")
        list = "Current mogi:\n"
        for index, player in enumerate(self.mogi["players"]):
            try:
                if get(ctx.guild.members, id=int(player.strip("<@!>"))).nick:
                    name = get(ctx.guild.members, id=int(player.strip("<@!>"))).nick
                else:
                    try:
                        name = get(ctx.guild.members, id=int(player.strip("<@!>"))).display_name
                    except:
                        name = player
            except:
                try:
                    name = get(ctx.guild.members, id=int(player.strip("<@!>"))).display_name
                except:
                    name = player
            if table:
                list += f"{name} + \n\n"
            else:
                list += f"*{index+1}.* {name}\n"
        await ctx.respond(list, allowed_mentions=discord.AllowedMentions(users=False))

    @slash_command(name="close", description="Stop the current Mogi if running", guild_only=True)
    async def close(self, ctx: ApplicationContext):
        await ctx.response.defer()
        if self.mogi["locked"]:
            return await ctx.respond("The mogi is locked, no joining, leaving or closing until it is unlocked")

        message = await ctx.send(
            f"""
        Closing the mogi discards all teams and points.
        Only do this after the results have been posted.
        Are you sure, {ctx.author.mention} ?
        """
        )

        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.user and str(reaction.emoji) in ("✅", "❌")

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=60, check=check
            )
        except asyncio.TimeoutError:
            await message.edit(content="Confirmation timed out.")
            return await ctx.respond("Timeout")

        if str(reaction.emoji) == "✅":
            await message.edit(content="Closing...")
            self.mogi = deepcopy(default_mogi_state)
            for member in ctx.guild.members:
                if get(ctx.guild.roles, name="InMogi") in member.roles:
                    await member.remove_roles(get(ctx.guild.roles, name="InMogi"))
            final_message = "# The mogi has been closed"
        else:
            await message.edit(content="Action canceled.")
            final_message = "‎ "

        await ctx.followup.send(final_message)

    @slash_command(
        name="pswd", description="view or change the server password (to send to mogi players)", guild_only=True
    )
    async def pswd(self, ctx: ApplicationContext, new=Option(str, required=False)):
        if not new:
            return await ctx.respond(f"Current password: ```{self.mogi['password']}```")
        self.mogi["password"] = new
        await ctx.respond("Updated password")

    @slash_command(name="status", description="See current state of mogi")
    async def status(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("No running mogi")
        await ctx.respond(f"Currently open mogi: {len(self.mogi['players'])} players")

    @slash_command(
        name="start", description="Randomize teams, vote format and start playing", guild_only=True
    )
    async def start(self, ctx: ApplicationContext):
        if self.mogi["voting"]:
            return await ctx.respond("Already started a vote", ephemeral=True)
        if not ctx.author.mention in self.mogi["players"]:
            return await ctx.respond(
                "You can't start a mogi you aren't in", ephemeral=True
            )
        if len(self.mogi["players"]) < 3:
            return await ctx.respond("Can't start a mogi with less than 3 players")
        if self.mogi["running"]:
            return await ctx.respond("Mogi is already in play")

        self.mogi["voting"] = 1
        self.mogi["locked"] = True

        players_len = len(self.mogi["players"])
        options = []
        options.append(discord.SelectOption(label=f"FFA", value=f"ffa"))
        for size in range(2, players_len // 2 + 1):
            if players_len % size == 0:
                options.append(
                    discord.SelectOption(label=f"{size}v{size}", value=f"{size}v{size}")
                )

        class FormatView(View):
            def __init__(self, mogi):
                super().__init__()
                self.mogi = mogi

            @discord.ui.select(options=options)
            async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
                if interaction.response.is_done() or interaction.user.id in self.mogi['voters']:
                    return await interaction.followup.send("You already voted", ephemeral=True)
                await interaction.response.defer()
                if interaction.user.mention not in self.mogi["players"]:
                    return
                if self.mogi["running"]:
                    return await interaction.respond(
                        "Mogi already decided, voting is closed", ephemeral=True
                    )
                selected_option = select.values[0]
                self.mogi["voters"].append(interaction.user.id)
                self.mogi["votes"][selected_option] += 1
                await interaction.followup.send(
                    f"+1 vote for *{selected_option}*", ephemeral=True
                )

                len_players = len(self.mogi["players"])
                max_voted = max(self.mogi["votes"], key=self.mogi["votes"].get)
                if (len(self.mogi["voters"]) >= len_players) or (self.mogi["votes"][max_voted] >= math.floor(len_players / 2) + 1):
                    self.mogi["format"] = max_voted
                    lineup_str = ""
                    if max_voted == "ffa":
                        for i, player in enumerate(self.mogi["players"]):
                            lineup_str += f"`{i+1}:` {player}\n"
                            self.mogi["teams"].append([player])
                    else:
                        random.shuffle(self.mogi["players"])
                        teams = []
                        for i in range(0, len(self.mogi["players"]), int(max_voted[0])):
                            teams.append(self.mogi["players"][i : i + int(max_voted[0])])
                        self.mogi["teams"] = teams
                        for i, item in enumerate(teams):
                            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

                    votes = "## Vote results:\n"
                    for item in self.mogi["votes"].keys():
                        votes += f"{item}: {self.mogi['votes'][item]}\n"
                    await ctx.send(votes)
                    await ctx.send(
                        f"""
                        # Mogi starting!
                        ## Format: {max_voted}
                        ### Lineup:
                        \n{lineup_str}
                    """
                    )
                    self.mogi["votes"] = {key: 0 for key in self.mogi["votes"]}
                    self.mogi["voting"] = 0
                    self.mogi["running"] = 1

                else:
                    pass

        view = FormatView(self.mogi)
        await ctx.respond(
            f"{get(ctx.guild.roles, name='InMogi').mention} \nBeginning Mogi \nVote for a format:",
            view=view,
        )

    @slash_command(name="debug_votes", guild_only=True)
    async def debug_votes(self, ctx: ApplicationContext):
        missing = []
        players = []
        for player in self.mogi['players']:
            players.append(int(player.strip("<@!>")))
        for player in players:
            if player not in self.mogi["voters"]:
                missing.append(player)
        if missing:
            string = f"**{len(missing)} player(s) haven't voted yet** \n"
            for missing_player in missing:
                string += f"{get(ctx.guild.members, id=missing_player).mention}\n"
            await ctx.respond(string)
        else: 
            await ctx.respond("No missing votes")

        await ctx.send(self.mogi['votes'])

    @slash_command(name="tags", description="assign team roles", guild_only=True)
    async def tags(self, ctx: ApplicationContext):
        await ctx.response.defer()
        if not self.mogi["format"]:
            return ctx.respond("No format chosen yet")
        if self.mogi["format"] != "ffa":
            for i, team in enumerate(self.mogi["teams"]):
                await ctx.send(f"team: {team} index: {i}")
                for player in team:
                    await get(ctx.guild.members, id=int(player.strip("<@!>"))).add_roles(
                        get(ctx.guild.roles, name=f"Team {i+1}")
                    )
            return await ctx.respond("Assigned team roles")
        await ctx.respond("format is ffa, not team roles assigned")

    @slash_command(name="untag", guild_only=True)
    async def untag(self, ctx: ApplicationContext):
        await ctx.response.defer()
        for i in [1, 2, 3, 4, 5]:
            for member in ctx.guild.members:
                if get(ctx.guild.roles, name=f"Team {i}") in member.roles:
                    await member.remove_roles(get(ctx.guild.roles, name=f"Team {i}"))

    @slash_command(
        name="force_start",
        description="When voting did not work - force start the mogi with a given format",
        guild_only=True
    )
    async def force_start(
        self,
        ctx: ApplicationContext,
        format=Option(
            str,
            name="format",
            description="format to play",
            required=True,
            choices=["ffa", "2v2", "3v3", "4v4", "5v5", "6v6"],
        ),
    ):
        self.mogi["teams"] = []

        lineup_str = "# Lineup \n"

        self.mogi["format"] = format
        self.mogi["running"] = 1
        self.mogi["locked"] = True
        self.mogi["voting"] = 0
        self.mogi["votes"] = {key: 0 for key in self.mogi["votes"]}
        self.mogi["voters"] = []

        if format == "ffa":
            for i, player in enumerate(self.mogi["players"]):
                lineup_str += f"`{i+1}:` {player}\n"
                self.mogi["teams"].append([player])
                self.mogi["running"] = 1
            return await ctx.respond(lineup_str)

        random.shuffle(self.mogi["players"])
        teams = []
        for i in range(0, len(self.mogi["players"]), int(format[0])):
            teams.append(self.mogi["players"][i : i + int(format[0])])
        self.mogi["teams"] = teams
        for i, item in enumerate(teams):
            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

        await ctx.respond(lineup_str)

    @slash_command(name="stop", description="Revert to the state before a vote was started")
    async def stop(self, ctx: ApplicationContext):
        if not self.mogi["running"]:
            return await ctx.respond("No running mogi yet. if vote is still in process, it needs to end or be force started before it can be stopped")
        if len(self.mogi["points"]):
            return await ctx.respond("The mogi is already in the process of MMR calculation")
        self.mogi["running"] = 0
        self.mogi["teams"] = []
        self.mogi["format"] = ""
        self.mogi["locked"] = False
        self.mogi["votes"] = {key: 0 for key in self.mogi["votes"]}
        self.mogi["voters"] = []
        self.mogi["voting"] = 0
        
        await ctx.respond("The mogi has been stopped, use /start to start it again")
        await ctx.send(f"Debug:\nVotes:{self.mogi['votes']}")


    @slash_command(name="teams", description="Show teams")
    async def teams(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("No open mogi", ephemeral=True)
        if not len(self.mogi["teams"]):
            return await ctx.respond("No teams decided yet", ephemeral=True)
        lineup_str = "# Teams \n"
        if self.mogi["format"] == "ffa":
            for i, player in enumerate(self.mogi["players"]):
                lineup_str += f"`{i+1}:` {get(ctx.guild.members, id=int(player.strip('<@!>'))).display_name}\n"
        else:
            for i, item in enumerate(self.mogi["teams"]):
                lineup_str += f"\n `{i+1}`. {', '.join(item)}"
        await ctx.respond(lineup_str)

    @slash_command(name="sub", description="Replace a player in the mogi", guild_only=True)
    async def sub(
        self,
        ctx: ApplicationContext,
        player = Option(
            str,
            name="player",
            description="who to replace (input @ discord mention)",
            required=True,
        ),
        sub = Option(
            str,
            name="sub",
            description="subbing player (input @ discord mention)",
            required=True,
        ),
    ):
        await ctx.response.defer()

        if not len(self.mogi["players"]):
            return await ctx.respond("no players", ephemeral=True)
        if not len(self.mogi["teams"]):
            return await ctx.respond("No teams decided yet")
        if sub in self.mogi["players"]:
            return await ctx.respond("This sub is already in the mogi")

        def replace(space, player, sub):
            if isinstance(space, list):
                return [replace(item, player, sub) for item in space]
            else:
                return sub if space == player else space

        self.mogi["players"] = replace(self.mogi["players"], player, sub)
        self.mogi["teams"] = replace(self.mogi["teams"], player, sub)

        await get(ctx.guild.members, id=int(sub.strip("<@!>"))).add_roles(get(ctx.guild.roles, name="InMogi"))
        await get(ctx.guild.members, id=int(player.strip("<@!>"))).remove_roles(get(ctx.guild.roles, name="InMogi"))

        self.mogi["subs"].append(sub)

        await ctx.respond(f"Subbed {player} with {sub} if applicable")

    @slash_command(name="points", description="Use after a mogi - input player points", guild_only=True)
    async def points(self, ctx: ApplicationContext):
        if not self.mogi["running"]:
            return await ctx.respond("No running mogi")

        class MogiModal(discord.ui.Modal):
            def __init__(self, mogi, db, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.mogi = mogi
                self.db = db

                count = 0
                for player in self.mogi["players"]:
                    if player not in mogi["calc"] and count < 4:
                        mentioned_user = db["players"].find_one(
                            {"discord": player.strip("<@!>")}
                        )["name"]
                        self.add_item(InputText(label = mentioned_user))
                        mogi["calc"].append(player)
                        count += 1

            async def callback(
                self: Modal = Modal,
                interaction: Interaction = Interaction,
                mogi=self.mogi,
            ):
                for i in range(0, len(self.children)):
                    mogi["input_points"].append(int(self.children[i].value))
                    self.mogi["point_count"] += 1
                        
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

        if len(self.mogi["players"]) > len(self.mogi["calc"]):
            modal = MogiModal(
                mogi=self.mogi, db=self.db, title="Input player points after match"
            )
            await ctx.send_modal(modal)
        else:
            return await ctx.respond("Already got all calcs")
        
    @slash_command(name="points_reset", description="Messed up points input? Reset them")
    async def points_reset(self, ctx: ApplicationContext):
        self.mogi["input_points"] = []
        self.mogi["points"] = []
        self.mogi["calc"] = []
        await ctx.respond("Clear all points")

    @slash_command(
        name="calc", description="Use after using /points to calculate new mmr", guild_only=True
    )
    async def calc(self, ctx: discord.ApplicationContext):
        if not len(self.mogi["calc"]):
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
        for team in self.mogi["teams"]:
            calc_team = []
            for player in team:
                mmr = self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
                calc_team.append(Rating(mmr, 100))
                new_algo_players.append(mmr)
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

        form = self.mogi['format'][0]
        new_new_ratings = mmr_alg.calculate_mmr(new_algo_players, placements, int(form) if form != "f" else 1 )
        await ctx.send(f"Hypothetical lounge-algoritm (soon new system) output: {new_new_ratings}")

        for team in new_ratings:
            self.mogi["results"].append([round(player.mu) for player in team])

        debug_string = "# Debug:\n Points:\n"
        for scoring in self.mogi['points']:
            debug_string += f"{scoring}\n"
        debug_string += "\n Current MMR:"
        for team in calc_teams:
            debug_string += f"{team}\n"
        debug_string += "\n New MMR:"
        for new in self.mogi["results"]:
            debug_string+= f"{new}\n"

        await ctx.respond(
            f'Data has been processed and new mmr has been calculated. Use /table to view and /apply to apply the new mmr \n {debug_string}',
            ephemeral=True,
        )

    @slash_command(name="table", description="Use after a /calc to view the results", guild_only=True)
    async def table(self, ctx: discord.ApplicationContext):
        players = [
            self.players.find_one({"discord": player.strip("<@!>")})["name"]
            for player in self.mogi["players"]
        ]
        current_mmr = [
            round(self.players.find_one({"discord": player.strip("<@!>")})["mmr"])
            for player in self.mogi["players"]
        ]
        new_mmr = [val for sublist in self.mogi["results"] for val in sublist]

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
        players = self.mogi["players"]
        current_mmr = [
            self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
            for player in self.mogi["players"]
        ]
        new_mmr = [element for sublist in self.mogi["results"] for element in sublist]
        deltas = [new_mmr[i] - current_mmr[i] for i in range(0, len(players))]

        for i, player in enumerate(players):
            if player in self.mogi["subs"] and deltas[i] < 0:
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

        self.mogi["locked"] = False

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
        if True or upscale == "y":
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
    bot.add_cog(mogi(bot))
