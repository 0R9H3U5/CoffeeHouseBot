import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from enum import Enum
from cogs.base_cog import log_command
import datetime

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
            user = self.bot.selectOne(
                "SELECT _id FROM member WHERE discord_id_num = %s",
                (interaction.user.id,)
            )

            if not user:
                await interaction.response.send_message(
                    "You are not registered in the member database. Please contact an admin.",
                    ephemeral=True
                )
                return

            # Execute update
            self.bot.execute_query(
                "UPDATE member SET %s = %s WHERE discord_id_num = %s",
                (field.value, value, interaction.user.id)
            )

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
    
    

    @app_commands.command(name="update-member", description="Update an existing member (admin only)")
    @log_command
    async def update_member(self, interaction, user_rsn: str, update_key: str, update_value: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Only allow updates on certain keys, this prevents new keys from being added
        print(f'Updating user {user_rsn}. Key {update_key} will be set to value {update_value}.')
        if update_key == "join_date":
            update_value = datetime.datetime.strptime(update_value, self.bot.getConfigValue("datetime_fmt"))
        self.bot.execute_query(
            "UPDATE member SET %s = %s WHERE rsn ILIKE %s",
            (update_key, update_value, user_rsn)
        )
        await interaction.followup.send(f'Updated user {user_rsn}. Key {update_key} set to value {update_value}.')

    @app_commands.command(name="set-active", description="Mark a member as active or inactive (admin only)")
    @log_command
    async def set_active(self, interaction, user_rsn: str, is_active: bool):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        # Call the update_member callback function
        await self.update_member.callback(self, interaction, user_rsn, "active", str(is_active).lower())

    @app_commands.command(name="set-onleave", description="Mark a member as on leave or returned (admin only)")
    @log_command
    async def set_onleave(self, interaction, user_rsn: str, is_onleave: bool):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        # Call the update_member callback function
        await self.update_member.callback(self, interaction, user_rsn, "on_leave", str(is_onleave).lower())

    @app_commands.command(name="temp-leave", description="Mark yourself as on temporary leave or returning from leave")
    @app_commands.describe(
        is_leaving="Set to true if going on leave, false if returning from leave",
        note="Optional note about your leave (e.g. expected return date, reason)"
    )
    async def temp_leave(
        self,
        interaction: discord.Interaction,
        is_leaving: bool,
        note: Optional[str] = None
    ):
        try:
            # Check if user exists in member table
            user = self.bot.selectOne(
                "SELECT _id, on_leave, on_leave_notes FROM member WHERE discord_id_num = %s",
                (interaction.user.id,)
            )

            if not user:
                await interaction.response.send_message(
                    "You are not registered in the member database. Please contact an admin.",
                    ephemeral=True
                )
                return

            # If returning from leave, clear the notes
            if not is_leaving:
                note = None

            # Update on_leave status and notes
            self.bot.execute_query(
                "UPDATE member SET on_leave = %s, on_leave_notes = %s WHERE discord_id_num = %s",
                (is_leaving, note, interaction.user.id)
            )

            # Create response embed
            embed = discord.Embed(
                title="Leave Status Updated",
                color=discord.Color.green()
            )

            status = "on temporary leave" if is_leaving else "returned from leave"
            embed.add_field(name="Status", value=f"You are now {status}", inline=False)
            
            if note:
                embed.add_field(name="Leave Note", value=note, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while updating your leave status: {str(e)}",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(User(bot)) 