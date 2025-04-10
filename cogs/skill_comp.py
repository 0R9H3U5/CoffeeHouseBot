from discord.ext import commands
from discord import app_commands
from cogs.competition import Competition
import discord
import wom

class SkillComp(Competition):
    """
    Logic for all skill competition command handling
    """
    def __init__(self, bot):
        self.bot = bot
        self.comp_type = self.get_comp_type()
        self.points_column = f"{self.comp_type}_comp_pts"
        self.points_life_column = f"{self.comp_type}_comp_pts_life"
    
    def get_comp_type(self):
        """
        Return the competition type
        """
        return "skill"
    
    def get_comp_name(self):
        """
        Return the human-readable name of the competition type
        """
        return "skill week"
    
    @app_commands.command(name="skill-comp-points", description="Fetch the skill competition points for the user")
    async def skill_comp_points(self, interaction):
        await self.comp_points(interaction)

    @app_commands.command(name="skill-comp-leaderboard", description="Show the skill competition points leaderboard")
    async def skill_comp_leaderboard(self, interaction):
        await self.comp_leaderboard(interaction)
    
    @app_commands.command(name="skill-comp-wins", description="Fetch the skill competition wins for the user")
    async def skill_comp_wins(self, interaction):
        await self.comp_wins(interaction)

    @app_commands.command(name="skill-comp-history", description="Show the recent skill competition history")
    async def skill_comp_history(self, interaction):
        await self.comp_history(interaction)
    
    @app_commands.command(name="skill-comp-add")
    # @app_commands.describe(
    #     name="The name of the competition",
    #     metric=f"Valid Values: {self.bot.wom_client.enums.Metric.Skills}",
    #     start_date="The start date in YYYY-MM-DD HH:MM format",
    #     end_date="The end date in YYYY-MM-DD HH:MM format",
    #     wom_code="The Wise Old Man group verification code"
    # )
    @app_commands.default_permissions(administrator=True)
    async def skill_comp_add(self, interaction):
        """
        Add a new skill competition
        """
        await self.show_comp_add_modal(interaction, wom.Skills)
    
    @app_commands.command(name="skill-comp-update", description="Update skill competition results")
    @app_commands.default_permissions(administrator=True)
    async def skill_comp_update(self, interaction, comp_id: int, winner: str, second_place: str, third_place: str):
        await self.comp_update(interaction, comp_id, winner, second_place, third_place)

async def setup(bot):
    await bot.add_cog(SkillComp(bot))