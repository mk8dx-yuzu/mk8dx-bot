import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
intents |= discord.Intents.guilds
intents |= discord.Intents.guild_messages

owners = [769525682039947314]

class customBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    async def close(self):
        for name,cog in self.cogs.items():
            cog._eject(self)
            print(f"Ejected {name}")
        await super().close()

bot = customBot(
    command_prefix=".", case_insensitive = True, help_command = None,
    intents=intents, owner_ids = set(owners), 
    status=discord.Status.online
)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(os.getenv('DISCORD_TOKEN'))