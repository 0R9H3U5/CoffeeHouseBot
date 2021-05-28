from discord.ext import commands

class userLookup(commands.Cog):
    """
    Logic for all user lookup command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='list-members', help="""Print out a list of all members""")
    # @commands.has_role('Leader')
    async def list_members(self, ctx):
        all_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member")        
        await ctx.channel.send(f'{self.format_user_list(all_members)}')

    @commands.command(name='list-inactive', help="""Print out a list of all inactive members""")
    # @commands.has_role('Leader')
    async def list_inactive(self, ctx):
        inactive_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member WHERE active=false")
        await ctx.channel.send(f'{self.format_user_list(inactive_members)}')

    @commands.command(name='list-onleave', help="""Print out a list of all members marked on leave""")
    # @commands.has_role('Leader')
    async def list_onleave(self, ctx):
        on_leave_members = self.bot.selectMany("SELECT _id, rsn, discord_id FROM member WHERE on_leave=true")
        await ctx.channel.send(f'{self.format_user_list(on_leave_members)}')

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

def setup(bot):
    bot.add_cog(userLookup(bot))