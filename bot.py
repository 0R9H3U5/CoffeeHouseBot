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
# - command categories
#######

import os
import ssl
import discord
import datetime
from discord.ext import commands
from dotenv import load_dotenv

import pymongo
from pymongo import MongoClient

import urllib.parse

mem_level_names = ["Friend", "Recruit", "Corporal", "Sergeant", "Lieutenant", "General", "Leader"]
updateable_keys = ["rsn", "discord_id", "membership_level", "join_date", "special_status", "former_rsn", "alt_rsn", "on_leave", "inactive", "skill_pts", "notes"]
true_values = ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'ye']
datetime_fmt = "%Y-%m-%d"

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB_USER = os.getenv('DB_USER')
DB_USER_PW = os.getenv('DB_USER_PW')
bot = commands.Bot(command_prefix='!')

# Connect to db
mongo_url = "mongodb+srv://" + DB_USER + ":" + urllib.parse.quote_plus(DB_USER_PW) + "@coffee-house-member-dat.p3irz.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
cluster = MongoClient(mongo_url, ssl_cert_reqs=ssl.CERT_NONE)
db = cluster["user_data"]
user_data = db["user_data"]
counters = db["counters"]

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
@bot.command(name='add-member', help="Add a new member")
# @commands.has_role('Leader')
async def add_member(ctx, user_rsn, user_discord_id=None, user_time_zone=None, user_notes=None):
    myquery = { "rsn": user_rsn }
    if (user_data.count_documents(myquery) == 0):
        user_id = getNextUserId()        
        today = datetime.date.today()
        post = {
            "_id": user_id,
            "rsn": user_rsn,
            "discord_id": user_discord_id,
            "membership_level": "0", 
            "l0" : f'{today}',
            "l1" : f'{today + datetime.timedelta(14)}', # 2 weeks
            "l2" : f'{today + datetime.timedelta(84)}', # 12 weeks
            "l3" : f'{today + datetime.timedelta(182)}', # 26 weeks
            "l4" : f'{today + datetime.timedelta(365)}', # 52 weeks
            "l5" : f'{today + datetime.timedelta(365)}', # 52 weeks
            "special_status" : None,
            "former_rsn" : None,
            "alt_rsn" : None,
            "on_leave" : False,
            "inactive" : False,
            "skill_pts" : 0,
            "notes" : user_notes} 
        user_data.insert_one(post)
        await ctx.channel.send(f'New member {user_rsn} accepted!')
        updateUsersCounter(user_id)
        await ctx.channel.send(f'User Counter is now {user_id}.')
    else:
        await ctx.channel.send(f'{user_rsn} already exists. Please use update command. Run `!help update-user` for more details.')

@bot.command(name='add-existing-member', help="""Add an existing member. 
Date format must be YYYY-MM-dd
Membership level is 0-6 where 0 is smiley, 6 is leader""")
# @commands.has_role('Leader')
async def add_existing_member(ctx, user_rsn, join_date, membership_level=None, user_discord_id=None, user_time_zone=None, user_notes=None):
    myquery = { "rsn": user_rsn }
    if (user_data.count_documents(myquery) == 0):
        user_id = getNextUserId()
        if membership_level is None:
            membership_level = "0"

        # Create datetime object from specified date
        joined = datetime.datetime.strptime(join_date, datetime_fmt)
        
        post = {
            "_id": user_id,
            "rsn": user_rsn,
            "discord_id": user_discord_id,
            "membership_level": membership_level,
            "l0" : f'{joined}',
            "l1" : f'{joined + datetime.timedelta(14)}', # 2 weeks
            "l2" : f'{joined + datetime.timedelta(84)}', # 12 weeks
            "l3" : f'{joined + datetime.timedelta(182)}', # 26 weeks
            "l4" : f'{joined + datetime.timedelta(365)}', # 52 weeks
            "l5" : f'{joined + datetime.timedelta(365)}', # 52 weeks
            "special_status" : None,
            "former_rsn" : None,
            "alt_rsn" : None,
            "on_leave" : False,
            "inactive" : False,
            "skill_pts" : 0,
            "notes" : user_notes} 
        user_data.insert_one(post)
        await ctx.channel.send(f'Added member {user_rsn}!')
        updateUsersCounter(user_id)
        await ctx.channel.send(f'User Counter is now {user_id}.')
    else:
        await ctx.channel.send(f'{user_rsn} already exists. Please use update command. Run `!help update-user` for more details.')

@bot.command(name='view-member', help="View member info by rsn")
# @commands.has_role('Leader')
async def view_member(ctx, user_rsn):
    myquery = { "rsn": user_rsn }
    user = user_data.find_one(myquery)
    if (user is None):
        await ctx.channel.send(f'No members found with rsn of {user_rsn}')
        return

    await ctx.channel.send(f"""**RSN:** {user['rsn']}
**Discord ID:** {user['discord_id']}
**Membership Level:** {mem_level_names[int(user['membership_level'])]}
**Next Promotion Date:** {getNextMemLvlDate(user)}
**Skill Comp Points:** {user['skill_pts']}
**On Leave:** {user['on_leave']}
**Inactive:** {user['inactive']}
**Alts:** {user['alt_rsn']}
**Previous RSN:** {user['former_rsn']}
**Other Notes:** {user['notes']}""")
# TODO - make this better

