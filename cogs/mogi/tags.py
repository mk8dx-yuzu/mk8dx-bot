import discord
from discord import SlashCommandGroup, ApplicationContext, Option, slash_command
from discord.ext import commands
from discord.utils import get

class tags(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    team = SlashCommandGroup(name = "tags", description = "Edit Team tags and apply/remove respective roles")

    @team.command(name="tag", description="set a tag for your own team")
    async def tag(self, ctx: ApplicationContext, tag = Option(str, name="tag", description="what tag to set for your team", required=True)):
        team_i = None
        for i, subarray in enumerate(self.bot.mogi["teams"]):
            if ctx.interaction.user.mention in subarray:
                team_i = i
        if team_i is not None:
            self.bot.mogi["team_tags"][int(team_i)] = tag
        await ctx.respond(f"Team {team_i+1} tag: {tag}")

    @team.command(name = "set", description = "set a tag for any team by number", guild_only=True)
    async def set(
        self, 
        ctx: ApplicationContext, 
        teamnumber = Option(int, name = "teamnumber", description = "which team's tag to set"), 
        tag = Option(str, name = "tag", description = "which tag to set")
        ):
        self.bot.mogi["team_tags"][int(teamnumber)-1] = tag
        await ctx.respond(f"Updated Team {teamnumber}'s tag to {tag}")

    @team.command(name = "apply_roles", description = "assign team roles", guild_only=True)
    async def apply_roles(self, ctx: ApplicationContext):
        await ctx.response.defer()
        if not self.bot.mogi["format"]:
            return ctx.respond("No format chosen yet")
        if self.bot.mogi["format"] != "ffa":
            for i, team in enumerate(self.bot.mogi["teams"]):
                for player in team:
                    await get(ctx.guild.members, id=int(player.strip("<@!>"))).add_roles(
                        get(ctx.guild.roles, name=f"Team {i+1}")
                    )
            return await ctx.respond("Assigned team roles")
        await ctx.respond("format is ffa, not team roles assigned")

    @team.command(name="unapply_roles", guild_only=True)
    async def unapply_roles(self, ctx: ApplicationContext):
        await ctx.response.defer()
        for i in [1, 2, 3, 4, 5]:
            role = get(ctx.guild.roles, name=f"Team {i}")
            for member in role.members:
                await member.remove_roles(role)
        await ctx.respond("Removed team roles")


def setup(bot: commands.Bot):
    bot.add_cog(tags(bot))