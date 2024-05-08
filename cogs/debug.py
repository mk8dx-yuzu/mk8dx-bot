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
        
def setup(bot: commands.Bot):
    bot.add_cog(debug(bot))