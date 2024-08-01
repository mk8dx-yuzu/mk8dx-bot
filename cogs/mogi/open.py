import discord, asyncio
from discord import ApplicationContext, slash_command
from discord.ext import commands
from discord.utils import get

from copy import deepcopy

import cogs.extras.mogi_config as config

default_mogi_state = config.mogi_config

class manage(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @slash_command(name="open", description="Start a new mogi", guild_only=True)
    async def open(self, ctx: ApplicationContext):
        if self.bot.mogi["status"]:
            return await ctx.respond("A mogi is already open")
        self.bot.mogi["status"] = True
        await ctx.respond("# Started a new mogi! \n Use /join to participate!")

    @slash_command(name="close", description="Stop the current Mogi if running", guild_only=True)
    async def close(self, ctx: ApplicationContext):
        if not self.bot.mogi["status"]:
            return await ctx.respond("No open mogi")
        await ctx.response.defer()
        if self.bot.mogi["locked"]:
            return await ctx.respond(self.bot.locked_mogi)

        message = await ctx.send(
            f"""
        Closing the mogi discards all teams and points.
        Only do this after the results have been posted.
        Are you sure, {ctx.author.mention} ?
        """
        )

        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.user and str(reaction.emoji) in ("✅", "❌")

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=60, check=check
            )
        except asyncio.TimeoutError:
            await message.edit(content="Confirmation timed out.")
            return await ctx.respond("Timeout")

        if str(reaction.emoji) == "✅":
            await message.edit(content="Closing...")
            self.bot.mogi = deepcopy(default_mogi_state)
            mogi_members = get(ctx.guild.roles, name="InMogi").members
            for member in mogi_members:
                await member.remove_roles(get(ctx.guild.roles, name="InMogi"))

            for i in range(5):
                role = get(ctx.guild.roles, name=f"Team {i+1}")
                for member in role.members:
                    await member.remove_roles(role)
            final_message = "# The mogi has been closed"
        else:
            await message.edit(content="Action canceled.")

        if final_message:
            await ctx.followup.send(final_message)
        
def setup(bot: commands.Bot):
    bot.add_cog(manage(bot))