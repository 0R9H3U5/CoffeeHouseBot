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

    @app_commands.command(name="view-member", description="View member info by RSN (admin only)")
    async def view_member(self, interaction, user_rsn: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Get column names from the database
        columns = self.bot.selectMany("SELECT column_name FROM information_schema.columns WHERE table_name = 'member' ORDER BY ordinal_position")
        column_names = [col[0] for col in columns]
        
        # Query the member data
        user_data = self.bot.selectOne(f"SELECT * FROM member WHERE rsn ILIKE '{user_rsn}' OR '{user_rsn}' ILIKE ANY (alt_rsn);")
        if user_data is None:
            await interaction.followup.send(f'No members found with rsn or alt of {user_rsn}')
            return
            
        # Create a dictionary mapping column names to values
        user = dict(zip(column_names, user_data))
        print(f"user: {user}")
        # Create an embed for the member information
        embed = discord.Embed(
            title=f"Member Information: {user['rsn']}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        # Add member details to the embed
        embed.add_field(name="RSN", value=user['rsn'], inline=True)
        embed.add_field(name="Discord ID", value=user['discord_id'] or "Not linked", inline=True)
        
        # Get membership level name
        try:
            membership_level = self.bot.getConfigValue("mem_level_names")[int(user['membership_level'])]
        except (IndexError, TypeError, ValueError):
            membership_level = "Unknown"
            
        embed.add_field(name="Membership Level", value=membership_level, inline=True)
        
        # Get next promotion date
        next_promotion = self.bot.getNextMemLvlDate(user['membership_level'], user['join_date'])
        if next_promotion:
            next_promotion_str = next_promotion.strftime("%d/%m/%Y")
        else:
            next_promotion_str = "No upcoming promotion"
            
        embed.add_field(name="Next Promotion Date", value=next_promotion_str, inline=True)
        
        # Calculate total competition points (skill + boss)
        skill_comp_pts = user['skill_comp_pts'] or 0
        boss_comp_pts = user['boss_comp_pts'] or 0
        total_comp_pts = skill_comp_pts + boss_comp_pts
        embed.add_field(name="Competition Points", value=str(total_comp_pts), inline=True)
        
        # Format boolean values
        on_leave = "Yes" if user['on_leave'] else "No"
        active = "Yes" if user['active'] else "No"
        
        embed.add_field(name="On Leave", value=on_leave, inline=True)
        embed.add_field(name="Active", value=active, inline=True)
        
        # Format arrays
        alt_rsn = user['alt_rsn']
        if alt_rsn and isinstance(alt_rsn, (list, tuple)) and len(alt_rsn) > 0:
            alt_rsn_str = ", ".join(alt_rsn)
        else:
            alt_rsn_str = "None"
            
        prev_rsn = user['previous_rsn']
        if prev_rsn and isinstance(prev_rsn, (list, tuple)) and len(prev_rsn) > 0:
            prev_rsn_str = ", ".join(prev_rsn)
        else:
            prev_rsn_str = "None"
            
        embed.add_field(name="Alt RSNs", value=alt_rsn_str, inline=False)
        embed.add_field(name="Previous RSNs", value=prev_rsn_str, inline=False)
        
        # Add notes if available
        if user['notes']:
            embed.add_field(name="Other Notes", value=user['notes'], inline=False)
            
        # Set footer with timestamp
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

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