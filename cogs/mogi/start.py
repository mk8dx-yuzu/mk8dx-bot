import discord, math, random
from discord import (
    Option,
    SlashCommandGroup,
    ApplicationContext,
    slash_command,
    Interaction,
)
from discord.ext import commands
from discord.utils import get
from discord.ui import View


def vote(bot: commands.Bot, format: str, user: discord.User):
    bot.mogi["votes"][format] += 1
    bot.mogi["voters"].append(user.mention)

def canVote(bot: commands.Bot, format: str, user: discord.User.mention):
    size = int(format[0]) if format[0] != "f" else 1
    return (
        bot.mogi["voting"] and
        (len(bot.mogi["players"]) % size == 0 and len(bot.mogi["players"]) > size)
        and user in bot.mogi["players"]
        and user not in bot.mogi["voters"]
    )

def isDecided(bot: commands.Bot):
    return (len(bot.mogi["voters"]) >= len(bot.mogi["players"])) or (
        bot.mogi["votes"][max(bot.mogi["votes"], key=bot.mogi["votes"].get)]
        >= math.floor(len(bot.mogi["players"]) / 2) + 1
    )

def startMogi(bot: commands.Bot):
    max_voted = max(bot.mogi["votes"], key=bot.mogi["votes"].get)
    bot.mogi["format"] = max_voted
    lineup_str = ""
    if max_voted == "ffa":
        for i, player in enumerate(bot.mogi["players"]):
            lineup_str += f"`{i+1}:` {player}\n"
            bot.mogi["teams"].append([player])
    else:
        random.shuffle(bot.mogi["players"])
        teams = []
        for i in range(0, len(bot.mogi["players"]), int(max_voted[0])):
            teams.append(
                bot.mogi["players"][i : i + int(max_voted[0])]
            )
        bot.mogi["teams"] = teams
        for i, item in enumerate(teams):
            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

    votes = "## Vote results:\n"
    for item in bot.mogi["votes"].keys():
        votes += f"{item}: {bot.mogi['votes'][item]}\n"
    bot.mogi["votes"] = {key: 0 for key in bot.mogi["votes"]}
    bot.mogi["voting"] = False
    bot.mogi["running"] = True

    return f"{votes}\n# Mogi starting!\n## Format: {max_voted}\n### Lineup:\n{lineup_str}"

class Menu(discord.ui.View):
    def __init__(self, bot, count):
        super().__init__()
        self.value = None
        self.count = count
        self.bot = bot

    def update_styles(self):
        self.btn2v2.style = (
            discord.ButtonStyle.blurple
            if self.count % 2 == 0 and self.count > 2
            else discord.ButtonStyle.gray
        )
        self.btn3v3.style = (
            discord.ButtonStyle.blurple
            if self.count % 3 == 0 and self.count > 3
            else discord.ButtonStyle.gray
        )
        self.btn4v4.style = (
            discord.ButtonStyle.blurple
            if self.count % 4 == 0 and self.count > 4
            else discord.ButtonStyle.gray
        )
        self.btn6v6.style = (
            discord.ButtonStyle.blurple
            if self.count % 6 == 0 and self.count > 6
            else discord.ButtonStyle.gray
        )
        print(self.children)

    @discord.ui.button(label="FFA", style=discord.ButtonStyle.blurple)
    async def btnffa(self, button: discord.ui.Button, interaction: Interaction):
        if not canVote(self.bot, button.label.lower(), interaction.user.mention):
            return await interaction.respond("Can't vote on that", ephemeral=True)

        vote(self.bot, button.label.lower(), interaction.user)
        await interaction.respond("Voted for FFA", ephemeral=True)

        if isDecided(self.bot):
            await interaction.channel.send(startMogi(self.bot))

    @discord.ui.button(label="2v2")
    async def btn2v2(self, button: discord.ui.Button, interaction: Interaction):
        if not canVote(self.bot, button.label.lower(), interaction.user.mention):
            return await interaction.respond("Can't vote on that", ephemeral=True)

        vote(self.bot, button.label.lower(), interaction.user)
        await interaction.respond("Voted for 2v2", ephemeral=True)

        if isDecided(self.bot):
            await interaction.channel.send(startMogi(self.bot))

    @discord.ui.button(label="3v3")
    async def btn3v3(self, button: discord.ui.Button, interaction: Interaction):
        if not canVote(self.bot, button.label.lower(), interaction.user.mention):
            return await interaction.respond("Can't vote on that", ephemeral=True)

        vote(self.bot, button.label.lower(), interaction.user)
        await interaction.respond("Voted for 3v3", ephemeral=True)

        if isDecided(self.bot):
            await interaction.channel.send(startMogi(self.bot))

    @discord.ui.button(label="4v4")
    async def btn4v4(self, button: discord.ui.Button, interaction: Interaction):
        if not canVote(self.bot, button.label.lower(), interaction.user.mention):
            return await interaction.respond("Can't vote on that", ephemeral=True)

        vote(self.bot, button.label.lower(), interaction.user)
        await interaction.respond("Voted for 4v4", ephemeral=True)

        if isDecided(self.bot):
            await interaction.channel.send(startMogi(self.bot))

    @discord.ui.button(label="6v6")
    async def btn6v6(self, button: discord.ui.Button, interaction: Interaction):
        if not canVote(self.bot, button.label.lower(), interaction.user.mention):
            return await interaction.respond("Can't vote on that", ephemeral=True)

        vote(self.bot, button.label.lower(), interaction.user)
        await interaction.respond("Voted for 6v6", ephemeral=True)

        if isDecided(self.bot):
            await interaction.channel.send(startMogi(self.bot))


