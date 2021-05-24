from discord.ext import commands

class general(commands.Cog):
    """
    Logic for all general command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="promotion-when", help="Returns next promotion date of requesting member")
    async def promotion_when(self, ctx):
        uid = f'{ctx.author.name}#{ctx.author.discriminator}'
        myquery = { "discord_id": uid }
        try:
            user = self.bot.user_data.find_one(myquery)
            if (user is None):
                await ctx.channel.send(f"I didn't find you in the member database. If you wish to apply see #applications") # TODO - actually link channel
                return
        except:
            await ctx.channel.send(f"I didn't find you in the member database. If you wish to apply see #applications") # TODO - actually link channel
            return

        next_mem_lvl_date = self.bot.getNextMemLvlDate(user)
        next_mem_lvl = self.bot.getNextMemLvl(user['membership_level'])
        if next_mem_lvl is None:
            await ctx.channel.send(f"{ctx.author.name}, you are are already eligible for all ranks.")
        else:
            await ctx.channel.send(f"{ctx.author.name}, you are eligible for promotion to {next_mem_lvl} on {next_mem_lvl_date[:10]}.")

def setup(bot):
    bot.add_cog(general(bot))