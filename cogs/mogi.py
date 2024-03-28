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

default_mogi_state = {
    "status": 0,
    "running": 0,
    "password": None,
    "locked": False,
    "players": [],
    "teams": [],
    "calc": [],
    "points": [],
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

    @slash_command(name="open", description="Start a new mogi")
    async def open(self, ctx: ApplicationContext):
        if self.mogi["status"]:
            return await ctx.respond("A mogi is already open")
        self.mogi["status"] = 1
        await ctx.respond("# Started a new mogi! Use /join to participate!")

    @slash_command(name="lock", description="Lock the current mogi from being closed")
    async def lock(self, ctx: ApplicationContext):
        self.mogi["locked"] = (not self.mogi["locked"])
        await ctx.respond(f"New mogi locking state: {self.mogi['locked']}")

    @slash_command(name="join", description="Join the current mogi")
    async def join(self, ctx: ApplicationContext):
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

    @slash_command(name="leave", description="Leave the current mogi")
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

    @slash_command(name="l", description="List all players in the current mogi")
    async def l(self, ctx: ApplicationContext):
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
            list += f"*{index+1}.* {name}\n"
        await ctx.respond(list, allowed_mentions=discord.AllowedMentions(users=False))

    @slash_command(name="close", description="Stop the current Mogi if running")
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
        name="pswd", description="view or change the server password (to send to mogi players)"
    )
    async def pswd(self, ctx: ApplicationContext, new=Option(str, required=False)):
        if not new:
            return await ctx.respond(f"Current password: ```{new}```")
        self.mogi["password"] = new
        await ctx.respond("Updated password")

    @slash_command(name="status", description="See current state of mogi")
    async def status(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("No running mogi")
        await ctx.respond(f"Currently open mogi: {len(self.mogi['players'])} players")

    @slash_command(
        name="start", description="Randomize teams, vote format and start playing"
    )
    async def start(self, ctx: ApplicationContext):
        if not ctx.author.mention in self.mogi["players"]:
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
            async def select_callback(self, select, interaction: discord.Interaction):
                await interaction.response.defer()
                if interaction.user.mention not in self.mogi["players"]:
                    return
                if self.mogi["running"]:
                    return await ctx.respond(
                        "Mogi already decided, voting is closed", ephemeral=True
                    )
                selected_option = select.values[0]
                if interaction.user.name in self.mogi["voters"]:
                    return await interaction.response.send_message(
                        "You already voted", ephemeral=True
                    )
                self.mogi["voters"].append(interaction.user.name)
                self.mogi["votes"][selected_option] += 1
                await interaction.followup.send(
                    f"+1 vote for *{selected_option}*", ephemeral=True
                )

                len_players = len(self.mogi["players"])
                max_voted = max(self.mogi["votes"], key=self.mogi["votes"].get)
                if (len(self.mogi["voters"]) >= len_players) or (self.mogi["votes"][max_voted] >= math.ceil(len_players / 2) + 1):
                    await ctx.send("test - if got triggered - should start now??")
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
                    if self.mogi["password"]:
                        await ctx.send(f"# Server password: {self.mogi['password']}")
                    self.mogi["votes"] = {key: 0 for key in self.mogi["votes"]}
                    self.mogi["running"] = 1

                else:
                    pass

        view = FormatView(self.mogi)
        await ctx.respond(
            f"{get(ctx.guild.roles, name='InMogi').mention} \nBeginning Mogi \nVote for a format:",
            view=view,
        )

    @slash_command(name="debug_votes")
    async def debug_votes(self, ctx: ApplicationContext):
        await ctx.respond(f"""
            --Current voting-- \n
            Who voted? 
            {self.mogi['voters']} \n
            What are the votes?
            {self.mogi['votes']}
    """)

    @slash_command(name="tags", description="assign team roles")
    async def tags(self, ctx: ApplicationContext):
        if not self.mogi["format"]:
            return ctx.respond("No format chosen yet")
        if self.mogi["format"] != "ffa":
            for i, team in enumerate(self.mogi["teams"]):
                for player in team:
                    await ctx.guild.fetch_member(int(player.strip("<@!>"))).add_roles(
                        get(ctx.guild.roles, name=f"Team {i+1}")
                    )
            return await ctx.respond("Assigned team roles")
        await ctx.respond("format is ffa, not team roles assigned")

    @slash_command(name="untag")
    async def untag(self, ctx: ApplicationContext):
        for i in [1, 2, 3, 4, 5]:
            for member in ctx.guild.members:
                if get(ctx.guild.roles, name=f"Team {i}") in member.roles:
                    await member.remove_roles(get(ctx.guild.roles, name=f"Team {i}"))

    @slash_command(
        name="force_start",
        description="When voting did not work - force start the mogi with a given format",
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
        lineup_str = "# Lineup \n"

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

        self.mogi["running"] = 1
        self.mogi["format"] = format
        await ctx.respond(lineup_str)

    @slash_command(name="teams", description="Show teams")
    async def teams(self, ctx: ApplicationContext):
        if not self.mogi["status"]:
            return await ctx.respond("No open mogi", ephemeral=True)
        if not len(self.mogi["teams"]):
            return await ctx.respond("No teams decided yet", ephemeral=True)
        lineup_str = "# Teams \n"
        if self.mogi["format"] == "ffa":
            for i, player in enumerate(self.mogi["players"]):
                lineup_str += f"`{i+1}:` {get(ctx.guild.members, id=int(player.strip("<@!>"))).display_name}\n"
        else:
            for i, item in enumerate(self.mogi["teams"]):
                lineup_str += f"\n `{i+1}`. {', '.join(item)}"
        await ctx.respond(lineup_str)

    @slash_command(name="sub", description="Replace a player in the mogi")
    async def sub(
        self,
        ctx: ApplicationContext,
        player=Option(
            str,
            name="player",
            description="who to replace (input @ discord mention)",
            required=True,
        ),
        sub=Option(
            str,
            name="sub",
            description="subbing player (input @ discord mention)",
            required=True,
        ),
    ):
        if not len(self.mogi["players"]):
            return await ctx.respond("no players", ephemeral=True)
        if not len(self.mogi["teams"]):
            return await ctx.respond("No teams decided yet")

        def replace(space, player, sub):
            if isinstance(space, list):
                return [replace(item, player, sub) for item in space]
            else:
                return sub if space == player else space

        self.mogi["players"] = replace(self.mogi["players"], player, sub)
        self.mogi["teams"] = replace(self.mogi["teams"], player, sub)
        await ctx.respond(f"Subbed {player} with {sub} if applicable")

    @slash_command(name="points", description="Use after a mogi - input player points")
    async def points(self, ctx: ApplicationContext):
        if not self.mogi["running"]:
            return await ctx.respond("No running mogi")

        class MogiModal(discord.ui.Modal):
            def __init__(self, mogi, db, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.mogi = mogi

                count = 0
                for player in mogi["players"]:
                    if player not in mogi["calc"] and count < 4:
                        mentioned_user = db["players"].find_one(
                            {"discord": player.strip("<@!>")}
                        )["name"]
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
                    if len(mogi["points"]) % size == 0:
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
            sigma=100,
            beta=9000,
            tau=950,
            draw_probability=0.05,
            backend=None,
            env=None,
        )

        calc_teams = []
        for team in self.mogi["teams"]:
            calc_team = []
            for player in team:
                mmr = self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
                calc_team.append(Rating(mmr, 200))
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

    @slash_command(name="table", description="Use after a /calc to view the results")
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

    @slash_command(name="calc_manual")
    async def calc_manualy(self, ctx: ApplicationContext):
        pass

    @slash_command(name="apply", description="Use after a /calc to apply new mmr")
    async def apply(self, ctx: ApplicationContext):
        players = self.mogi["players"]
        current_mmr = [
            self.players.find_one({"discord": player.strip("<@!>")})["mmr"]
            for player in self.mogi["players"]
        ]
        new_mmr = [element for sublist in self.mogi["results"] for element in sublist]
        deltas = [new_mmr[i] - current_mmr[i] for i in range(0, len(players))]

        for i, player in enumerate(players):
            self.players.update_one(
                {"discord": player.strip("<@!>")}, {"$set": {"mmr": new_mmr[i]}}
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

        await ctx.respond(
            f"Updated every racers mmr \n Debug: \n Players: {players}\n Current MMR: {current_mmr} \n New MMR: {new_mmr[i]}",
            ephemeral=True,
        )

def setup(bot: commands.Bot):
    bot.add_cog(mogi(bot))
