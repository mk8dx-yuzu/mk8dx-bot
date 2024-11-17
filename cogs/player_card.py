import os
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import discord
from discord import Option, ApplicationContext, slash_command
from discord.ext import commands
from pymongo import collection


class PlayerCardGenerator:
    def __init__(self, name):
        self.name = name
        self.width = 400
        self.height = 600
        self.media_path = Path("media")

    def create_card(self, player_data):
        # Create base card with gradient background
        card = Image.new("RGBA", (self.width, self.height), (44, 47, 51, 255))
        draw = ImageDraw.Draw(card)

        try:
            # Add player name and stats
            font = ImageFont.truetype("arial.ttf", 32)
            draw.text((20, 20), f"Name: {self.name}", fill=(255, 255, 255), font=font)
            draw.text(
                (20, 70),
                f"MMR: {player_data.get('mmr', 'N/A')}",
                fill=(255, 255, 255),
                font=font,
            )
            draw.text(
                (20, 120),
                f"Wins: {player_data.get('wins', 0)}",
                fill=(255, 255, 255),
                font=font,
            )

            # Add rank icon
            rank_icon_path = self.media_path / "Wood-Cup.png"
            if rank_icon_path.exists():
                rank_icon = Image.open(rank_icon_path).convert("RGBA")
                rank_icon = rank_icon.resize((100, 100))
                card.paste(rank_icon, (self.width - 120, self.height - 120), rank_icon)

            # Save to buffer instead of file
            buffer = BytesIO()
            card.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer

        except Exception as e:
            print(f"Error creating card: {e}")
            return None


class PlayerCardCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.players: collection.Collection = self.bot.players

    @slash_command(name="player_card", description="Get your own season 2 player card")
    async def get_player_card(self, ctx: ApplicationContext):
        await ctx.defer()  # Defer response for potentially slow operations

        try:
            # Query player data
            player_id = str(ctx.author.id)
            player = self.players.find_one({"_id": player_id})

            if player is None:
                await ctx.respond(
                    "You have not played any mogis in season 2", ephemeral=True
                )
                return

            # Generate card
            card_generator = PlayerCardGenerator(player.get("name", "Unknown"))
            buffer = card_generator.create_card(player)

            if buffer is None:
                await ctx.respond("Failed to generate player card", ephemeral=True)
                return

            await ctx.respond(file=discord.File(buffer, filename="player_card.png"))

        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(PlayerCardCog(bot))
