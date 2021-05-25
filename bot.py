#pylint: disable=E1101

#######
# TODO LIST:
# - Automate disc rank ups
#   - On command
#   - Check daily
# - Remove member
# - ALL - Check SKill Pts top 10
# - Set Skill Pts
# - left discord notification
# - Help Docs
# - WoM Integration
# - Google Sheets integration/better way to get whole mem list
# - SOTW/BOTW Poll
# - lottery entry tracking and picker
# - blocklist for ppl abusing bot
#######
import json
import os
import ssl
import discord
import logging
import urllib.parse
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient

__version__ = '0.1.0'

log = logging.getLogger('discord')
logging.basicConfig(level=os.getenv('LOGLEVEL', 'INFO'))

class CoffeeHouseBot(commands.AutoShardedBot):
    def __init__(self, db_user, db_pw):
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        
        # read in configs
        with open("config.json") as json_data_file:
            self.configs = json.load(json_data_file)

        # Connect to db
        mongo_url = "mongodb+srv://" + db_user + ":" + urllib.parse.quote_plus(db_pw) + "@coffee-house-member-dat.p3irz.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
        cluster = MongoClient(mongo_url, ssl_cert_reqs=ssl.CERT_NONE)
        db = cluster["user_data"]
        self.user_data = db["user_data"]
        self.counters = db["counters"]
        self.skill_comp = db["skill_comp"]

        super().__init__(command_prefix=self.configs["command_prefix"], intents=intents)

    async def on_ready(self):
        print(f'{bot.user} has connected to Discord!')
        log.info('Logged in as')
        log.info(f'Bot-Name: {self.user.name} | ID: {self.user.id}')
        # log.info(f'Dev Mode: {self.dev} | Docker: {self.docker}')
        log.info(f'Discord Version: {discord.__version__}')
        log.info(f'Bot Version: {__version__}')
        for cog in self.configs["cogs"]:
            try:
                print(f'Loading cog {cog}')
                self.load_extension(cog)
            except Exception:
                log.warning(f'Couldn\'t load cog {cog}')        
        self.get_cog('admin').update_disc_roles.start()
      
    async def on_message(self, message):
        # if message.author.bot or message.author.id in loadconfig.__blacklist__:
        #     return
        if isinstance(message.channel, discord.DMChannel):
            await message.author.send(':x: Sorry, but I don\'t accept commands through direct messages! Please use the `#bots` channel of your corresponding server!')
            return
        await self.process_commands(message)    


    # Use the current membership level to find when the next promotion is due
    def getNextMemLvlDate(self, user):
        current_lvl = user['membership_level']
        next_lvl = int(current_lvl) + 1
        if (next_lvl < 4):
            return user[f'l{next_lvl}']
        else:
            return 'Eligible for any membership level'

    # Get the name of the next membership level
    def getNextMemLvl(self, current):
        if (int(current) < 4):
            return self.configs["mem_level_names"][int(current) + 1]
        else:
            return None

    # fetch the user counter and pass it back incremented by one
    def getNextUserId(self):
        # Get the user count and add 1 for unique id
        counts = self.counters.find_one()
        return int(counts['users']) + 1

    def queryMembers(self, key, value):
        users = self.user_data.find({ key : value })
        userlist = " ID |          RSN          |     Discord ID\r\n"
        for mem in users:
            userlist = userlist + f"{mem['_id']}   {mem['rsn']}   {mem['discord_id']}\r\n"
        return userlist

    async def getUserFromAuthor(self, ctx):
        uid = f'{ctx.author.name}#{ctx.author.discriminator}'
        myquery = { "discord_id": uid }
        log.info(f'finding for user with query {myquery}')
        try:
            user = self.user_data.find_one(myquery)
            if (user is None):
                await ctx.channel.send(f"1 I didn't find you in the member database. If you wish to apply see `#applications`") # TODO - actually link channel
                return None
            return user
        except:
            await ctx.channel.send(f"1 I didn't find you in the member database. If you wish to apply see `#applications`") # TODO - actually link channel
            return None

    # update the user counter to the specified value
    def updateUsersCounter(self, new_value):
        self.counters.update({}, {"$set":{"users":f'{new_value}'}})

    def getConfigValue(self, key):
        return self.configs[key]

if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    DB_USER = os.getenv('DB_USER')
    DB_USER_PW = os.getenv('DB_USER_PW')

    bot = CoffeeHouseBot(DB_USER, DB_USER_PW)
    bot.run(TOKEN)