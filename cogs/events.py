import os
import random
import discord
from discord.ext import commands
import re

class events(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error): 
        if isinstance(error, commands.CommandNotFound): 
            return
        if isinstance(error, discord.errors.CheckFailure):
            return
        else:
            print(f"An uncaught error occured: \n{error} \n")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        
        # delete any unwanted messages in #lounge-information
        if message.channel.id == 1181312934803144724:
            if not message.author.guild_permissions.administrator or not message.author.guild_permissions.moderate_members and not message.content.startswith("/register"):
                await message.delete()

        if message.channel.type == discord.ChannelType.private :
            for hint in ["information", "piracy", "high", "seas", "sea", "yuzu", "download", "link"]:
                if hint in message.content.lower():
                    #await message.channel.send(f"{os.getenv('YUZU_URL')}")
                    return await message.channel.send("The legality of sharing yuzu is unclear to us, so we can't directly hand it out to people. You will have to obtain your own copy.")

def setup(bot: commands.Bot):
    bot.add_cog(events(bot))