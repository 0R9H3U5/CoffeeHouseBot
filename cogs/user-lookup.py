from discord.ext import commands

class userLookup(commands.Cog):
    """
    Logic for all general command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='list-members', help="""Print out a list of all members""")
    # @commands.has_role('Leader')
    async def list_members(self, ctx):
        all_members = self.bot.user_data.find({}) # TODO - keep an eye on how expensive this is

        lbl_id = "ID".center(6)
        lbl_rsn = "RSN".center(23)
        userlist = f"{lbl_id}|{lbl_rsn}|     Discord ID\r\n"
        for mem in all_members:
            memid = f"{mem['_id']}".center(6)
            rsn = f"{mem['rsn']}".center(23)
            userlist = userlist + f"{memid} {rsn}    {mem['discord_id']}\r\n"
        await ctx.channel.send(f'{userlist}')

    @commands.command(name='list-inactive', help="""Print out a list of all inactive members""")
    # @commands.has_role('Leader')
    async def list_inactive(self, ctx):
        inactive_members = self.bot.queryMembers("inactive", True)
        await ctx.channel.send(f'{inactive_members}')

    @commands.command(name='list-onleave', help="""Print out a list of all members marked on leave""")
    # @commands.has_role('Leader')
    async def list_onleave(self, ctx):
        on_leave_members = self.bot.queryMembers("on_leave", True)
        await ctx.channel.send(f'{on_leave_members}')

def setup(bot):
    bot.add_cog(userLookup(bot))