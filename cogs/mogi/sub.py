import discord
from discord import Option, ApplicationContext, SlashCommandGroup, slash_command
from discord.ext import commands
from discord.utils import get

from cogs.extras.replacement_logic import replace, swap
from cogs.extras.utils import is_mogi_manager

class sub(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    replace = SlashCommandGroup(name = "replace", description = "sub or swap players")

    @replace.command(name="swap", description="Swap 2 players with each other")
    @is_mogi_manager()
    async def swap(self, ctx: ApplicationContext, player1 = Option(str, name = "player1", description = "use @ mention"), player2 = Option(str, name = "player2", description = "use @ mention")):
        if not self.bot.mogi["running"]:
            return await ctx.respond("No running mogi")
        self.bot.mogi["players"] = swap(self.bot.mogi["players"], player1, player2)
        self.bot.mogi["teams"] = swap(self.bot.mogi["teams"], player1, player2)
        await ctx.respond(f"Swapped {player1} and {player2}")

    @replace.command(name="sub", description="Replace a player in the mogi, dismissing mmr loss for the subbing player")
    @is_mogi_manager()
    async def sub(
        self,
        ctx: ApplicationContext,
        player = Option(
            str,
            name="player",
            description="who to replace (input @ discord mention)",
            required=True,
        ),
        sub = Option(
            str,
            name="sub",
            description="subbing player (input @ discord mention)",
            required=True,
        ),
    ):
        await ctx.response.defer()

        if not len(self.bot.mogi["players"]):
            return await ctx.respond("no players", ephemeral=True)
        if not len(self.bot.mogi["teams"]):
            return await ctx.respond("No teams decided yet")
        if sub in self.bot.mogi["players"]:
            return await ctx.respond("This sub is already in the mogi")

        self.bot.mogi["players"] = replace(self.bot.mogi["players"], player, sub)
        self.bot.mogi["teams"] = replace(self.bot.mogi["teams"], player, sub)

        await get(ctx.guild.members, id=int(sub.strip("<@!>"))).add_roles(get(ctx.guild.roles, name="InMogi"))
        await get(ctx.guild.members, id=int(player.strip("<@!>"))).remove_roles(get(ctx.guild.roles, name="InMogi"))

        self.bot.mogi["subs"].append(sub)

        await ctx.respond(f"Subbed {player} with {sub} if applicable")

    @replace.command(name="unsub")
    @is_mogi_manager()
    async def unsub(self, ctx: ApplicationContext, player = discord.Option(name="player", description="@ mention")):
        if player not in self.bot.mogi["subs"]:
            return await ctx.respond("Player is not in subs")
        self.bot.mogi["subs"].remove(player)
        await ctx.respond(f"Removed {player} from subs.")

        
def setup(bot: commands.Bot):
    bot.add_cog(sub(bot))