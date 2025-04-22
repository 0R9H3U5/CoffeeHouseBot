from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import wom
import traceback
from discord.ui import Modal, TextInput
from enum import Enum
import discord
from typing import Optional, Union, Literal, List, Any
import logging
from cogs.base_cog import log_command

log = logging.getLogger('discord')

class CompetitionType(Enum):
    SKILL = "skill"
    BOSS = "boss"
###
# TODO: Update tests
# TODO: Add link to wom comp to comp_add modal
###
class CompetitionModal(Modal, title="Add New Competition"):
    """
    Modal for collecting competition details
    """
    def __init__(self, competition_cog, comp_type, comp_values):
        super().__init__()
        self.competition_cog = competition_cog
        self.comp_type = comp_type
        
        # Add text inputs
        self.name_input = TextInput(
            label="Competition Name",
            placeholder="Enter a name for the competition",
            required=True,
            max_length=50
        )
        self.add_item(self.name_input)
        
        # Format the metric values for display
        metric_values = [str(metric) for metric in comp_values]
        metric_placeholder = ", ".join(metric_values[0:3])
        
        self.metric_input = TextInput(
            label="Metric",
            placeholder=metric_placeholder,
            required=True,
            max_length=50
        )
        self.add_item(self.metric_input)
        
        self.start_date_input = TextInput(
            label="Start Date (YYYY-MM-DD HH:MM UTC)",
            placeholder="2023-01-01 00:00",
            required=True,
            max_length=16
        )
        self.add_item(self.start_date_input)
        
        self.end_date_input = TextInput(
            label="End Date (YYYY-MM-DD HH:MM UTC)",
            placeholder="2023-01-07 23:59",
            required=True,
            max_length=16
        )
        self.add_item(self.end_date_input)
    
    async def on_submit(self, interaction):
        # Defer the interaction first
        await interaction.response.defer()
        
        # Get values from inputs
        name = self.name_input.value
        metric = self.metric_input.value
        start_date = self.start_date_input.value
        end_date = self.end_date_input.value
        
        try:
            # Parse the dates in UTC
            start = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
            
            # Get the next competition ID
            result = self.competition_cog.bot.selectOne("SELECT MAX(comp_id) FROM competition")
            next_id = 1 if result[0] is None else result[0] + 1
            
            # Insert the new competition
            success = self.competition_cog.bot.execute_query(
                f"INSERT INTO competition (comp_id, comp_name, comp_type, metric, start_date, end_date) "
                f"VALUES ({next_id}, '{name}', '{self.comp_type.value}', '{metric}', '{start_date}', '{end_date}')"
            )
            
            if success:                
                try:
                    await self.competition_cog.bot.wom_client.start()
                    # Use the bot's WOM client
                    # Convert the metric string to a WOM Metric enum
                    wom_metric = None
                    metric_lower = metric.lower().replace(" ", "_")
                    
                    # Try to find a matching metric
                    for metric_enum in wom.Metric:
                        if metric_enum.value == metric_lower:
                            wom_metric = metric_enum
                            break
                    
                    # If no match found, try to find a partial match
                    if wom_metric is None:
                        for metric_enum in wom.Metric:
                            if metric_lower in metric_enum.value or metric_enum.value in metric_lower:
                                wom_metric = metric_enum
                                break
                    
                    # If still no match, default to Slayer
                    if wom_metric is None:
                        await interaction.followup.send("❌ Invalid metric for WOM competition.", ephemeral=True)
                        return
        
                    result = await self.competition_cog.bot.wom_client.competitions.create_competition(
                        title=name,
                        metric=wom_metric,
                        starts_at=start,
                        ends_at=end,
                        group_id=self.competition_cog.bot.getConfigValue("wom_group_id"),
                        group_verification_code=self.competition_cog.bot.getConfigValue("wom_verification_code")
                    )

                    if result.is_ok:
                        embed = discord.Embed(
                            title=f"✅ Added new {self.competition_cog.get_comp_name(self.comp_type)} competition",
                            description=f"**Name:** {name}\n"
                            f"**Metric:** {metric}\n"
                            f"**Start (UTC):** {start_date}\n"
                            f"**End (UTC):** {end_date}",
                            color=discord.Color.gold()
                        )
                        await interaction.followup.send(embed=embed)
                        await self.competition_cog.bot.wom_client.close()
                    else:
                        await self.competition_cog.bot.wom_client.close()
                        await interaction.followup.send("❌ Failed to create WOM competition.", ephemeral=True)
                except Exception as e:
                    await self.competition_cog.bot.wom_client.close()
                    await interaction.followup.send(f"❌ Error creating WOM competition: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to add competition.", ephemeral=True)
                
        except ValueError:
            await interaction.followup.send(
                "❌ Invalid date format. Please use YYYY-MM-DD HH:MM format in UTC.",
                ephemeral=True
            )

