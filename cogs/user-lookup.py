from discord.ext import commands
from discord import app_commands

class UserLookup(commands.Cog):
    """
    Logic for all user lookup command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list-members", description="Print out a list of all members")
    async def list_members(self, interaction):
        await interaction.response.defer()
        
        print("list_members")
        all_members = self.bot.selectMany("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member")        
        
        # Check if we have any members
        if not all_members:
            await interaction.followup.send("No members found in the database.")
            return
            
        # Format the member list
        formatted_output = self.format_user_list(all_members)
        
        # Check if the output is too long for Discord (2000 character limit)
        if len(formatted_output) > 1900:  # Leave some room for the code block markers
            # Split the output into chunks
            chunks = self.split_user_list(all_members)
            
            # Send the first chunk
            await interaction.followup.send(f'```\n{chunks[0]}```')
            
            # Send additional chunks if needed
            for i, chunk in enumerate(chunks[1:], 2):
                await interaction.followup.send(f'```\n{chunk}```')
        else:
            # Send the complete output
            await interaction.followup.send(f'```\n{formatted_output}```')

    @app_commands.command(name="list-inactive", description="Print out a list of all inactive members")
    async def list_inactive(self, interaction):
        await interaction.response.defer()
        
        inactive_members = self.bot.selectMany("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member WHERE active=false")
        
        # Check if we have any members
        if not inactive_members:
            await interaction.followup.send("No inactive members found in the database.")
            return
            
        # Format the member list
        formatted_output = self.format_user_list(inactive_members)
        
        # Check if the output is too long for Discord (2000 character limit)
        if len(formatted_output) > 1900:  # Leave some room for the code block markers
            # Split the output into chunks
            chunks = self.split_user_list(inactive_members)
            
            # Send the first chunk
            await interaction.followup.send(f'```\n{chunks[0]}```')
            
            # Send additional chunks if needed
            for i, chunk in enumerate(chunks[1:], 2):
                await interaction.followup.send(f'```\n{chunk}```')
        else:
            # Send the complete output
            await interaction.followup.send(f'```\n{formatted_output}```')

    @app_commands.command(name="list-onleave", description="Print out a list of all members marked on leave")
    async def list_onleave(self, interaction):
        await interaction.response.defer()
        
        on_leave_members = self.bot.selectMany("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member WHERE on_leave=true")
        
        # Check if we have any members
        if not on_leave_members:
            await interaction.followup.send("No members on leave found in the database.")
            return
            
        # Format the member list
        formatted_output = self.format_user_list(on_leave_members)
        
        # Check if the output is too long for Discord (2000 character limit)
        if len(formatted_output) > 1900:  # Leave some room for the code block markers
            # Split the output into chunks
            chunks = self.split_user_list(on_leave_members)
            
            # Send the first chunk
            await interaction.followup.send(f'```\n{chunks[0]}```')
            
            # Send additional chunks if needed
            for i, chunk in enumerate(chunks[1:], 2):
                await interaction.followup.send(f'```\n{chunk}```')
        else:
            # Send the complete output
            await interaction.followup.send(f'```\n{formatted_output}```')
            
    @app_commands.command(name="yellowpages", description="Print a simple directory of RSNs and Discord IDs")
    async def yellowpages(self, interaction):
        await interaction.response.defer()
        
        print("yellowpages")
        all_members = self.bot.selectMany("SELECT rsn, discord_id FROM member ORDER BY rsn")
        
        # Check if we have any members
        if not all_members:
            await interaction.followup.send("No members found in the database.")
            return
            
        # Format the yellowpages
        formatted_output = self.format_yellowpages(all_members)
        
        # Check if the output is too long for Discord (2000 character limit)
        if len(formatted_output) > 1900:  # Leave some room for the code block markers
            # Split the output into chunks
            chunks = self.split_yellowpages(all_members)
            
            # Send the first chunk
            await interaction.followup.send(f'```\n{chunks[0]}```')
            
            # Send additional chunks if needed
            for i, chunk in enumerate(chunks[1:], 2):
                await interaction.followup.send(f'```\n{chunk}```')
        else:
            # Send the complete output
            await interaction.followup.send(f'```\n{formatted_output}```')
            
    def format_user_list(self, list):
        if not list:
            return "No members found."
        
        # Create a more responsive format that works better on different screen sizes
        output = "**Member List**\n\n"
        
        for i, mem in enumerate(list, 1):
            rsn = mem[0]
            discord_id = mem[1] or "Not linked"
            
            # Format alt_rsn array
            alt_rsn = mem[2]
            if alt_rsn and len(alt_rsn) > 0:
                alt_rsn_str = ", ".join(alt_rsn)
            else:
                alt_rsn_str = "None"
            
            # Format previous_rsn array
            prev_rsn = mem[3]
            if prev_rsn and len(prev_rsn) > 0:
                prev_rsn_str = ", ".join(prev_rsn)
            else:
                prev_rsn_str = "None"
            
            # Format each member as a card-like entry
            output += f"** {rsn} **\n"
            output += f" Discord: {discord_id}\n"
            
            # Only show alt/previous RSNs if they exist
            if alt_rsn_str != "None":
                output += f" Alt RSNs: {alt_rsn_str}\n"
            if prev_rsn_str != "None":
                output += f" Previous RSNs: {prev_rsn_str}\n"
            
            # Add a separator between entries
            output += "\n"
        
        # Add count of members
        output += f"**Total: {len(list)} members**"
        
        return output
        
    def format_yellowpages(self, list):
        if not list:
            return "No members found."
            
        # Define column widths
        rsn_width = 25
        discord_width = 30
        
        # Create header
        header = f"╔{'═' * rsn_width}╦{'═' * discord_width}╗\n"
        header += f"║{'RSN'.center(rsn_width)}║{'Discord ID'.center(discord_width)}║\n"
        header += f"╠{'═' * rsn_width}╬{'═' * discord_width}╣\n"
        
        # Create rows
        rows = ""
        for mem in list:
            rsn = str(mem[0]).center(rsn_width)
            discord_id = str(mem[1] or "Not linked").center(discord_width)
            rows += f"║{rsn}║{discord_id}║\n"
        
        # Create footer
        footer = f"╚{'═' * rsn_width}╩{'═' * discord_width}╝\n"
        
        # Add count of members
        count = f"Total: {len(list)} members"
        
        return header + rows + footer + count

    def split_yellowpages(self, list):
        """Split the yellowpages into chunks that fit within Discord's character limit."""
        if not list:
            return ["No members found."]
            
        # Define column widths
        rsn_width = 25
        discord_width = 30
        
        # Create header and footer templates
        header = f"╔{'═' * rsn_width}╦{'═' * discord_width}╗\n"
        header += f"║{'RSN'.center(rsn_width)}║{'Discord ID'.center(discord_width)}║\n"
        header += f"╠{'═' * rsn_width}╬{'═' * discord_width}╣\n"
        
        footer = f"╚{'═' * rsn_width}╩{'═' * discord_width}╝\n"
        
        # Calculate how many rows we can fit in a chunk
        row_template = f"║{' ' * rsn_width}║{' ' * discord_width}║\n"
        row_length = len(row_template)
        
        # Calculate available space for rows (leaving room for header, footer, and count)
        available_space = 1900 - len(header) - len(footer) - 20  # 20 chars for count
        rows_per_chunk = available_space // row_length
        
        # Create chunks
        chunks = []
        total_members = len(list)
        
        for i in range(0, total_members, rows_per_chunk):
            chunk_members = list[i:i+rows_per_chunk]
            
            # Create rows for this chunk
            rows = ""
            for mem in chunk_members:
                rsn = str(mem[0]).center(rsn_width)
                discord_id = str(mem[1] or "Not linked").center(discord_width)
                rows += f"║{rsn}║{discord_id}║\n"
            
            # Add count for this chunk
            count = f"Showing {i+1}-{min(i+rows_per_chunk, total_members)} of {total_members} members"
            
            # Combine header, rows, footer, and count
            chunk = header + rows + footer + count
            
            chunks.append(chunk)
        
        return chunks

    def split_user_list(self, list):
        """Split the user list into chunks that fit within Discord's character limit."""
        if not list:
            return ["No members found."]
            
        # Create a more responsive format that works better on different screen sizes
        chunks = []
        current_chunk = "**Member List**\n\n"
        total_members = len(list)
        current_count = 0
        
        for i, mem in enumerate(list, 1):
            rsn = mem[0]
            discord_id = mem[1] or "Not linked"
            
            # Format alt_rsn array
            alt_rsn = mem[2]
            if alt_rsn and len(alt_rsn) > 0:
                alt_rsn_str = ", ".join(alt_rsn)
            else:
                alt_rsn_str = "None"
            
            # Format previous_rsn array
            prev_rsn = mem[3]
            if prev_rsn and len(prev_rsn) > 0:
                prev_rsn_str = ", ".join(prev_rsn)
            else:
                prev_rsn_str = "None"
            
            # Format each member as a card-like entry
            member_entry = f"** {rsn} **\n"
            member_entry += f"   Discord: {discord_id}\n"
            
            # Only show alt/previous RSNs if they exist
            if alt_rsn_str != "None":
                member_entry += f"   Alt RSNs: {alt_rsn_str}\n"
            if prev_rsn_str != "None":
                member_entry += f"   Previous RSNs: {prev_rsn_str}\n"
            
            # Add a separator between entries
            member_entry += "\n"
            
            # Check if adding this member would exceed the character limit
            if len(current_chunk) + len(member_entry) > 1900:
                # Add count to current chunk
                current_chunk += f"**Showing {current_count+1}-{i-1} of {total_members} members**"
                
                # Add current chunk to chunks list
                chunks.append(current_chunk)
                
                # Start a new chunk
                current_chunk = "**Member List (Continued)**\n\n"
                current_count = i - 1
            
            # Add member to current chunk
            current_chunk += member_entry
        
        # Add the last chunk if it's not empty
        if current_chunk:
            # Add count to last chunk
            current_chunk += f"**Showing {current_count+1}-{total_members} of {total_members} members**"
            chunks.append(current_chunk)
        
        return chunks

async def setup(bot):
    await bot.add_cog(UserLookup(bot))