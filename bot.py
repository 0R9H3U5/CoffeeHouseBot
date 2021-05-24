#######
# TODO LIST:
# - Automate disc rank ups
#   - On command
#   - Check daily
# - Remove member
# - ALL - Check SKill Pts(user)
# - ALL - Check SKill Pts top 10
# - Set Skill Pts
# - left discord notification
# - Command categories
# - Help Docs
# - WoM Integration
# - Refactor into better structure
# - Google Sheets integration/better way to get whole mem list
#######

import os
import ssl
import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv

import pymongo
from pymongo import MongoClient

import urllib.parse

__version__ = '0.1.0'

log = logging.getLogger('discord')
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

class CoffeeHouseBot(commands.Bot):
    __prefix__ = '!'
    __datetime_fmt__ = "%Y-%m-%d"
    __mem_level_names__ = ["Friend", "Recruit", "Corporal", "Sergeant", "Lieutenant", "General", "Leader"]
    __updateable_keys__ = ["rsn", "discord_id", "membership_level", "join_date", "special_status", "former_rsn", "alt_rsn", "on_leave", "inactive", "skill_pts", "notes"]
    __true_values__ = ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'ye']
    __cogs__ = ['cogs.admin', 'cogs.general', 'cogs.user-lookup']

    def __init__(self, db_user, db_pw):
        self.command_prefix='!'

        # Connect to db
        mongo_url = "mongodb+srv://" + db_user + ":" + urllib.parse.quote_plus(db_pw) + "@coffee-house-member-dat.p3irz.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
        cluster = MongoClient(mongo_url, ssl_cert_reqs=ssl.CERT_NONE)
        db = cluster["user_data"]
        self.user_data = db["user_data"]
        self.counters = db["counters"]
        self.skill_comp = db["skill_comp"]
        super().__init__(command_prefix=CoffeeHouseBot.__prefix__)

    async def on_ready(self):
        print(f'{bot.user} has connected to Discord!')
        log.info('Logged in as')
        log.info(f'Bot-Name: {self.user.name} | ID: {self.user.id}')
        # log.info(f'Dev Mode: {self.dev} | Docker: {self.docker}')
        log.info(f'Discord Version: {discord.__version__}')
        log.info(f'Bot Version: {__version__}')
        for cog in CoffeeHouseBot.__cogs__:
            try:
                print(f'Loading cog {cog}')
                self.load_extension(cog)
            except Exception:
                log.warning(f'Couldn\'t load cog {cog}')
      
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
            return CoffeeHouseBot.__mem_level_names__[int(current) + 1]
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


    # update the user counter to the specified value
    def updateUsersCounter(self, new_value):
        self.counters.update({}, {"$set":{"users":f'{new_value}'}})

if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    DB_USER = os.getenv('DB_USER')
    DB_USER_PW = os.getenv('DB_USER_PW')

    bot = CoffeeHouseBot(DB_USER, DB_USER_PW)
    bot.run(TOKEN)