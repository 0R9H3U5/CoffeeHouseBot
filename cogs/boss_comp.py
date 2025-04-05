from discord.ext import commands
from discord import app_commands
from cogs.competition import Competition
import discord

class BossComp(Competition):
    """
    Logic for all boss competition command handling
    """
    def __init__(self, bot):
        super().__init__(bot)
        
    def get_comp_type(self):
        """
        Return the competition type
        """
        return "boss"
        
    def get_comp_name(self):
        """
        Return the human-readable name of the competition type
        """
        return "boss week"
        
    @app_commands.command(name="boss-comp-points", description="Fetch the boss competition points for the user")
    async def boss_comp_points(self, interaction):
        await self.comp_points(interaction)

    @app_commands.command(name="boss-comp-leaderboard", description="Show the boss competition points leaderboard")
    async def boss_comp_leaderboard(self, interaction):
        await self.comp_leaderboard(interaction)
        
    @app_commands.command(name="boss-comp-wins", description="Fetch the boss competition wins for the user")
    async def boss_comp_wins(self, interaction):
        await self.comp_wins(interaction)
        
    @app_commands.command(name="boss-comp-history", description="Show the recent boss competition history")
    async def boss_comp_history(self, interaction):
        await self.comp_history(interaction)
        
    @app_commands.command(name="boss-comp-add", description="Add a new boss competition")
    @app_commands.default_permissions(administrator=True)
    async def boss_comp_add(self, interaction, name: str, winner: discord.Member):
        await interaction.response.defer()
        
        # Get the winner's ID from the database
        user = self.bot.selectOne(f"SELECT _id FROM member WHERE discord_id_num={winner.id}")
        if user is None:
            await interaction.followup.send(f"**{winner.name}** is not registered in our database.", ephemeral=True)
            return
            
        # Add the competition
        success = self.add_competition(name, user[0])
        
        if success:
            await interaction.followup.send(f"Added boss competition **{name}** won by **{winner.name}**")
        else:
            await interaction.followup.send("Failed to add the competition.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BossComp(bot)) 