from discord.ext import commands

class skillComp(commands.Cog):
    """
    Logic for all general command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='skill-comp-points', help="""Fetch the skill comp points for the user""")
    async def skill_comp_points(self, ctx):
        user = await self.bot.getUserFromAuthor(ctx)
        if user is not None:
            await  ctx.channel.send(f"**{ctx.author.name}** you currently have **{user['skill_comp']['points']}** points from skill week competitions.")

    @commands.command(name='skill-comp-wins', help="""Fetch the skill comp wins for the user""")
    async def skill_comp_wins(self, ctx):
        user = await self.bot.getUserFromAuthor(ctx)
        if user is not None:
            winsstring = user['skill_comp']['wins']
            wins = winsstring.split(',')
            wincount = len(wins)
            await ctx.channel.send(f"**{ctx.author.name}** you have won **{wincount}** skill week competitions:")
            for win in wins:
                unquoted_win = win.replace('"','')
                await ctx.channel.send(f" - {unquoted_win.strip()}")


def setup(bot):
    bot.add_cog(skillComp(bot))