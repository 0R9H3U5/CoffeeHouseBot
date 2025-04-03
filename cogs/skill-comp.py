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