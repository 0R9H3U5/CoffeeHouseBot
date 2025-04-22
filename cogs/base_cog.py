"""
Base cog that provides common functionality for all cogs.

IMPORTANT RULE FOR FUTURE COMMANDS:
All new commands MUST be decorated with @log_command to ensure proper command usage tracking.
Example:
    @app_commands.command(name="your-command")
    @log_command
    async def your_command(self, interaction, *args):
        # Your command code here
"""

import discord
from discord.ext import commands
from discord import app_commands
from functools import wraps
import logging

log = logging.getLogger('discord')

def log_command(func):
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            # Execute the command
            result = await func(self, interaction, *args, **kwargs)
            
            # Get the member's _id from the database
            member = self.bot.selectOne(f"SELECT _id FROM member WHERE discord_id_num = {interaction.user.id}")
            member_id = member[0] if member else None
            
            # Log successful command usage
            self.bot.execute_query(
                f"""
                INSERT INTO command_usage 
                (command_name, member_id, channel_id, guild_id, success, error_message)
                VALUES ('{func.__name__}', {member_id}, {interaction.channel_id}, {interaction.guild_id}, true, NULL)
                """
            )
            
            return result
        except Exception as e:
            # Get the member's _id from the database
            member = self.bot.selectOne(f"SELECT _id FROM member WHERE discord_id_num = {interaction.user.id}")
            member_id = member[0] if member else None
            
            # Log failed command usage
            error_message = str(e).replace("'", "''")  # Escape single quotes for SQL
            self.bot.execute_query(
                f"""
                INSERT INTO command_usage 
                (command_name, member_id, channel_id, guild_id, success, error_message)
                VALUES ('{func.__name__}', {member_id}, {interaction.channel_id}, {interaction.guild_id}, false, '{error_message}')
                """
            )
            raise
    return wrapper

class BaseCog(commands.Cog):
    """
    Base cog class that provides command logging functionality
    """
    def __init__(self, bot):
        self.bot = bot 

async def setup(bot):
    await bot.add_cog(BaseCog(bot)) 