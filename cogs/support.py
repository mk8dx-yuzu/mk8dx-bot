from discord.ext import commands
import discord

class support(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if not getattr(message.channel, "parent", None) or message.channel.parent.id != 1209934900992679966:
            return
        if len(await message.channel.history().flatten()) > 1:
            return
        
        # give a hint if its less than 50 chars
        if len(message.channel.name) + len(message.content) < 50:
            await message.channel.send("Hi! Your title and/or message are quite short. In case you haven't:\n Add exactly what is going wrong, any errors or messages you encounter, the exact steps you took and how to replicate them. \nAlso make sure you actually read the pinned post: https://discord.com/channels/1084911987626094654/1263002381033934900 and https://discord.com/channels/1084911987626094654/1237872197905809500")
        else:
            await message.channel.send("Hi! Make sure you read the pinned post: https://discord.com/channels/1084911987626094654/1263002381033934900 as well as https://discord.com/channels/1084911987626094654/1237872197905809500\n Both contain many helpful details on topics like:\n- firmware/keys\n- mobile/gpu drivers\n- game file formats\n- setting up the emulator\nand many more. ")

def setup(bot: commands.Bot):
    bot.add_cog(support(bot))
