import discord
from discord import ApplicationContext, slash_command
from discord.ext import commands
from discord.utils import get

class debug(commands.Cog):
    def __init__(self, bot):
            self.bot: commands.Bot = bot

    @slash_command(name="debug")
    async def debug(self, ctx: ApplicationContext):
        await ctx.respond(self.bot.mogi, ephemeral = True)

    @slash_command(name="status", description="See current state of mogi")
    async def status(self, ctx: ApplicationContext):
        if not self.bot.mogi["status"]:
            return await ctx.respond("No running mogi")
        await ctx.respond(f"Currently open mogi: {len(self.bot.mogi['players'])} players")

    @slash_command(name="lock", description="Lock the current mogi from being closed", guild_only=True)
    async def lock(self, ctx: ApplicationContext):
        self.bot.mogi["locked"] = (not self.bot.mogi["locked"])
        await ctx.respond(f"New mogi locking state: {self.bot.mogi['locked']}")

    @slash_command(name="votes", guild_only=True)
    async def votes(self, ctx: ApplicationContext):
        missing = []
        players = []
        for player in self.bot.mogi['players']:
            players.append(int(player.strip("<@!>")))
        for player in players:
            if player not in self.bot.mogi["voters"]:
                missing.append(player)
        if missing:
            string = f"**{len(missing)} player(s) haven't voted yet** \n"
            for missing_player in missing:
                string += f"{get(ctx.guild.members, id=missing_player).mention}\n"
            await ctx.respond(string)
        else: 
            await ctx.respond("No missing votes")

        await ctx.send(self.bot.mogi['votes'])
        
def setup(bot: commands.Bot):
    bot.add_cog(debug(bot))