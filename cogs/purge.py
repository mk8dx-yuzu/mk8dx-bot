import discord
from discord import ApplicationContext, slash_command, Option
from discord.ext import commands

import pymongo
from pymongo import collection, database

from cogs.extras.utils import is_admin

class purge(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.players: collection.Collection = self.bot.players

    @slash_command(name="purge_leaderboard", description="flag accounts with no mogis played for deletion, dm them with an option to prevent")
    @is_admin()
    async def purge_leaderboard(self, ctx: ApplicationContext):
        await ctx.interaction.response.defer()

        players_with_no_mogis = list(self.players.find({"mmr": 2000, "wins": 0, "losses": 0, "history": [], "inactive": { "$exists": False }}))
        self.players.update_many({"mmr": 2000, "wins": 0, "losses": 0, "history": [], "inactive": { "$exists": False }}, {"$set": {"inactive": True}})

        missed = 0
        for player in players_with_no_mogis:
            try:
                user = await self.bot.fetch_user(int(player["discord"]))
                await user.send(f"""
                    Hello,
                    You've registered yourself for Yuzu Online's competitive MK8DX Lounge Event as {player['name']}.
                    However, you have not yet played any events. We try to keep the ranking list clean of inactive players, so **we have marked you as 'inactive'**.
                    \n
                    If you don't want your registration deleted, simply **use the '/reactivate' slash command** here or in the server's Lounge channels. This shows us that you still want to play.
                    Otherwise, all registrations marked for deletion **will be removed from the leaderboard** and deleted after about **2 days**.
                    \n
                    Don't worry, even if this happens, you can simply re-register later in https://discord.com/channels/1084911987626094654/1181312934803144724 .
                """)
            except:
                missed += 1
        await ctx.respond(f"Marked {len(players_with_no_mogis)} accounts as inactive and DMed {len(players_with_no_mogis)-missed} users.")

    @slash_command(name="reactivate", description="use this to unmark your account from being inactive if you have not played any events")
    async def reactivate(self, ctx: ApplicationContext):
        self.players.update_one({"discord": str(ctx.interaction.user.id)}, {"$unset": {"inactive": ""}})
        await ctx.respond("Successfully unmarked your account from being inactive!")

    @slash_command(name="delete_inactive_players", description="Delete inactive-marked players from the leaderboard")
    @is_admin()
    async def delete_inactive_players(self, ctx: ApplicationContext):
        
        await ctx.response.defer()
        if self.bot.mogi["locked"]:
            return await ctx.respond(self.bot.locked_mogi)

        message = await ctx.send(
            f"""
        
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
    bot.add_cog(purge(bot))