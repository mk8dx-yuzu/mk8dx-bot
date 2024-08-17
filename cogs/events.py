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
        
        # for the funnies
        if message.channel.id == 1180622895316209664:
            if "dk summit" in message.content.lower() and random.random() < 0.4:
                await message.channel.send(random.choice(["DDDDKKKK SUMIIIIT", "dk summit mentioned", "mitsiku summit"]))
            
            if " election" in message.content.lower() and random.random() < 0.5:
                await message.channel.send(":flag_us:")
            
            if self.bot.user.mention in message.content.lower() and random.random() < 0.4:
                await message.channel.send("Grr stop pinging me")
            
            funnylist = ["is mogi over", "you might lose mmr", "if i sub will i lose mmr", "we don't need a sub", "what are your pc specs", "wanna 1v1"]
            if any(word in message.content.lower() for word in funnylist):
                await message.channel.send(random.choice(funnylist))
            
            if "banned" in message.content.lower():
                await message.channel.send("having fun? get banned loser")
            
            if "my dream" in message.content.lower():
                await message.channel.send("eyo bro, sorry that im writing u directly, U seem to have the File to Zelda totk. i want to play it on my pc but im too dumb to get it running and i dont seem to have the right game files. can u help me out? maybe by a link to the gamefile and a little guide to set that shit up. would be my dream bro")
            
            if "where" in message.content.lower() and "password" in message.content.lower():
                await message.channel.send("plz password mario kart 8 Eu main ? :3 Use Google Translate. I have a hard time understanding English, there is a server that asks me for a password and it goes to this discord, I thought I would find it here. I am from Chile (Spanish)")
            
        if message.content == "dc":
            await message.channel.send("https://autocompressor.net/av1?s=wfinqwL9")

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