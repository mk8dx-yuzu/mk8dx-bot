import discord
from discord import slash_command, Option, ApplicationContext
from discord.ext import commands

class help(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @slash_command(name="help", description="A summary of most of the commands to help")
    async def help(self, ctx: ApplicationContext):
        embed=discord.Embed(title="Help", description="Here you can find a brief summary of common commands.", color=discord.Color.blue())
        embed.set_thumbnail(url="https://raw.githubusercontent.com/mk8dx-yuzu/mk8dx-yuzu.github.io/main/public/favicon/ms-icon-310x310.png")
        embed.add_field(name="`/join`", value="Join an open or unlocked mogi", inline=False)
        embed.add_field(name="`/leave`", value="Leave the mogi", inline=False)
        embed.add_field(name="`/l`", value="List all players in the current mogi", inline=False)
        embed.add_field(name="`/teams`", value="Show teams in the mogi", inline=False)
        embed.add_field(name="`/player`", value="View your summarized stats", inline=False)
        embed.add_field(name="`/mmr`", value="View someone's MMR", inline=False)
        embed.add_field(name="`/leaderboard`", value="Show the leaderboard", inline=False)
        embed.add_field(name="`/open`", value="Start a new mogi", inline=False)
        embed.add_field(name="`/close`", value="End the current mogi", inline=False)

        embed.set_footer(text="Yuzu Online", icon_url="https://images-ext-1.discordapp.net/external/ymL8nMKRGEJwQZNCLRuCAbeHxt3n3HYA0XTD-JUW4m4/https/cdn.discordapp.com/icons/1084911987626094654/a_f51d88cf4421676675437f9cf4fbbff6.gif")

        await ctx.respond(embed=embed)

    @commands.command(name="changename")
    async def changename(self, ctx: commands.Context):
        with open("media/howtochangeusername.gif", "rb") as f:
            media = discord.File(f)
            await ctx.send(file=media)
        
    @commands.command(name="lan")
    async def changename(self, ctx: commands.Context):
        with open("media/lan.png", "rb") as f:
            media = discord.File(f)
            await ctx.send(file=media)
        
def setup(bot: commands.Bot):
    bot.add_cog(help(bot))