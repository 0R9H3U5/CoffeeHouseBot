import datetime
import sys
from discord.ext import commands
from discord.ext.tasks import loop
from discord import app_commands
import discord

class Admin(commands.Cog):
    """
    Logic for all admin command handling
    """
    def __init__(self, bot):
        self.bot = bot

    async def check_leaders_category(self, interaction: discord.Interaction) -> bool:
        """
        Check if the command is being used in a channel within the LEADERS category
        """
        return await self.bot.get_cog("InterCogs").check_category(
            interaction,
            "LEADERS"
        )

    @app_commands.command(name="shutdown", description="Shutdown the bot (admin only)")
    async def shutdown(self, interaction):
        if not await self.check_leaders_category(interaction):
            return
            
        # Check if user has admin permissions
        if not await self.bot.get_cog("InterCogs").check_permissions(
            interaction,
            required_permissions=['administrator']
        ):
            return
            
        await interaction.response.send_message('**Shutting Down...**')
        self.bot.conn.close()
        await self.bot.close()
        sys.exit(0)
        
    # TODO
    # @loop(seconds=90)
    async def update_disc_roles(self):
        ###
        ## How it will work:
        ## Grab users and check their rank
        ## Check next rank-up date
        ##   if rank-up date has passed update role on disc 
        ##       (up to 3nana, after that only update if mem_level doesn't match disc)
        ##   add to list mems needing osrs rank-up
        ## Print out list of rank-ups to leaders-chat
        #
        # Do we want to store list in database and require confirmation to remove?
        # print('hello')
        all_members = self.bot.selectMany("SELECT rsn, discord_id_num, membership_level, join_date FROM member")
        # print(f'{all_members}')
        if (all_members is not None):
            discord_roles = self.bot.getConfigValue("discord_role_names")            
            for guild in self.bot.guilds:
                if guild.id == self.bot.getConfigValue("test_server_guild_id"):
                    this_guild = guild
                    print(f"Roles: {this_guild.roles}")
            for mem in all_members:
                if int(mem[2]) < 3:
                    # has room to still be promoted
                    expected_lvl_min = self.bot.getExpectedMemLvlByJoinDate(mem[3])
                    try:
                        usr = await this_guild.fetch_member(mem[1])
                    except:
                        print(f'Unable to find {mem[0]} on server using id {mem[1]}')
                    print(f'{usr}\'s roles: {usr.roles}')
                    role_ok = False
                    for role in usr.roles:
                        if role.name.lower() == discord_roles[expected_lvl_min].lower():
                            role_ok = True
                    if not role_ok:
                        print(f"{usr} is currently role {discord_roles[mem[2]]}({mem[2]}) and will be promoted to role {discord_roles[expected_lvl_min]}({expected_lvl_min})")
                        # await usr.add_roles(this_guild.)

async def setup(bot):
    await bot.add_cog(Admin(bot))