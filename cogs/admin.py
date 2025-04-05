import datetime
import sys
from discord.ext import commands
from discord.ext.tasks import loop
from discord import app_commands

class Admin(commands.Cog):
    """
    Logic for all admin command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shutdown", description="Shutdown the bot (admin only)")
    async def shutdown(self, interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.send_message('**Shutting Down...**')
        self.bot.conn.close()
        await self.bot.close()
        sys.exit(0)

    @app_commands.command(name="sync-commands", description="Sync slash commands without restarting the bot (admin only)")
    async def sync_commands(self, interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Sync commands globally
            print('Syncing commands globally...')
            synced = await self.bot.tree.sync()
            print(f'Synced {len(synced)} commands globally!')
            
            # Also sync to test server if specified
            if "test_server_guild_id" in self.bot.configs:
                guild_id = self.bot.configs["test_server_guild_id"]
                print(f'Syncing commands to test server...')
                
                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    await interaction.followup.send(f"Could not find guild with ID {guild_id}. Make sure the bot is in this server.", ephemeral=True)
                    return
                
                print(f'Found guild: {guild.name}')
                synced = await self.bot.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to test server!')
                
                # List the synced commands
                command_list = "\n".join([f"- {cmd.name}" for cmd in synced])
                await interaction.followup.send(f"✅ Successfully synced {len(synced)} commands to {guild.name}:\n{command_list}")
            else:
                await interaction.followup.send(f"✅ Successfully synced {len(synced)} commands globally.")
        except Exception as error:
            print(f'ERROR: {error}')
            await interaction.followup.send(f"❌ Failed to sync commands: {error}", ephemeral=True)

    @app_commands.command(name="view-member", description="View member info by RSN (admin only)")
    async def view_member(self, interaction, user_rsn: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        user = self.bot.selectOne(f"SELECT * FROM member WHERE rsn ILIKE '{user_rsn}' OR '{user_rsn}' ILIKE ANY (alt_rsn);")
        if (user is None):
            await interaction.followup.send(f'No members found with rsn or alt of {user_rsn}')
            return

        await interaction.followup.send(f"""**RSN:** {user[1]}
**Discord ID:** {user[3]}
**Membership Level:** {self.bot.getConfigValue("mem_level_names")[int(user[4])]}
**Next Promotion Date:** {self.bot.getNextMemLvlDate(user[4], user[5])}
**Skill Comp Points:** {user[11]}
**On Leave:** {user[9]}
**Active:** {user[10]}
**Alts:** {user[8]}
**Previous RSN:** {user[7]}
**Other Notes:** {user[15]}""")

    @app_commands.command(name="update-member", description="Update an existing member (admin only)")
    async def update_member(self, interaction, user_rsn: str, update_key: str, update_value: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Only allow updates on certain keys, this prevents new keys from being added
        print(f'Updating user {user_rsn}. Key {update_key} will be set to value {update_value}.')
        if update_key == "join_date":
            update_value = datetime.datetime.strptime(update_value, self.bot.getConfigValue("datetime_fmt"))
        self.bot.execute_query(f"UPDATE member SET {update_key}={update_value} WHERE rsn ILIKE '{user_rsn}'")
        await interaction.followup.send(f'Updated user {user_rsn}. Key {update_key} set to value {update_value}.')

    @app_commands.command(name="set-active", description="Mark a member as active or inactive (admin only)")
    async def set_active(self, interaction, user_rsn: str, is_active: bool):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        await self.update_member(interaction, user_rsn, "active", is_active)
        await interaction.followup.send(f'{user_rsn} inactive flag set to {is_active}')

    @app_commands.command(name="set-onleave", description="Mark a member as on leave or returned (admin only)")
    async def set_onleave(self, interaction, user_rsn: str, is_onleave: bool):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        await self.update_member(interaction, user_rsn, "on_leave", is_onleave)
        await interaction.followup.send(f'{user_rsn} on_leave flag set to {is_onleave}')

    @app_commands.command(name="reload", description="Reload a cog (admin only)")
    async def reload(self, interaction, module: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # reload a cog
        try:
            if module[:4] != 'cogs':
                module = 'cogs.' + module
            self.bot.reload_extension(module)
            await interaction.followup.send('\N{OK HAND SIGN}')
        except commands.ExtensionError as e:
            await interaction.followup.send(f'{e.__class__.__name__}: {e}')

    # TODO if needed
    # @app_commands.command(name='disc-refresh', description="Update all discord usernames using discord id (admin only)")
    # async def disc_refresh(self, interaction):
    #     # Update all discord usernames using discord id

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