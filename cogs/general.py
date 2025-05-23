import discord
from discord.ext import commands
from discord import app_commands
import datetime

class General(commands.Cog):
    """
    Logic for all general command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="promotion-when", description="Returns next promotion date of requesting member")
    async def promotion_when(self, interaction: discord.Interaction):
        # First, acknowledge the interaction to prevent timeout
        await interaction.response.defer()
        
        # Get user data from database
        user = self.bot.selectOne(
            "SELECT discord_id, membership_level, join_date FROM member WHERE discord_id_num = %s",
            (interaction.user.id,)
        )
        
        if not user:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)
            return
            
        # Convert string date to datetime object if needed
        join_date = user[2]
        if isinstance(join_date, str):
            join_date = datetime.datetime.strptime(join_date, "%Y-%m-%d").date()
            
        next_mem_lvl_date = self.bot.getNextMemLvlDate(user[1], join_date)
        if next_mem_lvl_date is None:
            await interaction.followup.send(f"**{interaction.user.name}** you are already eligible for all ranks.")
        else:
            next_mem_lvl = self.bot.getNextMemLvl(user[1])
            await interaction.followup.send(f"**{interaction.user.name}** you are eligible for promotion to **{next_mem_lvl}** on **{next_mem_lvl_date.strftime('%Y-%m-%d')}**.")

async def setup(bot):
    await bot.add_cog(General(bot))