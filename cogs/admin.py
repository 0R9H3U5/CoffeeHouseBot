import datetime
import sys
from discord.ext import commands
from discord.ext.tasks import loop
from discord import app_commands
import discord
from cogs.base_cog import log_command
from enum import Enum

class TimePeriod(Enum):
    WEEK = "Week"
    MONTH = "Month"
    YEAR = "Year"
    ALL_TIME = "All-Time"

class Admin(commands.Cog):
    """
    Logic for all admin command handling
    """
    def __init__(self, bot):
        self.bot = bot

    async def check_leaders_category(self, interaction: discord.Interaction) -> bool:
        """
        Check if the command is being used in a channel within the LEADERS category
        """
        return await self.bot.get_cog("InterCogs").check_category(
            interaction,
            "LEADERS"
        )

    def format_command_stats(self, results, period_name, max_bar_length=30):
        """Format command statistics into a histogram string."""
        # Find the maximum usage count for scaling
        max_usage = max(row[1] for row in results)
        
        histogram = "```\n"
        histogram += f"Command Usage Statistics ({period_name})\n"
        histogram += "=" * 50 + "\n\n"
        
        for command_name, usage_count, success_count, failure_count in results:
            # Calculate success and failure percentages
            success_percent = (success_count / usage_count) * 100
            failure_percent = (failure_count / usage_count) * 100
            
            # Calculate bar lengths
            success_bar_length = int((success_count / max_usage) * max_bar_length)
            failure_bar_length = int((failure_count / max_usage) * max_bar_length)
            
            # Create the bar
            success_bar = "█" * success_bar_length
            failure_bar = "░" * failure_bar_length
            
            # Format the line
            histogram += f"{command_name:<20} {usage_count:>5} uses\n"
            histogram += f"  Success: {success_percent:>5.1f}% {success_bar}\n"
            histogram += f"  Failure: {failure_percent:>5.1f}% {failure_bar}\n\n"
        
        histogram += "```"
        return histogram

    def split_command_stats(self, results, period_name):
        """Split command statistics into pages that fit within Discord's character limit."""
        pages = []
        current_page = []
        current_length = 0
        
        # Header length (including code block markers and formatting)
        header = f"```\nCommand Usage Statistics ({period_name})\n{'=' * 50}\n\n```"
        header_length = len(header)
        
        # Calculate the maximum length for each page (leaving some buffer)
        max_length = 1900  # Discord's limit is 2000, leaving 100 characters buffer
        
        for result in results:
            # Format the command stats
            command_name, usage_count, success_count, failure_count = result
            success_percent = (success_count / usage_count) * 100
            failure_percent = (failure_count / usage_count) * 100
            
            # Format the command entry
            command_entry = (
                f"{command_name:<20} {usage_count:>5} uses\n"
                f"  Success: {success_percent:>5.1f}% {'█' * 30}\n"
                f"  Failure: {failure_percent:>5.1f}% {'░' * 30}\n\n"
            )
            entry_length = len(command_entry)
            
            # If adding this entry would exceed the limit, start a new page
            if current_length + entry_length + header_length > max_length and current_page:
                pages.append(current_page)
                current_page = []
                current_length = 0
            
            current_page.append(result)
            current_length += entry_length
        
        # Add the last page if it has content
        if current_page:
            pages.append(current_page)
        
        return pages

    @app_commands.command(name="command-stats", description="Display command usage statistics (admin only)")
    @app_commands.describe(
        duration="Time period to analyze (Week, Month, Year, All-Time)"
    )
    @log_command
    async def command_stats(self, interaction: discord.Interaction, duration: TimePeriod):
        if not await self.check_leaders_category(interaction):
            return
            
        # Check if user has admin permissions
        if not await self.bot.get_cog("InterCogs").check_permissions(
            interaction,
            required_permissions=['administrator']
        ):
            return
            
        await interaction.response.defer()
        
        try:
            # Calculate the date range based on the selected period
            end_date = datetime.datetime.now()
            if duration == TimePeriod.WEEK:
                start_date = end_date - datetime.timedelta(days=7)
                period_name = "Last Week"
            elif duration == TimePeriod.MONTH:
                start_date = end_date - datetime.timedelta(days=30)
                period_name = "Last Month"
            elif duration == TimePeriod.YEAR:
                start_date = end_date - datetime.timedelta(days=365)
                period_name = "Last Year"
            else:  # ALL_TIME
                start_date = datetime.datetime.min
                period_name = "All Time"
            
            # Query command usage statistics
            query = f"""
                SELECT 
                    command_name,
                    COUNT(*) as usage_count,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failure_count
                FROM command_usage
                WHERE timestamp >= '{start_date}'
                GROUP BY command_name
                ORDER BY usage_count DESC
            """
            
            results = self.bot.selectMany(query)
            
            if not results:
                await interaction.followup.send(f"No command usage data found for the {period_name.lower()}.")
                return
            
            # Split results into pages
            pages = self.split_command_stats(results, period_name)
            
            # Send each page
            for i, page in enumerate(pages, 1):
                page_content = self.format_command_stats(page, period_name)
                if i == 1:
                    await interaction.followup.send(page_content)
                else:
                    await interaction.followup.send(page_content)
            
        except Exception as e:
            await interaction.followup.send(f"Error generating command statistics: {str(e)}", ephemeral=True)

    @app_commands.command(name="shutdown", description="Shutdown the bot (admin only)")
    @log_command
    async def shutdown(self, interaction):
        if not await self.check_leaders_category(interaction):
            return
            
        # Check if user has admin permissions
        if not await self.bot.get_cog("InterCogs").check_permissions(
            interaction,
            required_permissions=['administrator']
        ):
            return
            
        await interaction.response.send_message('**Shutting Down...**')
        self.bot.conn.close()
        await self.bot.close()
        sys.exit(0)
        
    # TODO
    # @loop(seconds=90)
    async def update_disc_roles(self):
        ###
        ## How it will work:
        ## Grab users and check their rank
        ## Check next rank-up date
        ##   if rank-up date has passed update role on disc 
        ##       (up to 3nana, after that only update if mem_level doesn't match disc)
        ##   add to list mems needing osrs rank-up
        ## Print out list of rank-ups to leaders-chat
        #
        # Do we want to store list in database and require confirmation to remove?
        # print('hello')
        all_members = self.bot.selectMany("SELECT rsn, discord_id_num, membership_level, join_date FROM member")
        # print(f'{all_members}')
        if (all_members is not None):
            discord_roles = self.bot.getConfigValue("discord_role_names")            
            for guild in self.bot.guilds:
                if guild.id == self.bot.getConfigValue("test_server_guild_id"):
                    this_guild = guild
                    print(f"Roles: {this_guild.roles}")
            for mem in all_members:
                if int(mem[2]) < 3:
                    # has room to still be promoted
                    expected_lvl_min = self.bot.getExpectedMemLvlByJoinDate(mem[3])
                    try:
                        usr = await this_guild.fetch_member(mem[1])
                    except:
                        print(f'Unable to find {mem[0]} on server using id {mem[1]}')
                    print(f'{usr}\'s roles: {usr.roles}')
                    role_ok = False
                    for role in usr.roles:
                        if role.name.lower() == discord_roles[expected_lvl_min].lower():
                            role_ok = True
                    if not role_ok:
                        print(f"{usr} is currently role {discord_roles[mem[2]]}({mem[2]}) and will be promoted to role {discord_roles[expected_lvl_min]}({expected_lvl_min})")
                        # await usr.add_roles(this_guild.)

async def setup(bot):
    await bot.add_cog(Admin(bot))