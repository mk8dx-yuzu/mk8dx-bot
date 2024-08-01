import discord, json
from discord import ApplicationContext, slash_command, SlashCommandGroup, Option
from discord.ext import commands
from discord.utils import get

from cogs.extras.utils import is_admin, is_mogi_manager

class debug(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @slash_command(name="status", description="See current state of mogi")
    async def status(self, ctx: ApplicationContext):
        if not self.bot.mogi["status"]:
            return await ctx.respond("No running mogi")
        if self.bot.mogi["voting"]:
            return await ctx.respond("Currently voting")
        if self.bot.mogi["running"]:
            return await ctx.respond(f"Mogi currently playing: {len(self.bot.mogi['players'])} players")
        await ctx.respond(f"Currently open mogi: {len(self.bot.mogi['players'])} players")
    
    @slash_command(name="debug")
    @is_mogi_manager()
    async def debug(self, ctx: ApplicationContext, ephemeral = Option(str, required = False, choices=["y"], default = False)):
        await ctx.respond(self.bot.mogi, ephemeral = True if ephemeral else False)

    @slash_command(name="lock", description="Lock the current mogi from being closed")
    @is_admin()
    async def lock(self, ctx: ApplicationContext):
        self.bot.mogi["locked"] = (not self.bot.mogi["locked"])
        await ctx.respond(f"New mogi locking state: {self.bot.mogi['locked']}")

    @slash_command(name="votes")
    async def votes(self, ctx: ApplicationContext):
        if not self.bot.mogi["voting"]:
            return await ctx.respond("No vote going on")
        missing = []
        for player in self.bot.mogi['players']:
            if player not in self.bot.mogi["voters"]:
                missing.append(player)
        if missing:
            string = f"**{len(missing)} player(s) haven't voted yet** \n"
            for missing_player in missing:
                string += f"{self.bot.get_user(int(missing_player.strip('<@>'))).mention}\n"
            await ctx.respond(string)
        else: 
            await ctx.respond("No missing votes")

        votes = ""
        for key in self.bot.mogi['votes'].keys()
            votes += f"{key}: {self.bot.mogi['votes'][key]}\n"
        await ctx.send(votes)

    @slash_command(name="points_reset", description="Messed up points input? Reset them")
    @is_mogi_manager()
    async def points_reset(self, ctx: ApplicationContext):
        self.bot.mogi["point_count"] = 0
        self.bot.mogi["input_points"] = []
        self.bot.mogi["points"] = []
        self.bot.mogi["calc"] = []
        self.bot.mogi["results"] = []
        self.bot.mogi["points_user"] = ""
        await ctx.respond("Cleared all points", ephemeral = True)
        
    state = SlashCommandGroup(name = "state", description = "concerns self.bot.mogi and saving it as json")

    @state.command(name="save")
    @is_mogi_manager()
    async def save(self, ctx: ApplicationContext):
        with open("persistent/state.json", "w") as f:
            json.dump(self.bot.mogi, f)
            f.close()
        await ctx.respond("saved state")

    @state.command(name="load")
    @is_mogi_manager()
    async def load(self, ctx: ApplicationContext):
        try:
            with open("persistent/state.json", "r") as f:
                self.bot.mogi = json.load(f)
                f.close()
                await ctx.respond("loaded state")
        except:
            return await ctx.respond("Couldn't load state")

def setup(bot: commands.Bot):
    bot.add_cog(debug(bot))