class start(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @slash_command(name="start", guild_only=True)
    async def start(self, ctx: ApplicationContext):
        if len(self.bot.mogi["players"]) > 12:
            return await ctx.respond("Cant start with more than 12 players")
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

        self.bot.mogi["voting"] = True
        self.bot.mogi["locked"] = True

        global player_count
        player_count = len(self.bot.mogi["players"])
        view = Menu(self.bot, player_count)
        view.update_styles()
        await ctx.respond(f"Voting start!\n ||{''.join(self.bot.mogi['players'])}||", view=view)

    @slash_command(
        name="force_start",
        description="When voting did not work - force start the mogi with a given format",
        guild_only=True,
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
        self.bot.mogi["running"] = True
        self.bot.mogi["locked"] = True
        self.bot.mogi["voting"] = False
        self.bot.mogi["votes"] = {key: 0 for key in self.bot.mogi["votes"]}
        self.bot.mogi["voters"] = []
        self.bot.mogi["subs"] = []

        if format == "ffa":
            for i, player in enumerate(self.bot.mogi["players"]):
                lineup_str += f"`{i+1}:` {player}\n"
                self.bot.mogi["teams"].append([player])
                self.bot.mogi["running"] = True
            return await ctx.respond(lineup_str)

        random.shuffle(self.bot.mogi["players"])
        teams = []
        for i in range(0, len(self.bot.mogi["players"]), int(format[0])):
            teams.append(self.bot.mogi["players"][i : i + int(format[0])])
        self.bot.mogi["teams"] = teams
        for i, item in enumerate(teams):
            lineup_str += f"\n `{i+1}`. {', '.join(item)}"

        await ctx.respond(lineup_str)

    @slash_command(
        name="stop",
        description="Revert to the state before a vote was started",
        guild_only=True,
    )
    async def stop(self, ctx: ApplicationContext):
        if not self.bot.mogi["running"]:
            return await ctx.respond(
                "No running mogi yet. if vote is still in process, it needs to end or be force started before it can be stopped"
            )
        if len(self.bot.mogi["points"]):
            return await ctx.respond(
                "The mogi is already in the process of MMR calculation"
            )
        self.bot.mogi["running"] = False
        self.bot.mogi["teams"] = []
        self.bot.mogi["format"] = ""
        self.bot.mogi["locked"] = False
        self.bot.mogi["votes"] = {key: 0 for key in self.bot.mogi["votes"]}
        self.bot.mogi["voters"] = []
        self.bot.mogi["voting"] = False
        self.bot.mogi["subs"] = []

        await ctx.respond("The mogi has been stopped, use /start to start it again")
        await ctx.send(f"Debug:\nVotes:{self.bot.mogi['votes']}")


def setup(bot: commands.Bot):
    bot.add_cog(start(bot))
