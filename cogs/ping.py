from discord.ext import commands
import discord

class ping(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged into Discord as {self.bot.user.name} | ID: {self.bot.user.id}')
        print("Guilds:")
        for guild in list(self.bot.guilds):
            print(guild.name)
        print("--------")

    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("pong")
        
def setup(bot: commands.Bot):
    bot.add_cog(ping(bot))