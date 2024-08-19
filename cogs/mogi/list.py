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
        
        if self.bot.mogi["format"] in ["ffa", ""]:
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
                        list += f"\nhighest mmr: {high_mmr['name']}: {high_mmr['mmr']}\nlowest mmr: {low_mmr['name']}: {low_mmr['mmr']}\naverage mmr: {avg_mmr}\n"
                
                elif context == "usernames":
                    list += f"*{index+1}.* {user.name} \n"
                else:
                    list += f"*{index+1}.* {user.display_name}\n"

        else:
            list = "# Teams \n\n"
            for i, team in enumerate(self.bot.mogi["teams"]):
                list += f"{'## ' if context != 'table' else ''}{self.bot.mogi['team_tags'][i] or f'Team {i+1}'}\n"

                team = [get(ctx.guild.members, id=int(player.strip('<@!>'))) for player in team]
                for player in team:
                    if context == "table":
                        list += f"{player.display_name} +\n"

                    elif context == "mmr":
                        list += f"- {player.display_name}: {int(self.players.find_one({'discord': str(player.id)})['mmr'])}MMR\n"
                        
                    elif context == "usernames":
                        list += f"- {player.name} \n"

                    else:
                        list += f"- {player.display_name}\n"

                list += "\n"
                    
        await ctx.respond(list, allowed_mentions=discord.AllowedMentions(users=False))
        
def setup(bot: commands.Bot):
    bot.add_cog(list(bot))