import discord, asyncio
from discord import ApplicationContext, slash_command, Option
from discord.ext import commands
from discord.utils import get
import math
from pymongo import collection

class join(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.players: collection.Collection = self.bot.players

        self.join_sem = asyncio.Semaphore(1)


    @slash_command(name="join", description="Join the current mogi", guild_only=True)
    async def join(self, ctx: ApplicationContext):
        async with self.join_sem:
            if not self.bot.mogi["status"]:
                return await ctx.respond("Currently no mogi open")
            if self.bot.mogi["locked"]:
                return await ctx.respond("The mogi is locked, no joining, leaving or closing until it is unlocked")
            if ctx.author.mention in self.bot.mogi["players"]:
                return await ctx.respond("You are already in the mogi")
            if len(self.bot.mogi["players"]) >= 12:
                return await ctx.respond("The mogi is already full")
            if ctx.author.mention not in self.bot.mogi["players"]:
                self.bot.mogi["players"].append(ctx.author.mention)
            if get(ctx.guild.roles, name="InMogi") not in ctx.author.roles:
                await ctx.user.add_roles(get(ctx.guild.roles, name="InMogi"))
            await ctx.respond(
                f"{ctx.author.name} joined the mogi!\n{len(self.bot.mogi['players'])} players are in!"
                )
    
    @slash_command(name="leave", description="Leave the current mogi", guild_only=True)
    async def leave(self, ctx: ApplicationContext):
        if ctx.author.mention not in self.bot.mogi["players"]:
            return await ctx.respond("You are not in the mogi")
        if self.bot.mogi["locked"]:
            return await ctx.respond("The mogi is locked, no joining, leaving or closing until it is unlocked")
        self.bot.mogi["players"].remove(ctx.author.mention)
        await ctx.user.remove_roles(get(ctx.guild.roles, name="InMogi"))
        await ctx.respond(
            f"{ctx.author.mention} left the mogi!\n{len(self.bot.mogi['players'])} players are in!"
        )
        
    @slash_command(name="joni", description="Join the current mogi", guild_only=True)
    async def joni(self, ctx: ApplicationContext):
        await ctx.respond("buddy you typoed that, its not /joni")
        #self.players.update_one({"discord": f"{ctx.author.id}"}, {"$set": {"mmr": -math.inf}})

    @slash_command(name="kick", description="remove a player from the mogi")
    async def kick(self, ctx: ApplicationContext, player = Option(name="player", description="use @ mention")):
        if self.bot.mogi["running"]:
            return await ctx.respond("Already playing, use /stop to halt the mogi")
        if player not in self.bot.mogi["players"]:
            return await ctx.respond("This user is not in the mogi")
        self.bot.mogi["players"].remove(player)
        await ctx.respond(f"{player} got removed from the mogi (L Bozo)")

def setup(bot: commands.Bot):
    bot.add_cog(join(bot))