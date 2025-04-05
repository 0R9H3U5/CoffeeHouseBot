import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from enum import Enum

class ProfileField(Enum):
    PREVIOUS_RSN = "previous_rsn"
    ALT_RSN = "alt_rsn"
    LOC = "loc"
    TIMEZONE = "timezone"

class User(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="update_profile", description="Update your member profile information")
    @app_commands.describe(
        field="The field to update",
        value="The new value for the field"
    )
    async def update_profile(
        self,
        interaction: discord.Interaction,
        field: ProfileField,
        value: str
    ):
        try:
            # Validate inputs based on field type
            if field == ProfileField.LOC:
                if len(value) != 2:
                    await interaction.response.send_message(
                        "Location must be a 2-letter country code (e.g. US, UK, CA)",
                        ephemeral=True
                    )
                    return
                value = value.upper()

            elif field == ProfileField.ALT_RSN:
                alt_rsn_list = [name.strip() for name in value.split(',')]
                if any(len(name) > 12 for name in alt_rsn_list):
                    await interaction.response.send_message(
                        "Alternate RSNs cannot be longer than 12 characters",
                        ephemeral=True
                    )
                    return
                value = alt_rsn_list

            elif field == ProfileField.PREVIOUS_RSN:
                if len(value) > 12:
                    await interaction.response.send_message(
                        "Previous RSN cannot be longer than 12 characters",
                        ephemeral=True
                    )
                    return

            elif field == ProfileField.TIMEZONE:
                value = value.upper()

            # Check if user exists in member table
            user = self.bot.selectOne(f"""
                SELECT _id FROM member
                WHERE discord_id_num = {interaction.user.id}
            """)

            if not user:
                await interaction.response.send_message(
                    "You are not registered in the member database. Please contact an admin.",
                    ephemeral=True
                )
                return

            # Execute update
            self.bot.execute_query(f"""
                UPDATE member
                SET {field.value} = '{value}'
                WHERE discord_id_num = {interaction.user.id}
            """)

            # Create response embed
            embed = discord.Embed(
                title="Profile Updated",
                color=discord.Color.green()
            )

            field_name = field.name.replace('_', ' ').title()
            if field == ProfileField.ALT_RSN:
                embed.add_field(name=field_name, value=', '.join(value), inline=True)
            else:
                embed.add_field(name=field_name, value=value, inline=True)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating your profile: {str(e)}",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(User(bot)) 