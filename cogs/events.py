import random
import discord
from discord.ext import commands

class events(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error): 
        if isinstance(error, commands.CommandNotFound): 
            pass
        else:
            print(f"An error occured: \n{error} \n")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if "dk summit" in message.content.lower() and random.random() < 0.4:
            await message.channel.send(random.choice(["DDDDKKKK SUMIIIIT", "dk summit mentioned", "best track in the game"]))

def setup(bot: commands.Bot):
    bot.add_cog(events(bot))