import discord
from discord.ext import commands
from discord import app_commands
from typing import Union, Literal, Optional, List, Any
import logging
import re
import datetime

log = logging.getLogger('discord')

class InterCogs(commands.Cog):
    """
    Common functionality to be used between cogs
    """
    def __init__(self, bot):
        self.bot = bot

    async def check_category(
        self, 
        interaction_or_ctx: Union[discord.Interaction, commands.Context], 
        category_name: str,
        error_message: str = None
    ) -> bool:
        """
        Check if the command is being used in a channel within the specified category
        
        Args:
            interaction_or_ctx: Either a discord.Interaction or commands.Context
            category_name: The name of the category to check for
            error_message: Optional custom error message to display
            
        Returns:
            bool: True if the channel is in the specified category, False otherwise
        """
        # Get the channel from either interaction or context
        channel = (
            interaction_or_ctx.channel 
            if isinstance(interaction_or_ctx, discord.Interaction) 
            else interaction_or_ctx.channel
        )
        
        if not channel or not channel.category:
            msg = error_message or f"❌ This command can only be used in channels within the {category_name} category."
            if isinstance(interaction_or_ctx, discord.Interaction):
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            return False
            
        if channel.category.name.upper() != category_name.upper():
            msg = error_message or f"❌ This command can only be used in channels within the {category_name} category."
            if isinstance(interaction_or_ctx, discord.Interaction):
                await interaction_or_ctx.response.send_message(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
            return False
            
        return True

    async def check_permissions(
        self,
        interaction_or_ctx: Union[discord.Interaction, commands.Context],
        required_permissions: List[str] = None,
        required_roles: List[str] = None,
        error_message: str = None
    ) -> bool:
        """
        Check if a user has the required permissions or roles
        
        Args:
            interaction_or_ctx: Either a discord.Interaction or commands.Context
            required_permissions: List of permission names required (e.g., ['administrator'])
            required_roles: List of role names required
            error_message: Optional custom error message to display
            
        Returns:
            bool: True if the user has the required permissions/roles, False otherwise
        """
        user = (
            interaction_or_ctx.user 
            if isinstance(interaction_or_ctx, discord.Interaction) 
            else interaction_or_ctx.author
        )
        
        # Check permissions
        if required_permissions:
            for perm in required_permissions:
                if not getattr(user.guild_permissions, perm, False):
                    msg = error_message or f"❌ You don't have permission to use this command. Required permission: {perm}"
                    if isinstance(interaction_or_ctx, discord.Interaction):
                        await interaction_or_ctx.response.send_message(msg, ephemeral=True)
                    else:
                        await interaction_or_ctx.send(msg)
                    return False
        
        # Check roles
        if required_roles:
            user_roles = [role.name for role in user.roles]
            for role in required_roles:
                if role not in user_roles:
                    msg = error_message or f"❌ You don't have permission to use this command. Required role: {role}"
                    if isinstance(interaction_or_ctx, discord.Interaction):
                        await interaction_or_ctx.response.send_message(msg, ephemeral=True)
                    else:
                        await interaction_or_ctx.send(msg)
                    return False
        
        return True

    def format_sql_array(self, input_string: Union[str, List[str]]) -> str:
        """
        Format a comma-separated string or list as a PostgreSQL array
        
        Args:
            input_string: A string that may contain comma-separated values or a list of values
            
        Returns:
            str: A string representing a PostgreSQL array or 'NULL' if the input is empty
        """
        if not input_string:
            return "NULL"
            
        # Handle the case where input_string is already a list
        if isinstance(input_string, list):
            parts = [part.strip() for part in input_string if part and part.strip()]
        else:
            # Split by comma and clean up
            parts = [part.strip() for part in input_string.split(',') if part.strip()]
            
        if not parts:
            return "NULL"
        
        # Create the array string
        quoted_parts = []
        for part in parts:
            # Escape single quotes in the part
            escaped_part = part.replace("'", "''")
            quoted_parts.append(f"'{escaped_part}'")
        
        return f"ARRAY[{', '.join(quoted_parts)}]"

    def format_money(self, amount, unit="gp"):
        """
        Format a monetary amount in a human-readable format.
        
        Args:
            amount (int): The amount to format
            unit (str, optional): The unit to append. Defaults to "gp".
            
        Returns:
            str: A formatted string with the amount and unit
            
        Examples:
            - 100 gp remains 100 gp
            - 1000 gp becomes 1K gp
            - 10009 gp becomes 10K gp
            - 999500 gp becomes 999.5K gp
            - 2000000 gp becomes 2M gp
            - 2000400 gp becomes 2M gp
            - 755200080 gp becomes 755.2M gp
            - 4000000000 gp becomes 4T gp
        """
        if amount < 1000:
            return f"{amount} {unit}"
        
        # Determine the appropriate unit and divisor
        if amount < 1000000:
            divisor = 1000
            suffix = "K"
            # Convert non-essential digits to zeros
            # For thousands, we want to keep 4 significant digits
            # For example, 999999 becomes 999900
            total_digits = len(str(amount))
            significant_digits = total_digits - 2
            # Calculate the power of 10 to divide by to get the right number of significant digits
            power = total_digits - significant_digits
            if power > 0:
                # Round down to the nearest power of 10
                rounded_amount = (amount // (10 ** power)) * (10 ** power)
            else:
                rounded_amount = amount
        elif amount < 1000000000:
            divisor = 1000000
            suffix = "M"
            
            total_digits = len(str(amount))
            significant_digits = total_digits - 5
            power = total_digits - significant_digits
            if power > 0:
                rounded_amount = (amount // (10 ** power)) * (10 ** power)
            else:
                rounded_amount = amount
        else:
            divisor = 1000000000
            suffix = "T"
            
            total_digits = len(str(amount))
            significant_digits = total_digits - 8
            power = total_digits - significant_digits
            if power > 0:
                rounded_amount = (amount // (10 ** power)) * (10 ** power)
            else:
                rounded_amount = amount
        
        # Calculate the value in the appropriate unit
        value = rounded_amount / divisor
        
        # Format the value with one decimal place
        formatted = f"{value:.1f}"
        
        # Remove trailing .0 if it's a whole number
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        
        return f"{formatted}{suffix} {unit}"

    async def handle_error(
        self,
        interaction_or_ctx: Union[discord.Interaction, commands.Context],
        error: Exception,
        error_message: str = None,
        log_error: bool = True
    ) -> None:
        """
        Handle errors in a consistent way across cogs
        
        Args:
            interaction_or_ctx: Either a discord.Interaction or commands.Context
            error: The exception that occurred
            error_message: Optional custom error message to display
            log_error: Whether to log the error (default: True)
        """
        if log_error:
            log.error(f"Error occurred: {str(error)}", exc_info=True)
            
        msg = error_message or f"❌ An error occurred: {str(error)}"
        
        try:
            if isinstance(interaction_or_ctx, discord.Interaction):
                if not interaction_or_ctx.response.is_done():
                    await interaction_or_ctx.response.send_message(msg, ephemeral=True)
                else:
                    await interaction_or_ctx.followup.send(msg, ephemeral=True)
            else:
                await interaction_or_ctx.send(msg)
        except discord.errors.NotFound:
            log.error("Could not send error message: Interaction no longer valid")

async def setup(bot):
    await bot.add_cog(InterCogs(bot)) 