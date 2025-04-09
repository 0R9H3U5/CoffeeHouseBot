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
                    # print(f'Permissions:')
                    # for permission in g.me.guild_permissions:
                    #     print(f'  - {permission}')
                
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
        
        # Process commands first
        await self.process_commands(message)
        
        # Skip forwarding to cogs if this is a command
        if message.content.startswith(self.command_prefix):
            return
            
        # Forward non-command messages to cogs for event handling
        for cog in self.cogs.values():
            if hasattr(cog, 'on_message'):
                try:
                    await cog.on_message(message)
                except Exception as e:
                    log.error(f"Error in {cog.__class__.__name__}.on_message: {e}")

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
        """
        Establish a connection to the PostgreSQL database.
        If a connection already exists, it will be closed before creating a new one.
        If there's an aborted transaction, it will be rolled back.
        """
        # Close existing connection if it exists
        if hasattr(self, 'conn') and self.conn is not None:
            try:
                # Check if there's an aborted transaction
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            except psycopg2.OperationalError as e:
                if "current transaction is aborted" in str(e):
                    # Roll back the aborted transaction
                    try:
                        self.conn.rollback()
                        print("Rolled back aborted transaction")
                    except Exception as rollback_error:
                        print(f"Error rolling back transaction: {rollback_error}")
                # Close the connection
                try:
                    self.conn.close()
                    print("Closed existing connection with issues")
                except Exception as close_error:
                    print(f"Error closing connection: {close_error}")
            except Exception as e:
                # For any other error, try to close the connection
                try:
                    self.conn.close()
                    print("Closed existing connection due to error")
                except Exception as close_error:
                    print(f"Error closing connection: {close_error}")
        
        # Get database connection parameters
        db_name = self.getConfigValue("db_name")
        db_user = self.getConfigValue("db_user")
        db_pw = self.getConfigValue("db_pw")
        db_host = self.getConfigValue("db_host")
        db_port = self.getConfigValue("db_port")
        
        # Establish a new connection
        try:
            self.conn = psycopg2.connect(f'postgres://{db_user}:{db_pw}@{db_host}:{db_port}/{db_name}?sslmode=require')
            print(f'Successful connection to database - {self.conn.get_dsn_parameters()}')
            return True
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            self.conn = None
            return False

    def check_database_connection(self):
        """Check if the database connection is active and reconnect if needed."""
        try:
            # Try to execute a simple query to check connection
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # Connection is not active, attempt to reconnect
            print(f"Database connection issue detected: {e}")
            return self.getDatabaseConnection()
        except Exception as e:
            print(f"Error checking database connection: {e}")
            # Try to reconnect as a fallback
            return self.getDatabaseConnection()

    def selectMany(self, query):
        if not self.check_database_connection():
            print("Cannot execute query: No database connection")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except (Exception, psycopg2.Error) as error:
            print(f"Error while fetching data from PostgreSQL: {error}")
            # If there's a transaction issue, try to reconnect
            if "current transaction is aborted" in str(error):
                print("Transaction aborted, attempting to reconnect...")
                self.getDatabaseConnection()
            return None
    
    def selectOne(self, query):
        if not self.check_database_connection():
            print("Cannot execute query: No database connection")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except (Exception, psycopg2.Error) as error:
            print(f"Error while fetching data from PostgreSQL: {error}")
            # If there's a transaction issue, try to reconnect
            if "current transaction is aborted" in str(error):
                print("Transaction aborted, attempting to reconnect...")
                self.getDatabaseConnection()
            return None
            
    def execute_query(self, query):
        if not self.check_database_connection():
            print("Cannot execute query: No database connection")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            return True
        except (Exception, psycopg2.Error) as error:
            print(f"Error while executing query in PostgreSQL: {error}")
            # If there's a transaction issue, try to reconnect
            if "current transaction is aborted" in str(error):
                print("Transaction aborted, attempting to reconnect...")
                self.getDatabaseConnection()
            return None

    def format_money(self, amount, unit="gp"):
        """
        Format a monetary amount in a human-readable format.
        
        Args:
            amount (int): The amount to format
            unit (str, optional): The unit to append. Defaults to "gp".
            
        Returns:
            str: A formatted string with the amount and unit
            
        Examples:
            - 100 gp remains 100 gp
            - 1000 gp becomes 1K gp
            - 10009 gp becomes 10K gp
            - 999500 gp becomes 999.5K gp
            - 2000000 gp becomes 2M gp
            - 2000400 gp becomes 2M gp
            - 755200080 gp becomes 755.2M gp
            - 4000000000 gp becomes 4T gp
        """
        if amount < 1000:
            return f"{amount} {unit}"
        
        # Determine the appropriate unit and divisor
        if amount < 1000000:
            divisor = 1000
            suffix = "K"
            # Convert non-essential digits to zeros
            # For thousands, we want to keep 4 significant digits
            # For example, 999999 becomes 999900
            total_digits = len(str(amount))
            significant_digits = total_digits - 2
            # Calculate the power of 10 to divide by to get the right number of significant digits
            power = total_digits - significant_digits
            if power > 0:
                # Round down to the nearest power of 10
                rounded_amount = (amount // (10 ** power)) * (10 ** power)
            else:
                rounded_amount = amount
        elif amount < 1000000000:
            divisor = 1000000
            suffix = "M"
            
            total_digits = len(str(amount))
            significant_digits = total_digits - 5
            power = total_digits - significant_digits
            if power > 0:
                rounded_amount = (amount // (10 ** power)) * (10 ** power)
            else:
                rounded_amount = amount
        else:
            divisor = 1000000000
            suffix = "T"
            
            total_digits = len(str(amount))
            significant_digits = total_digits - 8
            power = total_digits - significant_digits
            if power > 0:
                rounded_amount = (amount // (10 ** power)) * (10 ** power)
            else:
                rounded_amount = amount
        
        # Calculate the value in the appropriate unit
        value = rounded_amount / divisor
        
        # Format the value with one decimal place
        formatted = f"{value:.1f}"
        
        # Remove trailing .0 if it's a whole number
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        
        return f"{formatted}{suffix} {unit}"

if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot = CoffeeHouseBot()
    bot.run(TOKEN)