class Competition(commands.Cog):
    """
    Base class for handling all competition types
    """
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    async def check_events_category(self, interaction: discord.Interaction) -> bool:
        """
        Check if the command is being used in a channel within the EVENTS & COMPETITIONS category
        """
        return await self.bot.get_cog("InterCogs").check_category(
            interaction,
            "EVENTS & COMPETITIONS"
        )
    
    def get_points_column(self, comp_type: CompetitionType):
        """
        Get the points column name for the given competition type
        """
        return f"{comp_type.value}_comp_pts"
    
    def get_points_life_column(self, comp_type: CompetitionType):
        """
        Get the lifetime points column name for the given competition type
        """
        return f"{comp_type.value}_comp_pts_life"
    
    def get_comp_name(self, comp_type: CompetitionType):
        """
        Get the human-readable name for the given competition type
        """
        return f"{comp_type.value.title()} Week"
    
    @app_commands.command(name="comp-points", description="Fetch the competition points for the user")
    @app_commands.describe(comp_type="The type of competition (skill or boss)")
    @log_command
    async def comp_points(self, interaction, comp_type: CompetitionType):
        if not await self.check_events_category(interaction):
            return
        await interaction.response.defer()
        
        points_column = self.get_points_column(comp_type)
        user = self.bot.selectOne(f"SELECT discord_id, {points_column} FROM member WHERE discord_id_num={interaction.user.id}")
        if user is not None:
            await interaction.followup.send(f"**{interaction.user.name}** you currently have **{user[1]}** points from {self.get_comp_name(comp_type)} competitions.")
        else:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)

    @app_commands.command(name="comp-leaderboard", description="Show the competition points leaderboard")
    @app_commands.describe(comp_type="The type of competition (skill or boss)")
    @log_command
    async def comp_leaderboard(self, interaction, comp_type: CompetitionType):
        if not await self.check_events_category(interaction):
            return
        await interaction.response.defer()
        
        points_column = self.get_points_column(comp_type)
        # Get all members ordered by points in descending order
        members = self.bot.selectMany(f"SELECT rsn, {points_column} FROM member WHERE {points_column} > 0 ORDER BY {points_column} DESC")
        
        if not members:
            await interaction.followup.send(f"No members have any {self.get_comp_name(comp_type)} competition points yet.")
            return
            
        # Format the leaderboard
        leaderboard = self.format_leaderboard(members)
        await interaction.followup.send(f"```\n{leaderboard}```")

    def format_leaderboard(self, members):
        if not members:
            return "No members found."
            
        # Define column widths
        rank_width = 4
        rsn_width = 25
        points_width = 10
        
        # Create header
        header = f"╔{'═' * rank_width}╦{'═' * rsn_width}╦{'═' * points_width}╗\n"
        header += f"║{'#'.center(rank_width)}║{'RSN'.center(rsn_width)}║{'Points'.center(points_width)}║\n"
        header += f"╠{'═' * rank_width}╬{'═' * rsn_width}╬{'═' * points_width}╣\n"
        
        # Create rows
        rows = ""
        for i, (rsn, points) in enumerate(members, 1):
            rank = str(i).center(rank_width)
            rsn_formatted = str(rsn).center(rsn_width)
            points_formatted = str(points).center(points_width)
            
            # Highlight rows with more than 12 points
            if points > 12:
                rows += f"║{rank}║{rsn_formatted}║{points_formatted}║ ★\n"
            else:
                rows += f"║{rank}║{rsn_formatted}║{points_formatted}║\n"
        
        # Create footer
        footer = f"╚{'═' * rank_width}╩{'═' * rsn_width}╩{'═' * points_width}╝\n"
        
        # Add legend
        legend = "★ = 12 points redeemable for a bond\n"
        legend += f"Total players: {len(members)}"
        
        return header + rows + footer + legend

    @app_commands.command(name="comp-wins", description="Fetch the competition wins for the user")
    @app_commands.describe(comp_type="The type of competition (skill or boss)")
    async def comp_wins(self, interaction, comp_type: CompetitionType):
        if not await self.check_events_category(interaction):
            return
        await interaction.response.defer()
        
        # Get the user's _id from the member table
        user = self.bot.selectOne(f"SELECT _id FROM member WHERE discord_id_num={interaction.user.id}")
        if user is None:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)
            return
            
        # Get the user's competition wins using the foreign key relationship
        wins = self.bot.selectMany(
            f"SELECT comp_name FROM competition WHERE winner = {user[0]} AND comp_type = '{comp_type.value}' ORDER BY comp_id DESC"
        )
        
        if not wins:
            await interaction.followup.send(f"**{interaction.user.name}** you have not won any {self.get_comp_name(comp_type)} competitions yet.")
            return
            
        await interaction.followup.send(f"**{interaction.user.name}** you have won **{len(wins)}** {self.get_comp_name(comp_type)} competitions:")
        for win in wins:
            await interaction.followup.send(f" - {win[0]}")
            
    @app_commands.command(name="comp-add", description="Add a new competition")
    @app_commands.describe(comp_type="The type of competition (skill or boss)")
    @app_commands.default_permissions(administrator=True)
    async def comp_add(self, interaction, comp_type: CompetitionType):
        if not await self.check_events_category(interaction):
            return
        """
        Add a new competition to the database
        """
        comp_values = wom.Skills if comp_type == CompetitionType.SKILL else wom.Bosses
        await self.show_comp_add_modal(interaction, comp_type, comp_values)
    
    async def show_comp_add_modal(self, interaction, comp_type: CompetitionType, comp_values):
        """
        Show the competition add modal to the user
        """
        modal = CompetitionModal(self, comp_type, comp_values)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="comp-update", description="Update competition results")
    @app_commands.describe(
        comp_type="The type of competition (skill or boss)",
        comp_id="The ID of the competition to update",
        winner="RSN of the winner",
        second_place="RSN of second place",
        third_place="RSN of third place"
    )
    @app_commands.default_permissions(administrator=True)
    @log_command
    async def comp_update(self, interaction, comp_type: CompetitionType, comp_id: int, winner: str, second_place: str, third_place: str):
        if not await self.check_events_category(interaction):
            return
            
        """
        Update a competition with the winners
        """
        await interaction.response.defer()
        
        try:
            # Get the competition details
            comp = self.bot.selectOne(
                f"SELECT comp_name, comp_type FROM competition WHERE comp_id = {comp_id}"
            )
            
            if comp is None:
                await interaction.followup.send(f"❌ Competition with ID {comp_id} not found.", ephemeral=True)
                return
                
            if comp[1].lower() != comp_type.value.lower():
                await interaction.followup.send(
                    f"❌ Competition {comp_id} is not a {self.get_comp_name(comp_type)} competition.",
                    ephemeral=True
                )
                return
                
            # Get the member IDs for the winners
            winner_id = self.bot.selectOne(f"SELECT _id FROM member WHERE rsn ILIKE '{winner}'")
            second_id = self.bot.selectOne(f"SELECT _id FROM member WHERE rsn ILIKE '{second_place}'")
            third_id = self.bot.selectOne(f"SELECT _id FROM member WHERE rsn ILIKE '{third_place}'")
            
            if not winner_id or not second_id or not third_id:
                await interaction.followup.send(
                    "❌ One or more of the specified RSNs could not be found in the database.",
                    ephemeral=True
                )
                return
                
            # Update the competition with the winners
            query = f"""
                UPDATE competition 
                SET winner_id = {winner_id[0]}, 
                    second_place_id = {second_id[0]}, 
                    third_place_id = {third_id[0]},
                    updated_at = NOW()
                WHERE comp_id = {comp_id}
            """
            
            if self.bot.execute_query(query):
                await interaction.followup.send(
                    f"✅ Successfully updated {comp[0]} with winners:\n"
                    f"1st: {winner}\n"
                    f"2nd: {second_place}\n"
                    f"3rd: {third_place}"
                )
            else:
                await interaction.followup.send(
                    "❌ Failed to update the competition. Please check the logs for more information.",
                    ephemeral=True
                )
                
        except Exception as e:
            await self.bot.get_cog("InterCogs").handle_error(interaction, e)

    def get_competitions(self, comp_type: CompetitionType, limit=10):
        """
        Get the most recent competitions
        """
        return self.bot.selectMany(
            f"SELECT c.comp_id, c.comp_name, m.rsn, c.comp_type, c.end_date FROM competition c "
            f"JOIN member m ON c.winner = m._id "
            f"WHERE c.comp_type = '{comp_type.value}' "
            f"ORDER BY c.comp_id DESC LIMIT {limit}"
        )
        
    @app_commands.command(name="comp-history", description="Show the recent competition history")
    @app_commands.describe(comp_type="The type of competition (skill or boss)")
    async def comp_history(self, interaction, comp_type: CompetitionType):
        if not await self.check_events_category(interaction):
            return
        await interaction.response.defer()
        
        competitions = self.get_competitions(comp_type)
        
        if not competitions:
            await interaction.followup.send(f"No {self.get_comp_name(comp_type)} competitions have been recorded yet.")
            return
            
        # Format the competition history
        history = f"**Recent {self.get_comp_name(comp_type)} Competitions**\n\n"
        
        for comp_id, comp_name, winner_rsn, comp_type, end_date in competitions:
            # Format the date in dd-mm-yyyy notation in UTC
            formatted_date = end_date.strftime("%d-%m-%Y %H:%M UTC") if end_date else "Unknown"
            history += f"**{comp_name}**  [{formatted_date}] - Won by **{winner_rsn}**\n"
            
        await interaction.followup.send(history)

    @app_commands.command(name="comp-status", description="Check the status of the current competition")
    @log_command
    async def comp_status(self, interaction):
        if not await self.check_events_category(interaction):
            return
        """
        Check the status of the current competition, including top 5 competitors and time remaining
        """
        await interaction.response.defer()
        
        try:
            # Check if WOM client exists and is closed, if so reestablish it
            if not hasattr(self.bot, 'wom_client') or not self.bot.wom_client:
                await self.bot.wom_client.start()
            else:
                try:
                    # Try a simple operation to check if session is alive
                    await self.bot.wom_client.groups.get_details(self.bot.getConfigValue("wom_group_id"))
                except:
                    # If the operation fails, the session is likely closed, so restart it
                    await self.bot.wom_client.start()
            
            # Get the group ID
            group_id = self.bot.getConfigValue("wom_group_id")
            if not group_id:
                await interaction.followup.send("❌ WOM group ID not configured.", ephemeral=True)
                return
            # Get active competitions for the group
            result = await self.bot.wom_client.groups.get_competitions(group_id)
            if not result.is_ok:
                await interaction.followup.send("❌ Failed to fetch competitions from WOM.", ephemeral=True)
                return
            
            competitions = result.unwrap()
            active_competition = None
            
            # Find the first active competition
            for comp in competitions:
                if comp.ends_at > datetime.now(timezone.utc) and comp.starts_at <= datetime.now(timezone.utc):
                    active_competition = comp
                    break

            print(f"active competition: {active_competition}")
            
            if not active_competition:
                embed = discord.Embed(
                    title="No Active Competition",
                    description="*There is currently no active competition.*\n\n"
                              "*Maybe you should start one? Or are you too busy drinking coffee?* ☕",
                    color=discord.Color.dark_grey()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Determine competition type
            comp_type = CompetitionType.SKILL if active_competition.metric in wom.Skills else CompetitionType.BOSS
            
            # Get the competition details
            participants_result = await self.bot.wom_client.competitions.get_details(active_competition.id)
            print(f"participants result: {participants_result}")

            if not participants_result.is_ok:
                await interaction.followup.send("❌ Failed to fetch competition participants.", ephemeral=True)
                return
            
            competition_details = participants_result.unwrap()
            # Sort participations by progress gained in descending order and take top 5
            top_5 = sorted(competition_details.participations, key=lambda x: x.progress.gained, reverse=True)[:5]
            
            # Calculate time remaining
            time_remaining = active_competition.ends_at - datetime.now(timezone.utc)
            days = time_remaining.days
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            
            # Create the embed
            embed = discord.Embed(
                title=f"🏆 {active_competition.title}",
                description=f"**Type:** {self.get_comp_name(comp_type)}\n"
                          f"**Metric:** {active_competition.metric.value.title()}\n"
                          f"**Time Remaining:** {days}d {hours}h {minutes}m\n"
                          f"**Participants:** {competition_details.participant_count}",
                color=discord.Color.gold()
            )
            
            # Add top 5 participants
            if top_5:
                leaderboard = ""
                for i, participant in enumerate(top_5, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    leaderboard += f"{medal} **{participant.player.display_name}** - {participant.progress.gained:,}\n"
                embed.add_field(name="Top 5 Competitors", value=leaderboard, inline=False)
            
            # Add footer with start/end times
            embed.set_footer(
                text=f"Started: {active_competition.starts_at.strftime('%Y-%m-%d %H:%M UTC')} | "
                     f"Ends: {active_competition.ends_at.strftime('%Y-%m-%d %H:%M UTC')}"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error checking competition status: {str(e)}", ephemeral=True)

    @app_commands.command(name="get-recent-comp-metrics", description="Show the metrics of recent competitions")
    @app_commands.describe(comp_type="The type of competition (skill or boss)")
    @log_command
    async def get_recent_comp_metrics(self, interaction, comp_type: CompetitionType):
        if not await self.check_events_category(interaction):
            return
        """
        Show the metrics of recent competitions for the given type
        """
        await interaction.response.defer()
        
        # Set the limit based on competition type
        limit = 5 if comp_type == CompetitionType.SKILL else 3
        
        # Get the recent competitions with their metrics
        competitions = self.bot.selectMany(
            f"SELECT comp_name, metric, end_date FROM competition "
            f"WHERE comp_type = '{comp_type.value}' "
            f"ORDER BY comp_id DESC LIMIT {limit}"
        )
        
        if not competitions:
            await interaction.followup.send(f"No {self.get_comp_name(comp_type)} competitions have been recorded yet.")
            return
            
        # Create an embed to display the metrics
        embed = discord.Embed(
            title=f"{self.get_comp_name(comp_type)} Competition Metrics on Cooldown",
            color=discord.Color.gold()
        )
        
        # Add each competition's metric to the embed
        for comp_name, metric, end_date in competitions:
            # Format the date in dd-mm-yyyy notation in UTC
            formatted_date = end_date.strftime("%d-%m-%Y") if end_date else "Unknown"
            embed.add_field(
                name=f"{comp_name} [{formatted_date}]",
                value=f"**Metric:** {metric}",
                inline=False
            )
            
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Competition(bot)) 