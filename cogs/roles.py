import json
import discord
from discord import Option, ApplicationContext, slash_command, Interaction
from discord.ext import commands
from discord.utils import get

class roles(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @slash_command(name="give_s1_roles")
    async def give_s1_roles(self, ctx: ApplicationContext):
        guild = self.bot.get_guild(1084911987626094654)
        data = []
        not_found = ""
        with open("./cogs/extras/season_1_end_leaderboard-2024-07-04.json") as file:
            data = json.loads(file.read())
        for player in data:
            user =  guild.get_member(int(player["discord"]))
            if user:
                await user.add_roles(get(ctx.guild.roles, name="Season 1 Player"))
            else: not_found += f"{player['discord']}\n"
        await ctx.respond(f"Could'nt find these players: \n {not_found}")

def setup(bot: commands.Bot):
    bot.add_cog(roles(bot))