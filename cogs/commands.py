import os
import discord
from discord.ext import commands
from discord.utils import get
import aiohttp
import asyncio
import json
import random

class commandos(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.httpSession = aiohttp.ClientSession()
        print("Created http session")

    def cog_unload(self):
        asyncio.run_coroutine_threadsafe(
            self.httpSession.close(), self.bot.loop
        ) 
        print("Closed http session")

    @commands.command()
    async def hi(self, ctx: commands.Context):
        await ctx.send("Hi")

    @commands.command()
    async def coin(self, ctx: commands.Context):
        await ctx.send(f"{ctx.author.display_name} flipped a coin, it turned up {'heads' if random.random() > 0.5 else 'tails'}")

def setup(bot: commands.Bot):
    bot.add_cog(commandos(bot))