from discord.ext import commands
import discord

class events(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error): 
        if isinstance(error, commands.CommandNotFound): 
            await ctx.send(embed = discord.Embed(description="Command not found.", color=ctx.author.color))
        else:
            print(f"An error occured: \n{error} \n")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pass

def setup(bot: commands.Bot):
    bot.add_cog(events(bot))