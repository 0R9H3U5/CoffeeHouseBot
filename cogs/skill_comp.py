from discord.ext import commands
from discord import app_commands
from cogs.competition import Competition
import discord

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
    
    @app_commands.command(name="skill-comp-add", description="Add a new skill competition")
    @app_commands.default_permissions(administrator=True)
    async def skill_comp_add(self, interaction, name: str, metric: str, start_date: str, end_date: str):
        await self.comp_add(interaction, name, metric, start_date, end_date)
    
    @app_commands.command(name="skill-comp-update", description="Update skill competition results")
    @app_commands.default_permissions(administrator=True)
    async def skill_comp_update(self, interaction, comp_id: int, winner: str, second_place: str, third_place: str):
        await self.comp_update(interaction, comp_id, winner, second_place, third_place)

async def setup(bot):
    await bot.add_cog(SkillComp(bot))