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
        self.processed_messages = set()  # Track processed message IDs
        log.info("Applications cog initialized")
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Set up the application channel ID and trial member role ID from config when the cog is ready."""
        try:
            self.application_channel_id = int(self.bot.getConfigValue("application_channel_id"))
            self.trial_member_role_id = int(self.bot.getConfigValue("trial_member_role_id"))
            log.info(f"Applications cog ready. Monitoring channel ID: {self.application_channel_id}")
            print(f"Applications cog ready. Monitoring channel ID: {self.application_channel_id}")
        except (KeyError, ValueError) as e:
            log.error(f"Error setting up Applications cog: {e}")
            print(f"Error setting up Applications cog: {e}")
            print("Please ensure 'application_channel_id' and 'trial_member_role_id' are set in config.json")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for application messages in the designated channel."""
        log.debug(f"Applications cog received message: {message.content[:50]}...")
        
        # Ignore messages from bots
        if message.author.bot:
            log.debug("Ignoring message from bot")
            return
            
        # Check if the message is in the application channel
        if message.channel.id != self.application_channel_id:
            log.debug(f"Message not in application channel. Expected: {self.application_channel_id}, Got: {message.channel.id}")
            return
            
        # Check if we've already processed this message
        if message.id in self.processed_messages:
            log.debug(f"Message {message.id} already processed, skipping")
            return
            
        log.debug("Message is in application channel, checking if it matches template")
        
        # Check if the message matches the application template
        if self._is_application_message(message.content):
            log.info(f"Application message detected from {message.author.name}")
            # Mark message as processed before processing to prevent duplicate processing
            self.processed_messages.add(message.id)
            await self._process_application(message)
        else:
            log.debug("Message does not match application template")
    
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
    
    def _verify_binary_response(self, content, question, accepted_value_type: bool):
        """Check if a question has a specific binary answer.
        
        Args:
            content (str): The application message content
            question (str): The question to check
            accepted_value_type (bool): True if the answer is positive, False if it is negative
            
        Returns:
            bool: True if the answer is the opposite of the accepted value type, False otherwise
        """
        answer = self._extract_answer(content, question)
        print(f"Answer: {answer}")
        if not answer:
            return False
        answer = answer.lower()
        
        valid_responses = self.bot.getConfigValue("true_values") if accepted_value_type else self.bot.getConfigValue("false_values")
        print(f"Valid responses: {valid_responses}")

        for val in valid_responses:
            if val in answer:
                return False
        return True
    
    async def _process_application(self, message):
        """Process an application message and add the user to the database."""
        try:
            log.info(f"Processing application from {message.author.name}")
            
            # Check for answer which invalidates application
            rules_question = "and do you agree to abide by these rules?"
            clan_question = "Are you currently in another clan?"
            
            if not self._verify_binary_response(message.content, rules_question, True):
                log.warning(f"Application denied: User did not agree to rules")
                embed = discord.Embed(
                    title="Application Denied",
                    description=f"Sorry, {message.author.mention}, your application has been denied.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Reason", 
                    value="You must agree to abide by our clan rules to join. Please review our rules and apply again if you agree.",
                    inline=False
                )
                await message.channel.send(embed=embed)
                return
                
            if not self._verify_binary_response(message.content, clan_question, False):
                log.warning(f"Application denied: User is in another clan")
                embed = discord.Embed(
                    title="Application Denied",
                    description=f"Sorry, {message.author.mention}, your application has been denied.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Reason", 
                    value="You cannot be a member of multiple clans. Please leave your current clan before applying again.",
                    inline=False
                )
                await message.channel.send(embed=embed)
                return
            
            # Extract RSN and location/timezone from the message
            rsn = self._extract_answer(message.content, "What is your RSN?")
            location_timezone = self._extract_answer(message.content, "Where do you live and what timezone are you in?")
            
            log.debug(f"Extracted RSN: {rsn}")
            log.debug(f"Extracted location/timezone: {location_timezone}")
            
            if not rsn:
                log.warning(f"No RSN found in application from {message.author.name}")
                await message.channel.send(f"{message.author.mention} I couldn't find your RSN in your application. Please make sure it's clearly stated.")
                return
                
            # Get the user's Discord username and ID number
            discord_id = message.author.name  # Use username instead of ID string
            discord_id_num = message.author.id
            
            # Get the current date for join date
            join_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Insert the user into the database
            query = f"""
            INSERT INTO member (rsn, loc, discord_id, discord_id_num, join_date, membership_level, active, on_leave, 
                              skill_comp_pts, skill_comp_pts_life, boss_comp_pts, boss_comp_pts_life)
            VALUES ('{rsn}', '{location_timezone}', '{discord_id}', {discord_id_num}, '{join_date}', 0, true, false, 0, 0, 0, 0)
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
                            embed.add_field(name="Location/Timezone", value=location_timezone, inline=True)
                            embed.add_field(name="Join Date", value=join_date, inline=True)
                            embed.add_field(name="Membership Level", value="Trial Member", inline=True)
                            
                            await message.channel.send(embed=embed)
                            log.info(f"Application from {rsn} fully processed")
                        else:
                            log.error(f"Trial Member role not found (ID: {self.trial_member_role_id})")
                            await message.channel.send(f"{message.author.mention} Your application was processed, but I couldn't find the Trial Member role. Please contact an admin.")
                    else:
                        log.error(f"Member object not found for {message.author.name}")
                        await message.channel.send(f"{message.author.mention} Your application was processed, but I couldn't find your member object. Please contact an admin.")
                except Exception as e:
                    log.error(f"Error granting Trial Member role: {e}")
                    await message.channel.send(f"{message.author.mention} Your application was processed, but there was an error granting your role. Please contact an admin.")
            else:
                log.error(f"Database query failed for {rsn}")
                await message.channel.send(f"{message.author.mention} There was an error processing your application. Please contact an admin.")
                
        except Exception as e:
            log.error(f"Error processing application: {e}")
            await message.channel.send(f"{message.author.mention} There was an error processing your application. Please contact an admin.")
    
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
        print(f"Question: {question}")
        if question == "Have you read our":
            # Find the end of the rules question
            rules_end = content.find("and do you agree to abide by these rules?")
            print("here")
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