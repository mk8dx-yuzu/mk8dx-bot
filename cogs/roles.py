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
        data = []
        with open("./cogs/extras/season_1_end_leaderboard-2024-07-04.json") as file:
            data = json.loads(file.read())
        for player in data:
            discord_member: discord.Member = get(ctx.guild.members, id=int(player["discord"]))
            discord_member.add_roles(get(ctx.guild.roles, name="Season 1 Player"))
    

def setup(bot: commands.Bot):
    bot.add_cog(roles(bot))