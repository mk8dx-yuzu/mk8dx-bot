import os
import discord
from discord.ext import commands
from discord.utils import get
import aiohttp
import asyncio
import json

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
    async def test(self, ctx: commands.Context):
        await ctx.send("Hi")

def setup(bot: commands.Bot):
    bot.add_cog(commandos(bot))