import os
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
        if " election" in message.content.lower() and random.random() < 0.5:
            await message.channel.send(":flag_us:")

        if message.channel.type == discord.ChannelType.private :
            for hint in ["high", "seas", "see", "yuzu", "download", "link"]:
                if hint in message.content.lower():
                    await message.channel.send(f"{os.getenv('YUZU_URL')}")
                    await message.channel.send("Please do not share this link with others so that it stays away from big N's eyes. Instead hint others at asking me here in DMs. Thank you")

def setup(bot: commands.Bot):
    bot.add_cog(events(bot))