import discord
from discord.ext import commands
from discord import app_commands
import datetime
import gspread
import psycopg2
import traceback
import sys
import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import asyncio

class Dev(commands.Cog):
    """
    Logic for development and debugging commands
    """
    def __init__(self, bot):
        self.bot = bot
        # Define the scopes for Google Sheets API
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        # Path to token file
        self.TOKEN_PATH = 'token.json'
        # Path to credentials file
        self.CREDENTIALS_PATH = 'credentials.json'

    @app_commands.command(name="db_status", description="Check the database connection status (dev only)")
    async def db_status(self, interaction: discord.Interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Check database connection
            is_connected = self.bot.check_database_connection()
            
            if is_connected:
                # Get database info
                db_info = self.bot.selectOne("SELECT version()")
                db_version = db_info[0] if db_info else "Unknown"
                
                # Create embed for response
                embed = discord.Embed(
                    title="✅ Database Connection Status",
                    description="The database connection is active and working properly.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Database Version", value=db_version, inline=False)
                embed.add_field(name="Connection String", value=f"postgres://{self.bot.getConfigValue('db_user')}:***@{self.bot.getConfigValue('db_host')}:25640/{self.bot.getConfigValue('db_name')}?sslmode=require", inline=False)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Database connection is not active. Check the logs for more information.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error checking database status: {str(e)}", ephemeral=True)

    @app_commands.command(name="ping", description="Check the bot's latency (dev only)")
    async def ping(self, interaction: discord.Interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Calculate latency
        latency = round(self.bot.latency * 1000)
        
        # Create embed for response
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="get_bot_info", description="Display information about the bot (dev only)")
    async def get_bot_info(self, interaction: discord.Interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Get bot information
        uptime = datetime.datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else "Unknown"
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds)
        
        # Create embed for response
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="Bot Version", value=self.bot.__version__, inline=True)
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="Guilds", value=guild_count, inline=True)
        embed.add_field(name="Users", value=user_count, inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="reload_cog", description="Reload a specific cog (dev only)")
    @app_commands.describe(
        cog_name="The name of the cog to reload (e.g., 'lotto', 'admin')"
    )
    async def reload_cog(self, interaction: discord.Interaction, cog_name: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Format cog name if needed
            if not cog_name.startswith('cogs.'):
                cog_name = f'cogs.{cog_name}'
                
            # Reload the cog
            self.bot.reload_extension(cog_name)
            
            await interaction.followup.send(f"✅ Successfully reloaded cog: **{cog_name}**")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to reload cog **{cog_name}**: {str(e)}", ephemeral=True)

    @app_commands.command(name="error_test", description="Test error handling (dev only)")
    async def error_test(self, interaction: discord.Interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Intentionally raise an error
            raise ValueError("This is a test error")
        except Exception as e:
            # Get the full traceback
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            
            # Create embed for response
            embed = discord.Embed(
                title="🔍 Error Test Results",
                description="This is a test of the error handling system.",
                color=discord.Color.red()
            )
            embed.add_field(name="Error Type", value=type(e).__name__, inline=True)
            embed.add_field(name="Error Message", value=str(e), inline=True)
            embed.add_field(name="Traceback", value=f"```py\n{error_traceback[:1000]}...```", inline=False)
            
            await interaction.followup.send(embed=embed)

    def format_sql_array(self, input_string):
        """Format a comma-separated string as a PostgreSQL array.
        
        Args:
            input_string: A string that may contain comma-separated values
            
        Returns:
            A string representing a PostgreSQL array or 'NULL' if the input is empty
        """
        if not input_string:
            return "NULL"
            
        parts = [part.strip() for part in input_string.split(',') if part.strip()]
        if not parts:
            return "NULL"
        
        # Create the array string without using nested f-strings
        quoted_parts = []
        for part in parts:
            quoted_parts.append(f"'{part}'")
        
        return f"ARRAY[{', '.join(quoted_parts)}]"

    @app_commands.command(name="load_member_data", description="Load member data from a Google Sheet (dev only)")
    @app_commands.describe(
        sheet_id="The ID of the Google Sheet (from the URL)",
        sheet_name="The name of the sheet/tab to read from",
        range="The range to read (e.g., 'A1:D100')"
    )
    async def load_member_data(
        self, 
        interaction: discord.Interaction, 
        sheet_id: str, 
        sheet_name: str = "Member Data - Active", 
        range: str = "B5:P141"
    ):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        try:
            # Check if credentials file exists
            if not os.path.exists(self.CREDENTIALS_PATH):
                await interaction.followup.send(
                    "❌ Google Sheets credentials file not found. Please place 'credentials.json' in the bot's root directory.",
                    ephemeral=True
                )
                return
                
            # Get Google Sheets service
            service = self.get_google_sheets_service()
            if not service:
                await interaction.followup.send(
                    "❌ Failed to authenticate with Google Sheets API. Check the logs for details.",
                    ephemeral=True
                )
                return
                
            # Debug information
            debug_info = f"Attempting to access sheet ID: {sheet_id}\nSheet name: {sheet_name}\nRange: {range}"
            print(debug_info)
            
            try:
                # Read data from the sheet
                result = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"{sheet_name}!{range}"
                ).execute()
                
                values = result.get('values', [])
                
                if not values:
                    await interaction.followup.send(
                        "❌ No data found in the specified range.",
                        ephemeral=True
                    )
                    return
                    
                # Convert to pandas DataFrame for easier manipulation
                df = pd.DataFrame(values[1:], columns=values[0])
                
                # Create a summary of the data
                summary = f"✅ Successfully loaded data from Google Sheet:\n"
                summary += f"- Sheet: **{sheet_name}**\n"
                summary += f"- Range: **{range}**\n"
                summary += f"- Rows: **{len(df)}**\n"
                summary += f"- Columns: **{', '.join(df.columns)}**\n\n"
                
                # Show first 5 rows as preview
                preview = df.head(5).to_string(index=False)
                if len(preview) > 1000:
                    preview = preview[:997] + "..."
                    
                # Create embed for response
                embed = discord.Embed(
                    title="📊 Google Sheet Data Loaded",
                    description=summary,
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Data Preview (First 5 Rows)",
                    value=f"```\n{preview}\n```",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                
                # Ask for confirmation before inserting data
                confirm_embed = discord.Embed(
                    title="⚠️ Confirm Database Insert",
                    description="Do you want to insert this data into the member table?",
                    color=discord.Color.yellow()
                )
                confirm_embed.add_field(
                    name="Mapping Information",
                    value="Column 1 → RSN\nColumn 4 → Membership Level\nColumn 5 → Previous RSN\nColumn 6 → Alt RSN\nColumn 7 → Discord ID\nColumn 8 → Join Date",
                    inline=False
                )
                
                confirm_message = await interaction.followup.send(embed=confirm_embed, ephemeral=True)
                
                # Add confirmation buttons
                confirm_button = discord.ui.Button(label="Yes, Insert Data", style=discord.ButtonStyle.green, custom_id="confirm_insert")
                cancel_button = discord.ui.Button(label="No, Cancel", style=discord.ButtonStyle.red, custom_id="cancel_insert")
                
                view = discord.ui.View()
                view.add_item(confirm_button)
                view.add_item(cancel_button)
                
                await confirm_message.edit(view=view)
                
                # Wait for button interaction
                try:
                    button_interaction = await self.bot.wait_for(
                        "interaction",
                        check=lambda i: i.user.id == interaction.user.id and i.data.get("custom_id") in ["confirm_insert", "cancel_insert"],
                        timeout=60.0
                    )
                    
                    if button_interaction.data.get("custom_id") == "cancel_insert":
                        await button_interaction.response.send_message("❌ Data insertion cancelled.", ephemeral=True)
                        return
                    
                    # Process the data insertion
                    await button_interaction.response.defer(ephemeral=True)
                    
                    # Get membership level mapping from config
                    membership_levels = self.bot.getConfigValue("discord_role_names")
                    
                    # Insert data into member table
                    inserted_count = 0
                    updated_count = 0
                    skipped_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            # Extract data from row
                            rsn = row[0] if len(row) > 0 else None
                            membership_level = row[3] if len(row) > 3 else None
                            previous_rsn = row[4] if len(row) > 4 else None
                            alt_rsn = row[5] if len(row) > 5 else None
                            discord_id = row[6] if len(row) > 6 else None
                            join_date_str = row[7] if len(row) > 7 else None
                            
                            # Skip if RSN is missing
                            if not rsn:
                                skipped_count += 1
                                continue
                                
                            # Convert join date string to datetime
                            join_date = None
                            if join_date_str and join_date_str.strip().upper() != "N/A":
                                try:
                                    # Use the specific date format %d/%m/%Y
                                    join_date = datetime.datetime.strptime(join_date_str, "%d/%m/%Y")
                                except Exception as e:
                                    print(f"Error parsing date {join_date_str}: {e}")
                            
                            # Map membership level to role ID
                            role_id = None
                            if membership_level and membership_level.strip().upper() != "N/A":
                                # Check if membership_levels is a dictionary
                                if isinstance(membership_levels, dict):
                                    for role_name, role_id_value in membership_levels.items():
                                        if membership_level.lower() in role_name.lower():
                                            role_id = role_id_value
                                            break
                                else:
                                    print(f"Warning: discord_role_names is not a dictionary: {type(membership_levels)}")
                                    # If it's a list, try to find a matching role ID
                                    if isinstance(membership_levels, list):
                                        # Assuming the list contains role IDs in order
                                        try:
                                            # Try to use the membership level as an index
                                            role_id = membership_levels[int(membership_level)]
                                        except (ValueError, IndexError):
                                            print(f"Could not map membership level '{membership_level}' to a role ID")
                            
                            # Handle "N/A" values
                            if previous_rsn and previous_rsn.strip().upper() == "N/A":
                                previous_rsn = None
                                
                            if alt_rsn and alt_rsn.strip().upper() == "N/A":
                                alt_rsn = None
                                
                            if discord_id and discord_id.strip().upper() == "N/A":
                                discord_id = None
                            
                            # Format arrays for PostgreSQL
                            previous_rsn_array = self.format_sql_array(previous_rsn)
                            alt_rsn_array = self.format_sql_array(alt_rsn)
                            
                            # Check if member already exists
                            existing_member = self.bot.selectOne(
                                f"SELECT _id FROM member WHERE rsn = '{rsn}'"
                            )
                            
                            if existing_member:
                                # Update existing member
                                update_sql = f"""
                                UPDATE member 
                                SET membership_level = {role_id if role_id is not None else 'NULL'}, 
                                    previous_rsn = {previous_rsn_array}, 
                                    alt_rsn = {alt_rsn_array}, 
                                    discord_id = {f"'{discord_id}'" if discord_id else 'NULL'}, 
                                    join_date = {f"'{join_date.strftime('%Y-%m-%d')}'" if join_date else 'NULL'}
                                WHERE rsn = '{rsn}'
                                """
                                # print(f"Executing SQL: {update_sql}")
                                self.bot.execute_query(update_sql)
                                updated_count += 1
                            else:
                                # Insert new member
                                insert_sql = f"""
                                INSERT INTO member (rsn, membership_level, previous_rsn, alt_rsn, discord_id, join_date)
                                VALUES (
                                    '{rsn}', 
                                    {role_id if role_id is not None else 'NULL'}, 
                                    {previous_rsn_array}, 
                                    {alt_rsn_array}, 
                                    {f"'{discord_id}'" if discord_id else 'NULL'}, 
                                    {f"'{join_date.strftime('%Y-%m-%d')}'" if join_date else 'NULL'}
                                )
                                """
                                # print(f"Executing SQL: {insert_sql}")
                                self.bot.execute_query(insert_sql)
                                inserted_count += 1
                                
                        except Exception as e:
                            print(f"Error processing row {row}: {e}")
                            error_count += 1
                    
                    # Send summary of database operations
                    result_embed = discord.Embed(
                        title="✅ Database Update Complete",
                        description=f"Successfully processed data from Google Sheet.",
                        color=discord.Color.green()
                    )
                    result_embed.add_field(name="Inserted", value=str(inserted_count), inline=True)
                    result_embed.add_field(name="Updated", value=str(updated_count), inline=True)
                    result_embed.add_field(name="Skipped", value=str(skipped_count), inline=True)
                    result_embed.add_field(name="Errors", value=str(error_count), inline=True)
                    
                    await button_interaction.followup.send(embed=result_embed, ephemeral=True)
                    
                except asyncio.TimeoutError:
                    await confirm_message.edit(content="⏱️ Confirmation timed out. Data insertion cancelled.", view=None)
                
            except HttpError as e:
                error_details = e.error_details if hasattr(e, 'error_details') else str(e)
                error_message = f"❌ Google Sheets API error: {error_details}\n\n"
                error_message += "Possible causes:\n"
                error_message += "1. The sheet ID is incorrect\n"
                error_message += "2. The sheet doesn't exist\n"
                error_message += "3. Your account doesn't have permission to access this sheet\n"
                error_message += "4. The sheet name or range is incorrect\n\n"
                error_message += f"Debug info: {debug_info}"
                
                await interaction.followup.send(error_message, ephemeral=True)
                print(f"Google Sheets API error: {error_details}")
            
        except Exception as e:
            error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await interaction.followup.send(
                f"❌ Error loading data from Google Sheet: {str(e)}\n\n```py\n{error_traceback[:1000]}...```",
                ephemeral=True
            )
            
    def get_google_sheets_service(self):
        """Get an authenticated Google Sheets service."""
        creds = None
        
        # Use a path in the user's home directory for the token file
        token_path = os.path.expanduser(self.TOKEN_PATH)
        
        # Check if token file exists
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            except Exception as e:
                print(f"Error loading token file: {e}")
                # If there's an error loading the token, we'll try to get new credentials
                
        # If credentials are not valid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    # If refresh fails, we'll try to get new credentials
            else:
                try:
                    # Try to use the default browser flow first
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CREDENTIALS_PATH, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Browser authentication failed: {e}")
                    # Fall back to console-based authentication
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CREDENTIALS_PATH, self.SCOPES)
                    creds = flow.run_console()
                
            # Save the credentials for the next run
            try:
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                print(f"Token saved to {token_path}")
            except PermissionError:
                print(f"Permission denied when writing to {token_path}. Token will not be saved.")
            except Exception as e:
                print(f"Error saving token: {e}")
                
        # Build and return the service
        try:
            service = build('sheets', 'v4', credentials=creds)
            return service
        except Exception as e:
            print(f"Error building Google Sheets service: {e}")
            return None

async def setup(bot):
    # Add start_time attribute to bot for uptime tracking
    bot.start_time = datetime.datetime.now()
    await bot.add_cog(Dev(bot)) 