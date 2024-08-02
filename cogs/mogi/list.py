import discord
from discord import Option, ApplicationContext, slash_command
from discord.ext import commands
from discord.utils import get

class list(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @slash_command(name="l", description="List all players in the current mogi")
    async def l(self, ctx: ApplicationContext, 
                table = Option(
                    name="table", 
                    description="Omit numbers to copy and paste into a table maker",
                    required=False,
                    choices = ["y"]
                    )):
        if not self.bot.mogi["status"]:
            return await ctx.respond("Currently no open mogi")
        if not self.bot.mogi["players"]:
            return await ctx.respond("Current mogi: \n No players")
        list = "Current mogi:\n"
        for index, player in enumerate(self.bot.mogi["players"]):
            name = get(ctx.guild.members, id=int(player.strip("<@!>"))).display_name
            if table:
                list += f"{name} +\n\n"
            else:
                list += f"*{index+1}.* {name}\n"
        await ctx.respond(list, allowed_mentions=discord.AllowedMentions(users=False))

    @slash_command(name="teams", description="Show teams")
    async def teams(self, ctx: ApplicationContext):
        if not self.bot.mogi["status"]:
            return await ctx.respond("No open mogi", ephemeral=True)
        if not len(self.bot.mogi["teams"]):
            return await ctx.respond("No teams decided yet", ephemeral=True)
        lineup_str = "# Teams \n\n"
        if self.bot.mogi["format"] == "ffa":
            for i, player in enumerate(self.bot.mogi["players"]):
                lineup_str += f"`{i+1}:` {get(ctx.guild.members, id=int(player.strip('<@!>'))).display_name}\n"
        else:
            for i, team in enumerate(self.bot.mogi["teams"]):
                lineup_str += f"{self.bot.mogi['team_tags'][i]}\n"
                team = [get(ctx.guild.members, id=int(player.strip('<@!>'))).display_name for player in team]
                for player in team:   
                    lineup_str += f"{player} +\n"
                lineup_str += "\n"
                    
        await ctx.respond(lineup_str)
        
def setup(bot: commands.Bot):
    bot.add_cog(list(bot))