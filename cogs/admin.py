import datetime
import sys
from discord.ext import commands
from discord.ext.tasks import loop

class admin(commands.Cog):
    """
    Logic for all admin command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['quit', 'exit'], hidden=True)
    async def shutdown(self, ctx):
        await ctx.send('**Shutting Down...**')
        self.bot.conn.close()
        await self.bot.close()
        sys.exit(0)

#TODO - theres gotta be a better way to do this
    # @commands.has_role('Leader')
    # @commands.command(name="add-member", help="Add a new member", hidden=True)
    # async def add_member(self, ctx, user_rsn, user_discord_id=None, user_time_zone=None, user_notes=None):
    #     myquery = { "rsn": user_rsn }
    #     if (self.bot.user_data.count_documents(myquery) == 0):
    #         user_id = self.bot.getNextUserId()  

    #         #add new member to user_data table      
    #         today = datetime.date.today()
    #         post = {
    #             "_id": user_id,
    #             "rsn": user_rsn,
    #             "discord_id": user_discord_id,
    #             "discord_id_num": self.get_disc_id(ctx, user_discord_id),
    #             "membership_level": "0", 
    #             "l0" : f'{today}',
    #             "l1" : f'{today + datetime.timedelta(14)}', # 2 weeks
    #             "l2" : f'{today + datetime.timedelta(84)}', # 12 weeks
    #             "l3" : f'{today + datetime.timedelta(182)}', # 26 weeks
    #             "l4" : f'{today + datetime.timedelta(365)}', # 52 weeks
    #             "special_status" : None,
    #             "former_rsn" : None,
    #             "alt_rsn" : None,
    #             "on_leave" : False,
    #             "inactive" : False,
    #             "skill_comp" : {
    #                 "points": 0,
    #                 "wins": "",
    #                 "lifetime_pts": 0 },
    #             "notes" : user_notes} 
    #         self.bot.user_data.insert_one(post)
    #         await ctx.channel.send(f'New member {user_rsn} accepted!')
    #         self.bot.updateUsersCounter(user_id)
    #         await ctx.channel.send(f'User Counter is now {user_id}.')
    #     else:
    #         await ctx.channel.send(f'{user_rsn} already exists. Please use update command. Run `!help update-user` for more details.')

# TODO? is this needed?
    # @commands.command(name='add-existing-member', help="""Add an existing member. 
    # Date format must be YYYY-MM-dd
    # Membership level is 0-6 where 0 is smiley, 6 is leader""")
    # # @commands.has_role('Leader')
    # async def add_existing_member(self, ctx, user_rsn, join_date, membership_level=None, user_discord_id=None, user_time_zone=None, user_notes=None):
    #     myquery = { "rsn": user_rsn }
    #     if (self.bot.user_data.count_documents(myquery) == 0):
    #         user_id = self.bot.getNextUserId()
    #         if membership_level is None:
    #             membership_level = "0"

    #         # Create datetime object from specified date
    #         joined = datetime.datetime.strptime(join_date, self.bot.getConfigValue("datetime_fmt"))
    #         disc_id_num = await self.get_disc_id_num(user_discord_id)
    #         print(f'+++++++++++{disc_id_num}')
    #         post = {
    #             "_id": user_id,
    #             "rsn": user_rsn,
    #             "discord_id": user_discord_id,
    #             "discord_id_num": disc_id_num,
    #             "membership_level": membership_level,
    #             "l0" : f'{joined}',
    #             "l1" : f'{joined + datetime.timedelta(14)}', # 2 weeks
    #             "l2" : f'{joined + datetime.timedelta(84)}', # 12 weeks
    #             "l3" : f'{joined + datetime.timedelta(182)}', # 26 weeks
    #             "l4" : f'{joined + datetime.timedelta(365)}', # 52 weeks
    #             "special_status" : None,
    #             "former_rsn" : None,
    #             "alt_rsn" : None,
    #             "on_leave" : False,
    #             "inactive" : False,
    #             "skill_comp" : {
    #                 "points": 0,
    #                 "wins": "",
    #                 "lifetime_pts": 0 },
    #             "notes" : user_notes} 
    #         self.bot.user_data.insert_one(post)
    #         await ctx.channel.send(f'Added member {user_rsn}!')
    #         self.bot.updateUsersCounter(user_id)
    #         await ctx.channel.send(f'User Counter is now {user_id}.')
    #     else:
    #         await ctx.channel.send(f'{user_rsn} already exists. Please use update command. Run `!help update-user` for more details.')

    @commands.command(name='view-member', help="View member info by rsn")
    # @commands.has_role('Leader')
    async def view_member(self, ctx, user_rsn):
        user = self.bot.selectOne(f"SELECT * FROM member WHERE rsn ILIKE '{user_rsn}' OR '{user_rsn}' ILIKE ANY (alt_rsn);")
        if (user is None):
            await ctx.channel.send(f'No members found with rsn or alt of {user_rsn}')
            return

        await ctx.channel.send(f"""**RSN:** {user[1]}
**Discord ID:** {user[3]}
**Membership Level:** {self.bot.getConfigValue("mem_level_names")[int(user[4])]}
**Next Promotion Date:** {self.bot.getNextMemLvlDate(user[4], user[5])}
**Skill Comp Points:** {user[11]}
**On Leave:** {user[9]}
**Active:** {user[10]}
**Alts:** {user[8]}
**Previous RSN:** {user[7]}
**Other Notes:** {user[15]}""")

    @commands.command(name='update-member', help="""Update an existing member""")
    # @commands.has_role('Leader')
    async def update_member(self, ctx, user_rsn, update_key, update_value):
        # Only allow updates on certain keys, this prevents new keys from being added
        print(f'Updating user {user_rsn}. Key {update_key} will be set to value {update_value}.')
        if update_key == "join_date":
            update_value = datetime.datetime.strptime(update_value, self.bot.getConfigValue("datetime_fmt"))
        self.bot.execute_query(f"UPDATE member SET {update_key}={update_value} WHERE rsn ILIKE '{user_rsn}'")
        await ctx.channel.send(f'Updated user {user_rsn}. Key {update_key} set to value {update_value}.')

    @commands.command(name='set-active', help="""Mark a member as active or inactive.""")
    # @commands.has_role('Leader')
    async def set_active(self, ctx, user_rsn, is_active):
        if is_active.lower() in self.bot.getConfigValue("true_values"):
            active = True
        else:
            active = False
        await self.update_member(ctx, user_rsn, "active", active)
        await ctx.channel.send(f'{user_rsn} inactive flag set to {active}')

    @commands.command(name='set-onleave', help="""Mark a member as on leave or returned""")
    # @commands.has_role('Leader')
    async def set_onleave(self, ctx, user_rsn, is_onleave):
        if is_onleave.lower() in self.bot.getConfigValue("true_values"):
            onleave = True
        else:
            onleave = False
        await self.update_member(ctx, user_rsn, "on_leave", onleave)
        await ctx.channel.send(f'{user_rsn} on_leave flag set to {onleave}')

# TODO
    # @commands.command(name='get-disc-id', help="""Get the numerical disc id for user""")
    # # @commands.has_role('Leader')
    # async def get_disc_id(self, ctx, user_disc_id):
    #     return self.get_disc_id_num(user_disc_id)
        
    # def get_disc_id_num(self, user_disc_id):
    #     if user_disc_id is None:
    #         return None
    #     for guild in self.bot.guilds:
    #         if guild.id == self.bot.getConfigValue("test_server_guild_id"):
    #             return guild.get_member_named(user_disc_id).id
    #     return None

    @commands.command(name='reload', hidden=True, invoke_without_command=True)
    async def _reload(self, ctx, *, module):
        # reload a cog
        try:
            if module[:4] != 'cogs':
                module = 'cogs.' + module
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    # TODO if needed
    # @commands.command(name='disc-refresh', hidden=True, invoke_without_command=True)
    # async def _disc_refresh(self, ctx, *, module):
    #     # Update all discord usernames using discord id

#TODO
    @loop(seconds=90)
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

def setup(bot):
    bot.add_cog(admin(bot))