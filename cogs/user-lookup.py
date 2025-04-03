from discord.ext import commands
from discord import app_commands

class userLookup(commands.Cog):
    """
    Logic for all user lookup command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list-members", description="Print out a list of all members")
    async def list_members(self, interaction):
        await interaction.response.defer()
        
        print("list_members")
        all_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member")        
        await interaction.followup.send(f'```\n{self.format_user_list(all_members)}```')

    @app_commands.command(name="list-inactive", description="Print out a list of all inactive members")
    async def list_inactive(self, interaction):
        await interaction.response.defer()
        
        inactive_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member WHERE active=false")
        await interaction.followup.send(f'```\n{self.format_user_list(inactive_members)}```')

    @app_commands.command(name="list-onleave", description="Print out a list of all members marked on leave")
    async def list_onleave(self, interaction):
        await interaction.response.defer()
        
        on_leave_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member WHERE on_leave=true")
        await interaction.followup.send(f'```\n{self.format_user_list(on_leave_members)}```')

    def format_user_list(self, list):
        if not list:
            return "No members found."
            
        # Define column widths
        id_width = 6
        rsn_width = 25
        discord_width = 30
        
        # Create header
        header = f"╔{'═' * id_width}╦{'═' * rsn_width}╦{'═' * discord_width}╗\n"
        header += f"║{'ID'.center(id_width)}║{'RSN'.center(rsn_width)}║{'Discord ID'.center(discord_width)}║\n"
        header += f"╠{'═' * id_width}╬{'═' * rsn_width}╬{'═' * discord_width}╣\n"
        
        # Create rows
        rows = ""
        for mem in list:
            mem_id = str(mem[0]).center(id_width)
            rsn = str(mem[1]).center(rsn_width)
            discord_id = str(mem[2]).center(discord_width)
            rows += f"║{mem_id}║{rsn}║{discord_id}║\n"
        
        # Create footer
        footer = f"╚{'═' * id_width}╩{'═' * rsn_width}╩{'═' * discord_width}╝\n"
        
        # Add count of members
        count = f"Total: {len(list)} members"
        
        return header + rows + footer + count

async def setup(bot):
    await bot.add_cog(userLookup(bot))