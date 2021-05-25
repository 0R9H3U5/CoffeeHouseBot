import datetime
import sys
from discord.ext import commands

class admin(commands.Cog):
    """
    Logic for all admin command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['quit', 'exit'], hidden=True)
    async def shutdown(self, ctx):
        await ctx.send('**Shutting Down...**')
        await self.bot.close()
        sys.exit(0)

    # @bot.command(name='add-member', help="Add a new member")
    # @commands.has_role('Leader')
    @commands.command(name="add-member", help="Add a new member")#hidden=True)
    async def add_member(self, ctx, user_rsn, user_discord_id=None, user_time_zone=None, user_notes=None):
        myquery = { "rsn": user_rsn }
        if (self.bot.user_data.count_documents(myquery) == 0):
            user_id = self.bot.getNextUserId()  

            #add new member to user_data table      
            today = datetime.date.today()
            post = {
                "_id": user_id,
                "rsn": user_rsn,
                "discord_id": user_discord_id,
                "membership_level": "0", 
                "l0" : f'{today}',
                "l1" : f'{today + datetime.timedelta(14)}', # 2 weeks
                "l2" : f'{today + datetime.timedelta(84)}', # 12 weeks
                "l3" : f'{today + datetime.timedelta(182)}', # 26 weeks
                "l4" : f'{today + datetime.timedelta(365)}', # 52 weeks
                "l5" : f'{today + datetime.timedelta(365)}', # 52 weeks
                "special_status" : None,
                "former_rsn" : None,
                "alt_rsn" : None,
                "on_leave" : False,
                "inactive" : False,
                "skill_comp" : {
                    "points": 0,
                    "wins": "",
                    "lifetime_pts": 0 },
                "notes" : user_notes} 
            self.bot.user_data.insert_one(post)
            await ctx.channel.send(f'New member {user_rsn} accepted!')
            self.bot.updateUsersCounter(user_id)
            await ctx.channel.send(f'User Counter is now {user_id}.')
        else:
            await ctx.channel.send(f'{user_rsn} already exists. Please use update command. Run `!help update-user` for more details.')

    @commands.command(name='add-existing-member', help="""Add an existing member. 
    Date format must be YYYY-MM-dd
    Membership level is 0-6 where 0 is smiley, 6 is leader""")
    # @commands.has_role('Leader')
    async def add_existing_member(self, ctx, user_rsn, join_date, membership_level=None, user_discord_id=None, user_time_zone=None, user_notes=None):
        myquery = { "rsn": user_rsn }
        if (self.bot.user_data.count_documents(myquery) == 0):
            user_id = self.bot.getNextUserId()
            if membership_level is None:
                membership_level = "0"

            # Create datetime object from specified date
            joined = datetime.datetime.strptime(join_date, self.bot.__datetime_fmt__)
            
            post = {
                "_id": user_id,
                "rsn": user_rsn,
                "discord_id": user_discord_id,
                "membership_level": membership_level,
                "l0" : f'{joined}',
                "l1" : f'{joined + datetime.timedelta(14)}', # 2 weeks
                "l2" : f'{joined + datetime.timedelta(84)}', # 12 weeks
                "l3" : f'{joined + datetime.timedelta(182)}', # 26 weeks
                "l4" : f'{joined + datetime.timedelta(365)}', # 52 weeks
                "l5" : f'{joined + datetime.timedelta(365)}', # 52 weeks
                "special_status" : None,
                "former_rsn" : None,
                "alt_rsn" : None,
                "on_leave" : False,
                "inactive" : False,
                "skill_comp" : {
                    "points": 0,
                    "wins": "",
                    "lifetime_pts": 0 },
                "notes" : user_notes} 
            self.bot.user_data.insert_one(post)
            await ctx.channel.send(f'Added member {user_rsn}!')
            self.bot.updateUsersCounter(user_id)
            await ctx.channel.send(f'User Counter is now {user_id}.')
        else:
            await ctx.channel.send(f'{user_rsn} already exists. Please use update command. Run `!help update-user` for more details.')

    @commands.command(name='view-member', help="View member info by rsn")
    # @commands.has_role('Leader')
    async def view_member(self, ctx, user_rsn):
        myquery = { "rsn": user_rsn }
        user = self.bot.user_data.find_one(myquery)
        if (user is None):
            await ctx.channel.send(f'No members found with rsn of {user_rsn}')
            return

        await ctx.channel.send(f"""**RSN:** {user['rsn']}
**Discord ID:** {user['discord_id']}
**Membership Level:** {self.bot.__mem_level_names__[int(user['membership_level'])]}
**Next Promotion Date:** {self.bot.getNextMemLvlDate(user)}
**Skill Comp Points:** {user['skill_comp']['points']}
**On Leave:** {user['on_leave']}
**Inactive:** {user['inactive']}
**Alts:** {user['alt_rsn']}
**Previous RSN:** {user['former_rsn']}
**Other Notes:** {user['notes']}""")
# TODO - make this better

    @commands.command(name='update-member', help="""Update an existing member""")
    # @commands.has_role('Leader')
    async def update_member(self, ctx, user_rsn, update_key, update_value):
        # Only allow updates on certain keys, this prevents new keys from being added
        print(f'updating user {user_rsn}. Key {update_key} will be set to value {update_value}.')
        if (update_key in self.bot.__updateable_keys__):
            if update_key == "join_date":
                update_key = "l0"
                # TODO - convert value to datetime
            self.bot.user_data.update_one({"rsn":user_rsn}, {"$set":{f'{update_key}':update_value}})
            await ctx.channel.send(f'Updated user {user_rsn}. Key {update_key} set to value {update_value}.')

    @commands.command(name='add-key-all-members', help="""Update all members with new database key""")
    # @commands.has_role('Leader')
    async def add_key_all_members(self, ctx, update_key, update_value):
        # Only allow updates on certain keys, this prevents new keys from being added
        print(f'Adding new key {update_key} to all users with initial value {update_value}.')
        self.bot.user_data.update_many({}, {"$set":{f'{update_key}':update_value}})
        await ctx.channel.send(f'Added key {update_key} for all users with value {update_value}.')

    @commands.command(name='set-active', help="""Mark a member as active or inactive.""")
    # @commands.has_role('Leader')
    async def set_active(self, ctx, user_rsn, is_active):
        if is_active.lower() in self.bot.__true_values__:
            inactive = False
        else:
            inactive = True
        await self.update_member(ctx, user_rsn, "inactive", inactive)
        await ctx.channel.send(f'{user_rsn} inactive flag set to {inactive}')

    @commands.command(name='set-onleave', help="""Mark a member as on leave or returned""")
    # @commands.has_role('Leader')
    async def set_onleave(self, ctx, user_rsn, is_onleave):
        if is_onleave.lower() in self.bot.__true_values__:
            onleave = True
        else:
            onleave = False
        await self.update_member(ctx, user_rsn, "on_leave", onleave)
        await ctx.channel.send(f'{user_rsn} on_leave flag set to {onleave}')

    # @commands.command(name="update-command-set", help="Reloads commands for the specified cog")
    # async def update_command_set(self, ctx, cog_name):
    #     await self.bot.reload_cog(cog_name)


def setup(bot):
    bot.add_cog(admin(bot))