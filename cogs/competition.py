from discord.ext import commands
from discord import app_commands
import datetime

class Competition(commands.Cog):
    """
    Base class for all competition types (Skill, Boss, etc.)
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.comp_type = self.get_comp_type()
        self.points_column = f"{self.comp_type}_comp_pts"
        self.points_life_column = f"{self.comp_type}_comp_pts_life"
    
    def get_comp_type(self):
        """
        Return the competition type (e.g., 'skill', 'boss')
        This is used to determine column names and command prefixes
        """
        raise NotImplementedError("Subclasses must implement get_comp_type()")
    
    def get_comp_name(self):
        """
        Return the human-readable name of the competition type
        """
        raise NotImplementedError("Subclasses must implement get_comp_name()")
        
    async def comp_points(self, interaction):
        await interaction.response.defer()
        
        user = self.bot.selectOne(f"SELECT discord_id, {self.points_column} FROM member WHERE discord_id_num={interaction.user.id}")
        if user is not None:
            await interaction.followup.send(f"**{interaction.user.name}** you currently have **{user[1]}** points from {self.get_comp_name()} competitions.")
        else:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)

    async def comp_leaderboard(self, interaction):
        await interaction.response.defer()
        
        # Get all members ordered by points in descending order
        members = self.bot.selectMany(f"SELECT rsn, {self.points_column} FROM member WHERE {self.points_column} > 0 ORDER BY {self.points_column} DESC")
        
        if not members:
            await interaction.followup.send(f"No members have any {self.get_comp_name()} competition points yet.")
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

    async def comp_wins(self, interaction):
        await interaction.response.defer()
        
        # Get the user's _id from the member table
        user = self.bot.selectOne(f"SELECT _id FROM member WHERE discord_id_num={interaction.user.id}")
        if user is None:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)
            return
            
        # Get the user's competition wins using the foreign key relationship
        wins = self.bot.selectMany(
            f"SELECT comp_name FROM competition WHERE winner = {user[0]} AND competition_type = '{self.comp_type}' ORDER BY comp_id DESC"
        )
        
        if not wins:
            await interaction.followup.send(f"**{interaction.user.name}** you have not won any {self.get_comp_name()} competitions yet.")
            return
            
        await interaction.followup.send(f"**{interaction.user.name}** you have won **{len(wins)}** {self.get_comp_name()} competitions:")
        for win in wins:
            await interaction.followup.send(f" - {win[0]}")
            
    async def comp_add(self, interaction, name: str, metric: str, start_date: str, end_date: str):
        """
        Add a new competition to the database
        
        Args:
            name (str): The name of the competition
            metric (str): The metric being measured (e.g., 'Total XP', 'Kill Count')
            start_date (str): The start date in YYYY-MM-DD HH:MM format
            end_date (str): The end date in YYYY-MM-DD HH:MM format
        """
        await interaction.response.defer()
        
        try:
            # Parse the dates
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M")
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M")
            
            # Get the next competition ID
            result = self.bot.selectOne("SELECT MAX(comp_id) FROM competition")
            next_id = 1 if result[0] is None else result[0] + 1
            
            # Insert the new competition
            success = self.bot.execute_query(
                f"INSERT INTO competition (comp_id, comp_name, comp_type, metric, start_date, end_date) "
                f"VALUES ({next_id}, '{name}', '{self.comp_type}', '{metric}', '{start_date}', '{end_date}')"
            )
            
            if success:
                await interaction.followup.send(
                    f"✅ Added new {self.get_comp_name()} competition:\n"
                    f"**Name:** {name}\n"
                    f"**Metric:** {metric}\n"
                    f"**Start:** {start_date}\n"
                    f"**End:** {end_date}"
                )
            else:
                await interaction.followup.send("❌ Failed to add competition.", ephemeral=True)
                
        except ValueError:
            await interaction.followup.send(
                "❌ Invalid date format. Please use YYYY-MM-DD HH:MM format.",
                ephemeral=True
            )
            
    async def comp_update(self, interaction, comp_id: int, winner: str, second_place: str, third_place: str):
        """
        Update a competition with the winners
        
        Args:
            comp_id (int): The ID of the competition to update
            winner (str): RSN of the winner
            second_place (str): RSN of second place
            third_place (str): RSN of third place
        """
        await interaction.response.defer()
        
        # Get the competition details
        comp = self.bot.selectOne(
            f"SELECT comp_name, comp_type FROM competition WHERE comp_id = {comp_id}"
        )
        
        if comp is None:
            await interaction.followup.send(f"❌ Competition with ID {comp_id} not found.", ephemeral=True)
            return
            
        if comp[1].lower() != self.comp_type.lower():
            await interaction.followup.send(
                f"❌ Competition {comp_id} is not a {self.get_comp_name()} competition.",
                ephemeral=True
            )
            return
            
        # Get the member IDs for the winners
        winner_id = self.bot.selectOne(f"SELECT _id FROM member WHERE rsn ILIKE '{winner}'")
        second_id = self.bot.selectOne(f"SELECT _id FROM member WHERE rsn ILIKE '{second_place}'")
        third_id = self.bot.selectOne(f"SELECT _id FROM member WHERE rsn ILIKE '{third_place}'")
        
        if not all([winner_id, second_id, third_id]):
            await interaction.followup.send(
                "❌ One or more winners not found in the database. Please check the RSNs.",
                ephemeral=True
            )
            return
            
        # Update the competition with the winners
        success = self.bot.execute_query(
            f"UPDATE competition SET winner = {winner_id[0]}, second_place = {second_id[0]}, third_place = {third_id[0]} "
            f"WHERE comp_id = {comp_id}"
        )
        
        if success:
            # Update points for all winners
            self.bot.execute_query(
                f"UPDATE member SET {self.points_column} = {self.points_column} + 3, "
                f"{self.points_life_column} = {self.points_life_column} + 3 "
                f"WHERE _id = {winner_id[0]}"
            )
            
            self.bot.execute_query(
                f"UPDATE member SET {self.points_column} = {self.points_column} + 2, "
                f"{self.points_life_column} = {self.points_life_column} + 2 "
                f"WHERE _id = {second_id[0]}"
            )
            
            self.bot.execute_query(
                f"UPDATE member SET {self.points_column} = {self.points_column} + 1, "
                f"{self.points_life_column} = {self.points_life_column} + 1 "
                f"WHERE _id = {third_id[0]}"
            )
            
            await interaction.followup.send(
                f"✅ Updated competition results for **{comp[0]}**:\n"
                f"🥇 **Winner:** {winner} (+3 points)\n"
                f"🥈 **Second Place:** {second_place} (+2 points)\n"
                f"🥉 **Third Place:** {third_place} (+1 point)"
            )
        else:
            await interaction.followup.send("❌ Failed to update competition results.", ephemeral=True)
            
    def get_competitions(self, limit=10):
        """
        Get the most recent competitions
        
        Args:
            limit (int): The maximum number of competitions to return
            
        Returns:
            list: A list of competitions
        """
        return self.bot.selectMany(
            f"SELECT c.comp_id, c.comp_name, m.rsn, c.comp_type, c.end_date FROM competition c "
            f"JOIN member m ON c.winner = m._id "
            f"WHERE c.comp_type = '{self.comp_type}' "
            f"ORDER BY c.comp_id DESC LIMIT {limit}"
        )
        
    async def comp_history(self, interaction):
        await interaction.response.defer()
        
        competitions = self.get_competitions()
        
        if not competitions:
            await interaction.followup.send(f"No {self.get_comp_name()} competitions have been recorded yet.")
            return
            
        # Format the competition history
        history = f"**Recent {self.get_comp_name()} Competitions**\n\n"
        
        for comp_id, comp_name, winner_rsn, comp_type, end_date in competitions:
            # Format the date in dd-mm-yyyy notation
            formatted_date = end_date.strftime("%d-%m-%Y") if end_date else "Unknown"
            history += f"**{comp_name}**  [{formatted_date}] - Won by **{winner_rsn}**\n"
            
        await interaction.followup.send(history) 