@bot.command(name='update-member', help="""Update an existing member""")
# @commands.has_role('Leader')
async def update_member(ctx, user_rsn, update_key, update_value):
    # Only allow updates on certain keys, this prevents new keys from being added
    print(f'updating user {user_rsn}. Key {update_key} will be set to value {update_value}.')
    if (update_key in updateable_keys):
        if update_key == "join_date":
            update_key = "l0"
            # TODO - convert valte to datetime
        user_data.update({"rsn":user_rsn}, {"$set":{f'{update_key}':update_value}})
        await ctx.channel.send(f'Updated user {user_rsn}. Key {update_key} set to value {update_value}.')

@bot.command(name='set-active', help="""Mark a member as active or inactive.""")
# @commands.has_role('Leader')
async def set_active(ctx, user_rsn, is_active):
    if is_active.lower() in true_values:
        inactive = False
    else:
        inactive = True
    await update_member(ctx, user_rsn, "inactive", inactive)
    await ctx.channel.send(f'{user_rsn} inactive flag set to {inactive}')

@bot.command(name='set-onleave', help="""Mark a member as on leave or returned""")
# @commands.has_role('Leader')
async def set_active(ctx, user_rsn, is_onleave):
    if is_onleave.lower() in true_values:
        onleave = True
    else:
        onleave = False
    await update_member(ctx, user_rsn, "on_leave", onleave)
    await ctx.channel.send(f'{user_rsn} on_leave flag set to {onleave}')

@bot.command(name='list-members', help="""Print out a list of all members""")
# @commands.has_role('Leader')
async def list_members(ctx):
    all_members = user_data.find({}) # TODO - keep an eye on how expensive this is

    lbl_id = "ID".center(6)
    lbl_rsn = "RSN".center(23)
    userlist = f"{lbl_id}|{lbl_rsn}|     Discord ID\r\n"
    for mem in all_members:
        memid = f"{mem['_id']}".center(6)
        rsn = f"{mem['rsn']}".center(23)
        userlist = userlist + f"{memid} {rsn}    {mem['discord_id']}\r\n"
    await ctx.channel.send(f'{userlist}')

@bot.command(name='list-inactive', help="""Print out a list of all inactive members""")
# @commands.has_role('Leader')
async def list_inactive(ctx):
    inactive_members = queryMembers("inactive", True)
    await ctx.channel.send(f'{inactive_members}')

@bot.command(name='list-onleave', help="""Print out a list of all members marked on leave""")
# @commands.has_role('Leader')
async def list_onleave(ctx):
    on_leave_members = queryMembers("on_leave", True)
    await ctx.channel.send(f'{on_leave_members}')

@bot.command(name='promotion-when', help="Returns next promotion date of requesting member")
async def promotion_when(ctx):
    uid = f'{ctx.author.name}#{ctx.author.discriminator}'
    myquery = { "discord_id": uid }
    try:
        user = user_data.find_one(myquery)
        if (user is None):
            await ctx.channel.send(f"1 I didn't find you in the member database. If you wish to apply see #applications") # TODO - actually link channel
            return
    except:
        await ctx.channel.send(f"2 I didn't find you in the member database. If you wish to apply see #applications") # TODO - actually link channel
        return

    next_mem_lvl_date = getNextMemLvlDate(user)
    next_mem_lvl = getNextMemLvl(user['membership_level'])
    if next_mem_lvl is None:
        await ctx.channel.send(f"{ctx.author.name}, you are are already eligible for all ranks.")
    else:
        await ctx.channel.send(f"{ctx.author.name}, you are eligible for promotion to {next_mem_lvl} on {next_mem_lvl_date[:10]}.")


# Use the current membership level to find when the next promotion is due
def getNextMemLvlDate(user):
    current_lvl = user['membership_level']
    next_lvl = int(current_lvl) + 1
    if (next_lvl < 4):
        return user[f'l{next_lvl}']
    else:
        return 'Eligible for any membership level'

# Get the name of the next membership level
def getNextMemLvl(current):
    if (int(current) < 4):
        return mem_level_names[int(current) + 1]
    else:
        return None

# fetch the user counter and pass it back incremented by one
def getNextUserId():
    # Get the user count and add 1 for unique id
    counts = counters.find_one()
    return int(counts['users']) + 1

def queryMembers(key, value):
    users = user_data.find({ key : value })
    userlist = " ID |          RSN          |     Discord ID\r\n"
    for mem in users:
        userlist = userlist + f"{mem['_id']}   {mem['rsn']}   {mem['discord_id']}\r\n"
    return userlist


# update the user counter to the specified value
def updateUsersCounter(new_value):
    counters.update({}, {"$set":{"users":f'{new_value}'}})

bot.run(TOKEN)