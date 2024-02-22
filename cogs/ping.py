from discord.ext import commands

class ping(commands.Cog):
    def __init__(self, bot):
            self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(
        f'Logged into Discord as {self.bot.user.name} | ID: {self.bot.user.id} \n'
        f'------'
        )

    @commands.command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("pong")
        
def setup(bot: commands.Bot):
    bot.add_cog(ping(bot))