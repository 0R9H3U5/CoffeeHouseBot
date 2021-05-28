from discord.ext import commands

class general(commands.Cog):
    """
    Logic for all general command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="promotion-when", help="Returns next promotion date of requesting member")
    async def promotion_when(self, ctx):
        user = self.bot.selectOne(f"SELECT discord_id, membership_level, join_date FROM member WHERE discord_id_num={ctx.author.id}")

        next_mem_lvl_date = self.bot.getNextMemLvlDate(user[1], user[2])
        if next_mem_lvl_date is None:
            await ctx.channel.send(f"**{ctx.author.name}** you are are already eligible for all ranks.")
        else:
            next_mem_lvl = self.bot.getNextMemLvl(user[1])
            await ctx.channel.send(f"**{ctx.author.name}** you are eligible for promotion to **{next_mem_lvl}** on **{next_mem_lvl_date[:10]}**.")

def setup(bot):
    bot.add_cog(general(bot))