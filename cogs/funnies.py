import random

import discord
from discord.ext import commands

class funnies(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.channel.id == 1180622895316209664:
            if "dk summit" in message.content.lower() and random.random() < 0.4:
                await message.channel.send(random.choice(["DDDDKKKK SUMIIIIT", "dk summit mentioned", "mitsiku summit"]))

            if (" election" in message.content.lower() or message.content.lower().startswith("election")) and random.random() < 0.5:
                await message.channel.send(":flag_us:")

            if self.bot.user.mention in message.content.lower() and random.random() < 0.4:
                await message.channel.send("Grr stop pinging me")

            funnylist = ["is mogi over", "you might lose mmr", "if i sub will i lose mmr", "we don't need a sub", "what are your pc specs", "wanna 1v1"]
            if any(word in message.content.lower() for word in funnylist):
                await message.channel.send(random.choice(funnylist))

            if "banned" in message.content.lower():
                await message.channel.send("having fun? get banned loser")

            if "my dream" in message.content.lower():
                if 0.1 < random.random():
                    return await message.channel.send("eyo bro, sorry that im writing u directly, U seem to have the File to Zelda totk. i want to play it on my pc but im too dumb to get it running and i dont seem to have the right game files. can u help me out? maybe by a link to the gamefile and a little guide to set that shit up. would be my dream bro")
                await message.channel.send("Hello, recently I've downloaded a rom of tears of the kingdom. But when I launch the game with yuzu. He says me this : “The titlekey for this rights ID could not be found” I've tried to get new keys but it's the same results. Can you help me pls ? (Sorry for my English, I'm French)")

            if "where" in message.content.lower() and "password" in message.content.lower():
                await message.channel.send("plz password mario kart 8 Eu main ? :3 Use Google Translate. I have a hard time understanding English, there is a server that asks me for a password and it goes to this discord, I thought I would find it here. I am from Chile (Spanish)")

        if message.content == "dc":
            await message.channel.send("https://autocompressor.net/av1?s=wfinqwL9")
        
def setup(bot: commands.Bot):
    bot.add_cog(funnies(bot))