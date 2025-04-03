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
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        print("list_members")
        all_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member")        
        await interaction.followup.send(f'{self.format_user_list(all_members)}')

    @app_commands.command(name="list-inactive", description="Print out a list of all inactive members")
    async def list_inactive(self, interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        inactive_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member WHERE active=false")
        await interaction.followup.send(f'{self.format_user_list(inactive_members)}')

    @app_commands.command(name="list-onleave", description="Print out a list of all members marked on leave")
    async def list_onleave(self, interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        on_leave_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member WHERE on_leave=true")
        await interaction.followup.send(f'{self.format_user_list(on_leave_members)}')

    def format_user_list(self, list):
        # list is expected to be query results with fields in the following order: _id, rsn, discord_id
        lbl_id = "ID".center(6)
        lbl_rsn = "RSN".center(23)
        userlist = f"{lbl_id}|{lbl_rsn}|     Discord ID\r\n"               
        for mem in list:
            memid = f"{mem[0]}".center(6)
            rsn = f"{mem[1]}".center(23)
            userlist = userlist + f"{memid} {rsn}    {mem[2]}\r\n"
        return userlist

async def setup(bot):
    await bot.add_cog(userLookup(bot))