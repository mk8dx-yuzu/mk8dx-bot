from discord.ext import commands
import discord

class support(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        
        # confirmation-replies to the bot msg in support threads
        if (
            message.reference 
            and message.reference.resolved.author == self.bot.user # is a reply to bot
            and getattr(message.channel, "parent", None) # has parent (is thread)
            and message.channel.parent.id == 1209934900992679966 # in #support
            and message.author == message.channel.owner # reply is by thread creator
        ):
            unconfirmed_tag = [tag for tag in message.channel.parent.available_tags if tag.name == 'unconfirmed'][0]
            if unconfirmed_tag in message.channel.applied_tags:
                await message.channel.edit(applied_tags=[tag for tag in message.channel.applied_tags if tag.name != 'unconfirmed'])
                await message.channel.send("Ok, you verified that you read all help-channels and threads as well as posting rules before posting.")

        # default reply to new support threads
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
