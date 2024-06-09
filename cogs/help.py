import discord
from discord import slash_command, Option
from discord.ext import commands

class help(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context):
        await ctx.send("this is help")
        
def setup(bot: commands.Bot):
    bot.add_cog(help(bot))