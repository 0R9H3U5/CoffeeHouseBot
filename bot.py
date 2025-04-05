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
# - SOTW/BOTW Poll
# - blocklist for ppl abusing bot
# - notify of comp lead change
# - database connection restart on failure
#######
import json
import os
import pprint
import ssl
import datetime
import discord
import logging
import urllib.parse 
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import psycopg2

__version__ = '0.1.0'

log = logging.getLogger('discord')
logging.basicConfig(level=os.getenv('LOGLEVEL', 'INFO'))
log = logging.getLogger('discord')
log.propagate = False  # Prevent propagation to root logger to avoid duplicate logs

class CoffeeHouseBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        # read in configs
        with open("config.json") as json_data_file:
            self.configs = json.load(json_data_file)

        # Connect to db
        self.getDatabaseConnection()

        super().__init__(command_prefix=self.configs["command_prefix"], intents=intents)

    async def setup_hook(self):
        """This is called when the bot starts up"""
        # Load all cogs
        for cog in self.configs["cogs"]:
            try:
                print(f'Loading cog {cog}')
                await self.load_extension(cog)
            except Exception as e:
                log.warning(f'Couldn\'t load cog {cog}: {str(e)}')
        
        # Sync commands globally
        try:
            print('Syncing commands globally...')
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} commands globally!')
        except Exception as error:
            log.error(f'Failed to sync commands: {error}')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        log.info('Logged in as')
        log.info(f'Bot-Name: {self.user.name} | ID: {self.user.id}')
        log.info(f'Discord Version: {discord.__version__}')
        log.info(f'Bot Version: {__version__}')
        
        # Sync to test server if specified
        if "test_server_guild_id" in self.configs:
            try:
                print(f'Syncing commands to test server...')
                guild_id = self.configs["test_server_guild_id"]
                print(f'Looking for guild with ID: {guild_id}')
                
                # List all guilds the bot is in for debugging
                print(f'Bot is in {len(self.guilds)} guilds:')
                for g in self.guilds:
                    print(f'  - {g.name} (ID: {g.id})')
                
                guild = self.get_guild(guild_id)
                if guild is None:
                    log.error(f'Could not find guild with ID {guild_id}')
                    print(f'ERROR: Guild with ID {guild_id} not found. Make sure the bot is in this server.')
                    return
                
                print(f'Found guild: {guild.name}')
                synced = await self.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to test server!')
                
                # List the synced commands
                print('Synced commands:')
                for cmd in synced:
                    print(f'  - {cmd.name}')
            except Exception as error:
                log.error(f'Failed to sync commands to test server: {error}')
                print(f'ERROR: {error}')

    async def on_command(self, ctx):
        log.info(f'recieved command: {ctx.message}')
        msg = ctx.message

    async def on_message(self, message):
        # if message.author.bot or message.author.id in loadconfig.__blacklist__:
        #     return
        log.info(f'recieved message: {message}')
        await self.process_commands(message)    

    # Use the current membership level to find when the next promotion is due
    def getNextMemLvlDate(self, mem_lvl, join_date):
        next_lvl = int(mem_lvl) + 1
        if (next_lvl < 5):
            today = datetime.date.today()
            
            # Ensure join_date is a datetime.date object
            if isinstance(join_date, str):
                try:
                    # Try to parse the date string
                    join_date = datetime.datetime.strptime(join_date, "%Y-%m-%d").date()
                except ValueError:
                    # If parsing fails, return None
                    return None
            elif isinstance(join_date, datetime.datetime):
                # Convert datetime to date if needed
                join_date = join_date.date()
            elif not isinstance(join_date, datetime.date):
                # If it's not a date, datetime, or string, return None
                return None
                
            days_as_member = today - join_date
            days_as_member_int = days_as_member.days  # Convert timedelta to integer
            print(f'days_as_member_int: {days_as_member_int}')
            if days_as_member_int < 14: # 2 weeks
                return join_date + datetime.timedelta(days=14)
            elif days_as_member_int < 84: # 12 weeks
                return join_date + datetime.timedelta(days=84)
            elif days_as_member_int < 182: # 26 weeks
                return join_date + datetime.timedelta(days=182)
            elif days_as_member_int < 365: # 52 weeks
                return join_date + datetime.timedelta(days=365)
            else:
                return None
        else:
            return None

    # Use the current membership level to find when the next promotion is due
    def getExpectedMemLvlByJoinDate(self, join_date):
        today = datetime.date.today()
        days_as_member = today - join_date
        if days_as_member < datetime.timedelta(days = 14): # Under 2 weeks
            return 0
        elif days_as_member > datetime.timedelta(days = 14) and days_as_member < datetime.timedelta(days = 84): # Between 2 weeks and 12 weeks
            return 1
        elif days_as_member > datetime.timedelta(days = 84) and days_as_member < datetime.timedelta(days = 182): #  Between 12 weeks and 26 weeks
            return 2
        # elif days_as_member > datetime.timedelta(days = 182) and days_as_member < datetime.timedelta(days = 365): # Between 26 weeks and 52 weeks
        #     return 3
        else:
            return 3

    # Get the name of the next membership level
    def getNextMemLvl(self, current):
        if (int(current) < 4):
            return self.configs["mem_level_names"][int(current) + 1]
        else:
            return None

    def queryMembers(self, key, value):
        users = self.cursor.execute("SELECT _id, rsn, discord_if from member")
        userlist = " ID |          RSN          |     Discord ID\r\n"
        for mem in users:
            userlist = userlist + f"{mem['_id']}   {mem['rsn']}   {mem['discord_id']}\r\n"
        return userlist

    def getConfigValue(self, key):
        return self.configs[key]

    def getDatabaseConnection(self):
        db_name = self.getConfigValue("db_name")
        db_user = self.getConfigValue("db_user")
        db_pw = self.getConfigValue("db_pw")
        db_host = self.getConfigValue("db_host")
        # self.conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pw, host=db_host, port='5432', sslmode='require')
        self.conn = psycopg2.connect(f'postgres://{db_user}:{db_pw}@{db_host}:25640/{db_name}?sslmode=require')
        print(f'Successful connection to database - {self.conn.get_dsn_parameters()}')

    def check_database_connection(self):
        """Check if the database connection is active and reconnect if needed."""
        try:
            # Try to execute a simple query to check connection
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # Connection is not active, attempt to reconnect
            try:
                print("Database connection lost. Attempting to reconnect...")
                self.getDatabaseConnection()
                return True
            except Exception as e:
                print(f"Failed to reconnect to database: {e}")
                return False
        except Exception as e:
            print(f"Error checking database connection: {e}")
            return False

    def selectMany(self, query):
        if not self.check_database_connection():
            print("Cannot execute query: No database connection")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL", error)
            return None
        finally:
            cursor.close()
    
    def selectOne(self, query):
        if not self.check_database_connection():
            print("Cannot execute query: No database connection")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchone()
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching data from PostgreSQL", error)
            return None
        finally:
            cursor.close()
            
    def execute_query(self, query):
        if not self.check_database_connection():
            print("Cannot execute query: No database connection")
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            return True
        except (Exception, psycopg2.Error) as error:
            print("Error while running query", error)
            return False
        finally:
            cursor.close()

if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot = CoffeeHouseBot()
    bot.run(TOKEN)