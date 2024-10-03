import os
import discord
import pymongo
from pymongo import collection, database
from discord import slash_command, Option, ApplicationContext, SlashCommandGroup
from discord.ext import commands
from discord.utils import get

from cogs.extras.utils import is_admin
from cogs.extras.ranks import ranks

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.db: database.Database = self.bot.db
        self.players: collection.Collection = self.bot.players
        self.archived: collection.Collection = self.bot.archived

    edit = SlashCommandGroup(name = "edit", description = "edit player data")

    @edit.command(
        name="any",
        description="Edit a player's MMR. Wins/Losses and MMR History can be updated accordingly.",
    )
    @is_admin()
    async def any(
        self,
        ctx: ApplicationContext,
        name = Option(
            str,
            name="player",
            description="Which player's record to modify",
            required=True,
        ),
        stat = Option(
            str,
            name="stat",
            description="new MMR value",
            required=True,
            choices=[
                "name",
                "mmr",
                "wins",
                "losses",
                "discord",
            ],
        ),
        new_value = Option(
            name="value",
            description="new value",
            required=True,
        ),
        calc = Option(
            str,
            name="calc",
            description="type 'y' or 'n' | add to wins/losses and history",
            required=True,
            choices=["y", "n"]
        ),
    ):
        player = self.players.find_one({"name": name})
        if stat in ["mmr", "wins", "losses"]:
            new_value = int(new_value)
        if stat in ["name", "discord"]:
            new_value = str(new_value)
            await ctx.respond(f"Updated {name}s {stat} to {new_value}")
            
        if stat == "mmr":
            new_value = int(new_value)
            delta = int(new_value) - int(player["mmr"])
            self.players.update_one({"name": name}, {"$set": {f"mmr": new_value}})
            if calc == 'y':
                self.players.update_one(
                    {"name": f"{player['name']}"}, {"$push": {f"history": delta}}
                )
                self.players.update_one(
                    {"name": name}, {"$inc": {f"{'wins' if delta >= 0 else 'losses'}": 1}}
                )
            return await ctx.respond(f"Sucessfully edited {name}s MMR to {new_value}")
        self.players.update_one({"name": name}, {"$set": {stat: new_value}})

    @edit.command(name="mmr")
    @is_admin()
    async def mmr(
        self, ctx: ApplicationContext, 
        player = Option(str, name="player", description="username of the player"), 
        change = Option(int, name="change", description="mmr delta (integer)")
    ):
        if not isinstance(change, int):
            return await ctx.respond("Change is not a valid integer")
        current_mmr = self.players.find_one({"name": player}).get("mmr")
        if not current_mmr:
            return await ctx.respond("Couldn't find that player")
        self.players.update_one({"name": player}, {"$set": {"mmr": current_mmr + change}})
        await ctx.respond(f"{player}: {change}MMR, updated to {current_mmr + change}MMR")

    @slash_command(name="remove", description="Remove a player from the leaderboard")
    @is_admin()
    async def remove(
        self,
        ctx: ApplicationContext,
        player=Option(str, description="Name of the player"),
    ):
        user = self.players.find_one({"name": player})
        if not user:
            return await ctx.respond("Couldn't find that player")
        user_discord = user['discord']
        self.players.delete_one({"name": player})
        member: discord.Member = ctx.guild.get_member(int(user_discord))
        if member:
            await member.remove_roles(get(ctx.guild.roles, name="Lounge Player"))
            for item in ranks:
                role = get(ctx.guild.roles, name=f"Lounge {item['name']}")
                if role in member.roles:
                    await member.remove_roles(role)
        await ctx.respond(f"Successfully deleted {player}s player records")

    @slash_command(name="archive", description="archive a player")
    @is_admin()
    async def archive(self, ctx: ApplicationContext, player = Option(
        str,
        name="player",
        description="use username or @ mention"
    )):
        profile = self.players.find_one({"name": player})
        if not profile:
            profile = self.players.find({"discord": player.strip("<@!>")})
        if not profile: return await ctx.respond("Couldn't find that player")

        self.archived.insert_one(self.players.find_one({"discord": player.strip("<@!>")}))
        self.players.delete_one({"discord": player.strip("<@!>")})
        await ctx.respond(f"{player} has been archived")

    @slash_command(name="unarchive", description="unarchive a player")
    @is_admin()
    async def unarchive(self, ctx: ApplicationContext, player = Option(
        str,
        name="player",
        description="use @ mention"
    )):
        self.players.insert_one(self.archived.find_one({"discord": player.strip("<@!>")}))
        self.archived.delete_one({"discord": player.strip("<@!>")})
        await ctx.respond(f"{player} has been unarchived")

    @slash_command(name="add")
    @is_admin()
    async def add(self, ctx: ApplicationContext, player = Option(name="player", description="@ mention")):
        self.bot.mogi["players"].append(player)
        
        if not get(ctx.guild.roles, name="InMogi") in ctx.guild.get_member(int(player.strip("<@>"))).roles:
            await ctx.guild.get_member(int(player.strip("<@>"))).add_roles(get(ctx.guild.roles, name="InMogi"))

        await ctx.respond(f"{player} joined the mogi! (they had no choice)\n {len(self.bot.mogi['players'])} players are in!")

    @slash_command(name="player_cap")
    @is_admin()
    async def player_cap(self, ctx: ApplicationContext, number = Option(int, name="number", required=True)):
        if isinstance(number, int):
            self.bot.mogi["player_cap"] = number
            await ctx.respond(f"Max. Player amount is now {number}")
        else:
            await ctx.respond("Input not a valid integer")

def setup(bot: commands.Bot):
    bot.add_cog(admin(bot))
