import discord, math, random
from discord import Option, SlashCommandGroup, ApplicationContext, slash_command
from discord.ext import commands
from discord.utils import get
from discord.ui import View, Modal, InputText

class start(commands.Cog):
    def __init__(self, bot):
            self.bot: commands.Bot = bot

    @slash_command(
        name="start", description="Randomize teams, vote format and start playing", guild_only=True
    )
    async def start(self, ctx: ApplicationContext):
        if self.bot.mogi["voting"]:
            return await ctx.respond("Already started a vote", ephemeral=True)
        if not ctx.author.mention in self.bot.mogi["players"]:
            return await ctx.respond(
                "You can't start a mogi you aren't in", ephemeral=True
            )
        if len(self.bot.mogi["players"]) < 3:
            return await ctx.respond("Can't start a mogi with less than 3 players")
        if self.bot.mogi["running"]:
            return await ctx.respond("Mogi is already in play")

        self.bot.mogi["voting"] = 1
        self.bot.mogi["locked"] = True

        players_len = len(self.bot.mogi["players"])
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

        view = FormatView(self.bot.mogi)
        await ctx.respond(
            f"<@&{get(ctx.guild.roles, name='InMogi').id}> \nBeginning Mogi \nVote for a format:",
            view=view,
        )

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
        self.bot.mogi["teams"] = []

        lineup_str = "# Lineup \n"

        self.bot.mogi["format"] = format
        self.bot.mogi["running"] = 1
        self.bot.mogi["locked"] = True
        self.bot.mogi["voting"] = 0
        self.bot.mogi["votes"] = {key: 0 for key in self.bot.mogi["votes"]}
        self.bot.mogi["voters"] = []

        if format == "ffa":
            for i, player in enumerate(self.bot.mogi["players"]):
                lineup_str += f"`{i+1}:` {player}\n"
                self.bot.mogi["teams"].append([player])
                self.bot.mogi["running"] = 1
            return await ctx.respond(lineup_str)

        random.shuffle(self.bot.mogi["players"])
        teams = []
        for i in range(0, len(self.bot.mogi["players"]), int(format[0])):
            teams.append(self.bot.mogi["players"][i : i + int(format[0])])
        self.bot.mogi["teams"] = teams
        for i, item in enumerate(teams):
            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

        await ctx.respond(lineup_str)

    @slash_command(name="stop", description="Revert to the state before a vote was started", guild_only=True)
    async def stop(self, ctx: ApplicationContext):
        if not self.bot.mogi["running"]:
            return await ctx.respond("No running mogi yet. if vote is still in process, it needs to end or be force started before it can be stopped")
        if len(self.bot.mogi["points"]):
            return await ctx.respond("The mogi is already in the process of MMR calculation")
        self.bot.mogi["running"] = 0
        self.bot.mogi["teams"] = []
        self.bot.mogi["format"] = ""
        self.bot.mogi["locked"] = False
        self.bot.mogi["votes"] = {key: 0 for key in self.bot.mogi["votes"]}
        self.bot.mogi["voters"] = []
        self.bot.mogi["voting"] = 0
        
        await ctx.respond("The mogi has been stopped, use /start to start it again")
        await ctx.send(f"Debug:\nVotes:{self.bot.mogi['votes']}")
        
def setup(bot: commands.Bot):
    bot.add_cog(start(bot))