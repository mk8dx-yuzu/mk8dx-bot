import os
import discord
import random
from discord.ext import commands, tasks
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.default()
intents |= discord.Intents.guilds
intents |= discord.Intents.messages
intents |= discord.Intents.message_content
intents |= discord.Intents.members

owners = [769525682039947314, 450728788570013721]

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
    status=discord.Status.online, activity=discord.Streaming(name="ones and zeroes", url="https://www.youtube.com/watch?v=xvFZjo5PgG0")
)

@tasks.loop(seconds=15)
async def change_activity():
    activities = [
        discord.Activity(type=discord.ActivityType.listening, name="DK Summit OST"),
        discord.Activity(type=discord.ActivityType.listening, name="Mario Kart 8 Menu Music"),
        discord.Activity(type=discord.ActivityType.playing, name="Mario Kart Wii"),
        discord.Activity(type=discord.ActivityType.playing, name="Mario Kart 7"),
        discord.Activity(type=discord.ActivityType.playing, name="on Wii Rainbow Road"),
        discord.Activity(type=discord.ActivityType.watching, name="Shroomless tutorials"),
        discord.Activity(type=discord.ActivityType.watching, name="DK Summit gapcut tutorials"),
        discord.Streaming(name="ones and zeroes", url="https://www.youtube.com/watch?v=xvFZjo5PgG0&autoplay=1")
    ]
    await bot.change_presence(activity = random.choice(activities))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    change_activity.start()

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(os.getenv('DISCORD_TOKEN'))