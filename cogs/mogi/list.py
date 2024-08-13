import discord
from discord import Option, ApplicationContext, slash_command
from discord.ext import commands
from discord.utils import get
from pymongo import collection

class list(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.players: collection.Collection = self.bot.players

    @slash_command(name="l", description="List all players in the current mogi")
    async def l(self, ctx: ApplicationContext, 
                context = Option(
                    name="context", 
                    description="extra context to give the list",
                    required=False,
                    choices = ["table", "mmr", "usernames"]
                    )):
        if not self.bot.mogi["status"]:
            return await ctx.respond("Currently no open mogi")
        if not self.bot.mogi["players"]:
            return await ctx.respond("Current mogi: \n No players")
        list = "Current mogi:\n"
        mmrs = []
        for index, player in enumerate(self.bot.mogi["players"]):
            user: discord.Member = get(ctx.guild.members, id=int(player.strip("<@!>")))
            if context == "table":
                list += f"{user.global_name if user.global_name else user.display_name} +\n\n"

            elif context == "mmr":
                mmr = int(self.players.find_one({'discord': player.strip('<@!>')})['mmr'])
                list += f"*{index+1}.* {user.display_name}: {mmr}MMR\n"
                mmrs.append({"name": user.display_name, "mmr": mmr})

                if index+1 == len(self.bot.mogi["players"]):
                    high_mmr = max(mmrs, key=lambda x: x['mmr'])
                    low_mmr = min(mmrs, key=lambda x: x['mmr'])
                    avg_mmr = sum(item['mmr'] for item in mmrs) // len(mmrs)
                    list += f"\nhighest mmr: {high_mmr['name']}: {high_mmr[mmr]}\nlowest mmr: {low_mmr['name']}: {low_mmr[mmr]}\naverage mmr: {avg_mmr}\n"
            
            elif context == "usernames":
                list += f"*{index+1}.* {user.name} \n"
            else:
                list += f"*{index+1}.* {user.display_name}\n"
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