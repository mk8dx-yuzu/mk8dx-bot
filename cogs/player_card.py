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
        self.width = 3840  # 4K width
        self.height = 2160  # 4K height
        self.media_path = Path("media")

    def create_card(self, player_data):
        # Load and resize the background image
        background_image_path = self.media_path / "Artboard_12x.png"
        background = Image.open(background_image_path).resize((self.width, self.height))

        # Create base card
        card = Image.new("RGBA", (self.width, self.height))
        card.paste(background, (0, 0))
        draw = ImageDraw.Draw(card)

        try:
            # Scale up font size for 4K resolution
            font = ImageFont.truetype("media/YouTubeSansRegular.otf", 180)

            # Add player name and stats with adjusted positioning
            margin_left = 200
            text_spacing = 300
            draw.text(
                (margin_left, 200),
                self.name,
                fill=(255, 255, 255),
                font=font,
            )
            draw.text(
                (margin_left, 200 + text_spacing),
                f"MMR: {player_data.get('mmr', 'N/A')}",
                fill=(255, 255, 255),
                font=font,
            )
            draw.text(
                (margin_left, 200 + text_spacing * 2),
                f"Wins: {player_data.get('wins', 0)}",
                fill=(255, 255, 255),
                font=font,
            )
            draw.text(
                (margin_left, 200 + text_spacing * 2),
                f"Losses: {player_data.get('losses', 0)}",
                fill=(255, 255, 255),
                font=font,
            )

            # Add rank icon in top right
            rank_icon_path = self.media_path / "Wood-Cup.png"
            if rank_icon_path.exists():
                rank_icon = Image.open(rank_icon_path).convert("RGBA")
                icon_size = (800, 800)  # Larger icon size for 4K
                rank_icon = rank_icon.resize(icon_size)
                icon_padding = 150
                card.paste(
                    rank_icon,
                    (self.width - icon_size[0] - icon_padding, icon_padding),
                    rank_icon,
                )

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
            player = self.players.find_one({"discord": str(ctx.author.id)})

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
