from discord.ext import commands
from discord import app_commands

class skillComp(commands.Cog):
    """
    Logic for all skill competition command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skill-comp-points", description="Fetch the skill comp points for the user")
    async def skill_comp_points(self, interaction):
        await interaction.response.defer()
        
        user = self.bot.selectOne(f"SELECT discord_id, skill_comp_pts FROM member WHERE discord_id_num={interaction.user.id}")
        if user is not None:
            await interaction.followup.send(f"**{interaction.user.name}** you currently have **{user[1]}** points from skill week competitions.")
        else:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)

    @app_commands.command(name="skill-comp-leaderboard", description="Show the skill competition points leaderboard")
    async def skill_comp_leaderboard(self, interaction):
        await interaction.response.defer()
        
        # Get all members ordered by skill_comp_pts in descending order
        members = self.bot.selectMany("SELECT rsn, skill_comp_pts FROM member WHERE skill_comp_pts > 0 ORDER BY skill_comp_pts DESC")
        
        if not members:
            await interaction.followup.send("No members have any skill competition points yet.")
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

    # TODO
    # @app_commands.command(name="skill-comp-wins", description="Fetch the skill comp wins for the user")
    # async def skill_comp_wins(self, interaction):
    #     await interaction.response.defer()
    #     
    #     user = self.bot.selectOne(f"SELECT discord_id, skill_comp_wins FROM member WHERE discord_id_num={interaction.user.id}")
    #     if user is not None:
    #         winsstring = user[1]
    #         wins = winsstring.split(',')
    #         wincount = len(wins)
    #         await interaction.followup.send(f"**{interaction.user.name}** you have won **{wincount}** skill week competitions:")
    #         for win in wins:
    #             unquoted_win = win.replace('"','')
    #             await interaction.followup.send(f" - {unquoted_win.strip()}")
    #     else:
    #         await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(skillComp(bot))