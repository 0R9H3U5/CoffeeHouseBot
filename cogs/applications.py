import discord
from discord.ext import commands
import re
import datetime
import logging
from discord import app_commands

# Set up logging
log = logging.getLogger('discord')
log.setLevel(logging.INFO)

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.application_channel_id = None  # Will be set from config
        self.trial_member_role_id = None    # Will be set from config
        self.timezones = []                 # Will be set from config
        log.info("Applications cog initialized")
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Set up the application channel ID and trial member role ID from config when the cog is ready."""
        try:
            self.application_channel_id = int(self.bot.getConfigValue("application_channel_id"))
            self.trial_member_role_id = int(self.bot.getConfigValue("trial_member_role_id"))
            self.timezones = self.bot.getConfigValue("timezones")
            
            # Register the context menu command
            self.ctx_menu = app_commands.ContextMenu(
                name='Accept Application',
                callback=self.accept_app_context_menu, 
                type=discord.AppCommandType.message,
                guild_ids=[int(self.bot.getConfigValue("test_server_guild_id"))]
            )
            self.bot.tree.add_command(self.ctx_menu)
            await self.bot.tree.sync(guild=self.bot.get_guild(int(self.bot.getConfigValue("test_server_guild_id"))))
            print(f"2: Synced commands to test server!")
            
            log.info(f"Applications cog ready. Application channel ID: {self.application_channel_id}")
            print(f"Applications cog ready. Application channel ID: {self.application_channel_id}")
            for cmd in self.bot.tree.walk_commands():
                print(f"Command: {cmd.name}")
                
        except (KeyError, ValueError) as e:
            log.error(f"Error setting up Applications cog: {e}")
            print(f"Error setting up Applications cog: {e}")
            print("Please ensure 'application_channel_id' and 'trial_member_role_id' are set in config.json")
    
    async def accept_app_context_menu(self, interaction: discord.Interaction, message: discord.Message):
        """Accept an application using the context menu."""
        try:
            # Check if the command is used in the application channel
            if interaction.channel_id != self.application_channel_id:
                await interaction.response.send_message("This command can only be used in the application channel.", ephemeral=True)
                return
                
            # Check if the message matches the application template
            if not self._is_application_message(message.content):
                await interaction.response.send_message("The message does not appear to be a valid application.", ephemeral=True)
                return
                
            # Acknowledge the interaction immediately to prevent timeout
            await interaction.response.defer(ephemeral=False)
            
            # Process the application
            await self._process_application(message, interaction)
            
        except Exception as e:
            log.error(f"Error in accept-app context menu: {e}")
            try:
                # Try to send a followup message if the interaction is still valid
                await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            except discord.errors.NotFound:
                # If the interaction is no longer valid, log the error but don't try to respond
                log.error("Could not send error message: Interaction no longer valid")
    
    async def accept_app(self, interaction: discord.Interaction, message_id: str):
        """Accept an application by providing the message ID."""
        try:
            # Check if the command is used in the application channel
            if interaction.channel_id != self.application_channel_id:
                await interaction.response.send_message("This command can only be used in the application channel.", ephemeral=True)
                return
                
            # Convert message_id to integer
            try:
                message_id_int = int(message_id)
            except ValueError:
                await interaction.response.send_message("Invalid message ID. Please provide a valid message ID.", ephemeral=True)
                return
                
            # Get the referenced message
            try:
                application_message = await interaction.channel.fetch_message(message_id_int)
            except discord.NotFound:
                await interaction.response.send_message("Could not find the application message. Make sure the message ID is correct.", ephemeral=True)
                return
            except discord.Forbidden:
                await interaction.response.send_message("I don't have permission to access that message.", ephemeral=True)
                return
            except Exception as e:
                log.error(f"Error fetching message: {e}")
                await interaction.response.send_message(f"An error occurred while fetching the message: {e}", ephemeral=True)
                return
                
            # Check if the message matches the application template
            if not self._is_application_message(application_message.content):
                await interaction.response.send_message("The message does not appear to be a valid application.", ephemeral=True)
                return
                
            # Acknowledge the interaction immediately to prevent timeout
            await interaction.response.defer(ephemeral=False)
            
            # Process the application using the discord.Message object
            await self._process_application(application_message, interaction)
            
        except Exception as e:
            log.error(f"Error in accept-app command: {e}")
            try:
                # Try to send a followup message if the interaction is still valid
                await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            except discord.errors.NotFound:
                # If the interaction is no longer valid, log the error but don't try to respond
                log.error("Could not send error message: Interaction no longer valid")
    
    def _is_application_message(self, content):
        """Check if a message matches the application template."""
        # Define the expected questions in the application
        expected_questions = [
            "What is your RSN?",
            "How did you find out about the clan?",
            "What are your favorite activities to do on Runescape?",
            "Where do you live and what timezone are you in?",
            "How often do you play?",
            "Have you read our",
            "and do you agree to abide by these rules?",
            "Are you currently in another clan?",
            "How do you drink your Coffee?"
        ]
        
        # Check if all expected questions are in the message
        for question in expected_questions:
            if question not in content:
                log.debug(f"Missing question in application: {question}")
                return False
                
        # Special check for the rules question with special characters
        if "Have you read our" in content and "and do you agree to abide by these rules?" in content:
            # Check if there's some form of "rules" between these two parts
            rules_part = content[content.find("Have you read our") + len("Have you read our"):content.find("and do you agree to abide by these rules?")]
            if "rules" not in rules_part.lower():
                log.debug("Rules question found but 'rules' keyword missing")
                return False
        
        log.debug("All expected questions found in message")
        return True
    
    def _parse_location_timezone(self, content):
        """Parse the location and timezone from the answer to the location/timezone question."""
        # Extract the answer to the location/timezone question
        answer = self._extract_answer(content, "Where do you live and what timezone are you in?")
        if not answer:
            return None, None
            
        # Try to find a timezone in the answer
        timezone = None
        location = answer
        
        # Check if any of the timezone strings are in the answer
        for tz in self.timezones:
            # Look for the timezone with word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(tz) + r'\b'
            match = re.search(pattern, answer, re.IGNORECASE)
            if match:
                timezone = tz
                # Remove the timezone from the answer to get the location
                location = answer[:match.start()].strip() + answer[match.end():].strip()
                # Clean up any remaining punctuation or conjunctions
                location = re.sub(r'\s*[,/]\s*$', '', location)
                location = re.sub(r'\s+and\s+$', '', location)
                break
                
        # If no timezone was found, try to extract it using common patterns
        if not timezone:
            # Look for UTC/GMT +/- X patterns
            utc_match = re.search(r'(UTC|GMT)\s*([+-]\d+)', answer, re.IGNORECASE)
            if utc_match:
                timezone = f"{utc_match.group(1)}{utc_match.group(2)}"
                location = answer[:utc_match.start()].strip() + answer[utc_match.end():].strip()
                location = re.sub(r'\s*[,/]\s*$', '', location)
                location = re.sub(r'\s+and\s+$', '', location)
            else:
                # Look for timezone abbreviations
                tz_match = re.search(r'\b(EST|CST|MST|PST|EDT|CDT|MDT|PDT)\b', answer, re.IGNORECASE)
                if tz_match:
                    timezone = tz_match.group(1)
                    location = answer[:tz_match.start()].strip() + answer[tz_match.end():].strip()
                    location = re.sub(r'\s*[,/]\s*$', '', location)
                    location = re.sub(r'\s+and\s+$', '', location)
        
        # If still no timezone, try to extract it from common phrases
        if not timezone:
            # Look for phrases like "in [timezone]" or "timezone is [timezone]"
            tz_phrase_match = re.search(r'(?:in|timezone is|timezone of|timezone)\s+([A-Za-z\s+]+)(?:\s+time)?', answer, re.IGNORECASE)
            if tz_phrase_match:
                potential_tz = tz_phrase_match.group(1).strip()
                # Check if this potential timezone is in our list
                for tz in self.timezones:
                    if potential_tz.lower() == tz.lower():
                        timezone = tz
                        location = answer[:tz_phrase_match.start()].strip() + answer[tz_phrase_match.end():].strip()
                        location = re.sub(r'\s*[,/]\s*$', '', location)
                        location = re.sub(r'\s+and\s+$', '', location)
                        break
        
        # If we still don't have a timezone, use a default
        if not timezone:
            timezone = "Unknown"
            
        # If location is empty after removing timezone, use a default
        if not location.strip():
            location = "Unknown"
            
        log.debug(f"Parsed location: '{location}', timezone: '{timezone}'")
        return location, timezone
    
    def _check_existing_member(self, rsn: str, discord_id_num: int) -> tuple[bool, str]:
        """Check if a member with the given RSN or Discord ID already exists in the database.
        
        Returns:
            tuple[bool, str]: (exists, message) where exists is True if the member exists,
            and message is a description of which identifier already exists.
        """
        # Check for existing RSN
        rsn_query = f"SELECT rsn FROM member WHERE rsn ILIKE '{rsn}'"
        rsn_result = self.bot.selectOne(rsn_query)
        print(f"RSN Result: {rsn_result}")
        
        # Check for existing Discord ID
        discord_query = f"SELECT discord_id_num FROM member WHERE discord_id_num = {discord_id_num}"
        discord_result = self.bot.selectOne(discord_query)
        print(f"Discord Result: {discord_result}")
        
        if rsn_result and discord_result:
            return True, f"Both RSN '{rsn}' and Discord ID {discord_id_num} are already registered in the clan."
        elif rsn_result:
            return True, f"RSN '{rsn}' is already registered in the clan."
        elif discord_result:
            return True, f"Discord ID {discord_id_num} is already registered in the clan."
        
        return False, ""
    
    async def _process_application(self, message: discord.Message, interaction: discord.Interaction):
        """Process an application message and add the user to the database."""
        try:
            log.info(f"Processing application from {message.author.name}")
            
            # Extract RSN from the message
            rsn = self._extract_answer(message.content, "What is your RSN?")
            
            # Parse location and timezone
            location, timezone = self._parse_location_timezone(message.content)
            
            # Extract additional application questions
            how_found_clan = self._extract_answer(message.content, "How did you find out about the clan?")
            favorite_activities = self._extract_answer(message.content, "What are your favorite activities to do on Runescape?")
            play_frequency = self._extract_answer(message.content, "How often do you play?")
            coffee_preference = self._extract_answer(message.content, "How do you drink your Coffee?")
            
            log.debug(f"Extracted RSN: {rsn}")
            log.debug(f"Extracted location: {location}, timezone: {timezone}")
            log.debug(f"Extracted additional info: found_clan={how_found_clan}, activities={favorite_activities}, frequency={play_frequency}, coffee={coffee_preference}")
            
            if not rsn:
                log.warning(f"No RSN found in application from {message.author.name}")
                await interaction.followup.send(f"I couldn't find the RSN in the application. Please make sure it's clearly stated.", ephemeral=False)
                return
                
            # Get the user's Discord username and ID number
            discord_id = message.author.name  # Use username instead of ID string
            discord_id_num = message.author.id
            
            # Check if the member already exists
            exists, error_message = self._check_existing_member(rsn, discord_id_num)
            if exists:
                log.warning(f"Attempted to add existing member: {error_message}")
                await interaction.followup.send(error_message, ephemeral=True)
                return
            
            # Get the current date for join date
            join_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Insert the user into the database
            query = f"""
            INSERT INTO member (rsn, loc, timezone, discord_id, discord_id_num, join_date, membership_level, active, on_leave, 
                              skill_comp_pts, skill_comp_pts_life, boss_comp_pts, boss_comp_pts_life,
                              how_found_clan, favorite_activities, play_frequency, coffee_preference)
            VALUES ('{rsn}', '{location}', '{timezone}', '{discord_id}', {discord_id_num}, '{join_date}', 0, true, false, 0, 0, 0, 0,
                   '{how_found_clan}', '{favorite_activities}', '{play_frequency}', '{coffee_preference}')
            """
            
            log.debug(f"Executing database query: {query}")
            
            if self.bot.execute_query(query):
                log.info(f"Successfully added {rsn} to database")
                
                # Grant the Trial Member role
                try:
                    member = message.guild.get_member(message.author.id)
                    if member:
                        role = message.guild.get_role(self.trial_member_role_id)
                        if role:
                            log.debug(f"Adding role {role.name} to {member.name}")
                            await member.add_roles(role)
                            
                            # Send confirmation message
                            embed = discord.Embed(
                                title="Application Accepted!",
                                description=f"Welcome to the clan, {rsn}!",
                                color=discord.Color.green()
                            )
                            embed.add_field(name="RSN", value=rsn, inline=True)
                            embed.add_field(name="Location", value=location, inline=True)
                            embed.add_field(name="Timezone", value=timezone, inline=True)
                            embed.add_field(name="Join Date", value=join_date, inline=True)
                            embed.add_field(name="Membership Level", value="Trial Member", inline=True)
                            
                            # Send the embed as a public message (not ephemeral)
                            await interaction.followup.send(embed=embed, ephemeral=False)
                            log.info(f"Application from {rsn} fully processed")
                        else:
                            log.error(f"Trial Member role not found (ID: {self.trial_member_role_id})")
                            await interaction.followup.send(f"The application was processed, but I couldn't find the Trial Member role. Please contact an admin.", ephemeral=True)
                    else:
                        log.error(f"Member object not found for {message.author.name}")
                        await interaction.followup.send(f"The application was processed, but I couldn't find the member object. Please contact an admin.", ephemeral=True)
                except Exception as e:
                    log.error(f"Error granting Trial Member role: {e}")
                    await interaction.followup.send(f"The application was processed, but there was an error granting the role. Please contact an admin.", ephemeral=True)
            else:
                log.error(f"Database query failed for {rsn}")
                await interaction.followup.send(f"There was an error processing the application. Please contact an admin.", ephemeral=True)
                
        except Exception as e:
            log.error(f"Error processing application: {e}")
            try:
                await interaction.followup.send(f"There was an error processing the application. Please contact an admin.", ephemeral=True)
            except discord.errors.NotFound:
                log.error("Could not send error message: Interaction no longer valid")
    
    def _extract_answer(self, content, question):
        """Extract the answer to a specific question from the application message."""
        # Find the question in the content
        question_index = content.find(question)
        if question_index == -1:
            log.debug(f"Question not found in content: {question}")
            return None
            
        # Find the next question or the end of the content
        next_question_index = -1
        for q in ["What is your RSN?", "How did you find out about the clan?", 
                 "What are your favorite activities to do on Runescape?", 
                 "Where do you live and what timezone are you in?",
                 "How often do you play?",
                 "Have you read our",  
                 "and do you agree to abide by these rules?",
                 "Are you currently in another clan?",
                 "How do you drink your Coffee?"]:
            if q != question:
                index = content.find(q, question_index + len(question))
                if index != -1 and (next_question_index == -1 or index < next_question_index):
                    next_question_index = index
        
        # Special handling for the rules question
        if question == "Have you read our":
            # Find the end of the rules question
            rules_end = content.find("and do you agree to abide by these rules?")
            if rules_end != -1:
                next_question_index = rules_end
        
        # Extract the answer
        if next_question_index == -1:
            # No next question found, take until the end
            answer = content[question_index + len(question):].strip()
        else:
            # Take until the next question
            answer = content[question_index + len(question):next_question_index].strip()
            
        log.debug(f"Extracted answer for '{question}': {answer}")
        return answer

async def setup(bot):
    await bot.add_cog(Applications(bot)) 