import discord
from discord import SlashCommandGroup, ApplicationContext, Option, slash_command
from discord.ext import commands
from discord.utils import get

class tags(commands.Cog):
    def __init__(self, bot):
            self.bot: commands.Bot = bot

    tags = SlashCommandGroup(name = "tags", description = "Edit Team tags and apply/remove respective roles")

    @tags.command(name = "set", description = "set a tag for a team")
    async def set(
        self, 
        ctx: ApplicationContext, 
        teamnumber = Option(int, name = "teamnumber", description = "which team's tag to set"), 
        tag = Option(str, name = "tag", description = "which tag to set")
        ):
        self.bot.mogi["team_tags"][int(teamnumber)-1] = tag
        await ctx.respond(f"Updated Team {teamnumber}'s tag to {tag}")

    @tags.command(name = "apply_roles", description = "assign team roles", guild_only=True)
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

    @tags.command(name="unapply_roles", guild_only=True)
    async def unapply_roles(self, ctx: ApplicationContext):
        await ctx.response.defer()
        for i in [1, 2, 3, 4, 5]:
            role = get(ctx.guild.roles, name=f"Team {i}")
            for member in role.members:
                await member.remove_roles(role)
        await ctx.respond("Removed team roles")


def setup(bot: commands.Bot):
    bot.add_cog(tags(bot))