from discord.ext import commands
from discord import app_commands
from abc import ABC, abstractmethod

class Competition(commands.Cog, ABC):
    """
    Base class for all competition types (Skill, Boss, etc.)
    """
    def __init__(self, bot):
        self.bot = bot
        self.comp_type = self.get_comp_type()
        self.points_column = f"{self.comp_type}_comp_pts"
        self.points_life_column = f"{self.comp_type}_comp_pts_life"
        self.wins_column = f"{self.comp_type}_comp_wins"
        
    @abstractmethod
    def get_comp_type(self):
        """
        Return the competition type (e.g., 'skill', 'boss')
        This is used to determine column names and command prefixes
        """
        pass
        
    @abstractmethod
    def get_comp_name(self):
        """
        Return the human-readable name of the competition type
        """
        pass
        
    @app_commands.command(name="comp-points", description="Fetch the competition points for the user")
    async def comp_points(self, interaction):
        await interaction.response.defer()
        
        user = self.bot.selectOne(f"SELECT discord_id, {self.points_column} FROM member WHERE discord_id_num={interaction.user.id}")
        if user is not None:
            await interaction.followup.send(f"**{interaction.user.name}** you currently have **{user[1]}** points from {self.get_comp_name()} competitions.")
        else:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)

    @app_commands.command(name="comp-leaderboard", description="Show the competition points leaderboard")
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

    @app_commands.command(name="comp-wins", description="Fetch the competition wins for the user")
    async def comp_wins(self, interaction):
        await interaction.response.defer()
        
        user = self.bot.selectOne(f"SELECT discord_id, {self.wins_column} FROM member WHERE discord_id_num={interaction.user.id}")
        if user is not None:
            winsstring = user[1]
            if winsstring:
                wins = winsstring.split(',')
                wincount = len(wins)
                await interaction.followup.send(f"**{interaction.user.name}** you have won **{wincount}** {self.get_comp_name()} competitions:")
                for win in wins:
                    unquoted_win = win.replace('"','')
                    await interaction.followup.send(f" - {unquoted_win.strip()}")
            else:
                await interaction.followup.send(f"**{interaction.user.name}** you have not won any {self.get_comp_name()} competitions yet.")
        else:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)
            
    def add_competition(self, name, winner_id):
        """
        Add a new competition to the database
        
        Args:
            name (str): The name of the competition
            winner_id (int): The ID of the winner
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get the next competition ID
        result = self.bot.selectOne("SELECT MAX(comp_id) FROM competition")
        next_id = 1 if result[0] is None else result[0] + 1
        
        # Insert the new competition
        success = self.bot.execute_query(
            f"INSERT INTO competition (comp_id, comp_name, winner, competition_type) VALUES ({next_id}, '{name}', {winner_id}, '{self.comp_type}')"
        )
        
        if success:
            # Update the winner's points and wins
            self.bot.execute_query(
                f"UPDATE member SET {self.points_column} = {self.points_column} + 1, {self.points_life_column} = {self.points_life_column} + 1 WHERE _id = {winner_id}"
            )
            
            # Get the current wins array
            result = self.bot.selectOne(f"SELECT {self.wins_column} FROM member WHERE _id = {winner_id}")
            if result and result[0]:
                wins = result[0]
                # Add the new win to the array
                wins.append(name)
                # Update the wins array
                self.bot.execute_query(
                    f"UPDATE member SET {self.wins_column} = ARRAY{wins} WHERE _id = {winner_id}"
                )
            else:
                # Initialize the wins array with the new win
                self.bot.execute_query(
                    f"UPDATE member SET {self.wins_column} = ARRAY['{name}'] WHERE _id = {winner_id}"
                )
                
        return success
        
    def get_competitions(self, limit=10):
        """
        Get the most recent competitions
        
        Args:
            limit (int): The maximum number of competitions to return
            
        Returns:
            list: A list of competitions
        """
        return self.bot.selectMany(
            f"SELECT c.comp_id, c.comp_name, m.rsn, c.competition_type FROM competition c "
            f"JOIN member m ON c.winner = m._id "
            f"WHERE c.competition_type = '{self.comp_type}' "
            f"ORDER BY c.comp_id DESC LIMIT {limit}"
        )
        
    @app_commands.command(name="comp-history", description="Show the recent competition history")
    async def comp_history(self, interaction):
        await interaction.response.defer()
        
        competitions = self.get_competitions()
        
        if not competitions:
            await interaction.followup.send(f"No {self.get_comp_name()} competitions have been recorded yet.")
            return
            
        # Format the competition history
        history = f"**Recent {self.get_comp_name()} Competitions**\n\n"
        
        for comp_id, comp_name, winner_rsn, comp_type in competitions:
            history += f"**{comp_name}** - Won by **{winner_rsn}**\n"
            
        await interaction.followup.send(history) 