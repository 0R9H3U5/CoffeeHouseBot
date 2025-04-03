from discord.ext import commands

class skillComp(commands.Cog):
    """
    Logic for all skill competition command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='skill-comp-points', help="""Fetch the skill comp points for the user""")
    async def skill_comp_points(self, ctx):
        print("test")
        user = self.bot.selectOne(f"SELECT discord_id, skill_comp_pts FROM member WHERE discord_id_num={ctx.author.id}")
        if user is not None:
            await ctx.channel.send(f"**{ctx.author.name}** you currently have **{user[1]}** points from skill week competitions.")

    # TODO
    # @commands.command(name='skill-comp-wins', help="""Fetch the skill comp wins for the user""")
    # async def skill_comp_wins(self, ctx):
    #     user = await self.bot.getUserFromAuthor(ctx)
    #     if user is not None:
    #         winsstring = user['skill_comp']['wins']
    #         wins = winsstring.split(',')
    #         wincount = len(wins)
    #         await ctx.channel.send(f"**{ctx.author.name}** you have won **{wincount}** skill week competitions:")
    #         for win in wins:
    #             unquoted_win = win.replace('"','')
    #             await ctx.channel.send(f" - {unquoted_win.strip()}")

async def setup(bot):
    await bot.add_cog(skillComp(bot))