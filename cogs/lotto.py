import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random
from datetime import timedelta

class Lotto(commands.Cog):
    """
    Logic for all clan lotto command handling
    """
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_lottery", description="Create a new lottery")
    @app_commands.describe(
        start_date="When the lottery starts (e.g. '2024-03-20 18:00')",
        duration_days="How many days the lottery runs for",
        entry_fee="Cost per entry in gp",
        max_entries="Maximum number of entries per person"
    )
    async def create_lottery(
        self,
        interaction: discord.Interaction,
        start_date: str,
        duration_days: int,
        entry_fee: int,
        max_entries: int
    ):
        try:
            # Parse the start date
            start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + datetime.timedelta(days=duration_days)
            
            # Validate parameters
            if entry_fee < 0:
                await interaction.response.send_message("Entry fee cannot be negative.", ephemeral=True)
                return
            if max_entries <= 0:
                await interaction.response.send_message("Maximum entries must be greater than 0.", ephemeral=True)
                return
            if start_datetime < datetime.datetime.now():
                await interaction.response.send_message("Start date cannot be in the past.", ephemeral=True)
                return

            # Insert new lottery into database
            self.bot.execute_query(f"""
                INSERT INTO lottery (start_date, end_date, entry_fee, max_entries)
                VALUES ('{start_datetime}', '{end_datetime}', {entry_fee}, {max_entries})
            """)
            
            # Get the lottery ID
            lottery = self.bot.selectOne(f"""
                SELECT lottery_id FROM lottery 
                WHERE start_date = '{start_datetime}' 
                AND end_date = '{end_datetime}' 
                AND entry_fee = {entry_fee} 
                AND max_entries = {max_entries}
                ORDER BY lottery_id DESC LIMIT 1
            """)
            
            lottery_id = lottery[0] if lottery else None

            # Create embed for response
            embed = discord.Embed(
                title="🎟️ New Lottery Created!",
                color=discord.Color.green()
            )
            embed.add_field(name="Start Date", value=start_datetime.strftime("%Y-%m-%d %H:%M"), inline=True)
            embed.add_field(name="End Date", value=end_datetime.strftime("%Y-%m-%d %H:%M"), inline=True)
            embed.add_field(name="Entry Fee", value=self.bot.format_money(entry_fee, "gp"), inline=True)
            embed.add_field(name="Max Entries", value=str(max_entries), inline=True)
            embed.add_field(name="Lottery ID", value=str(lottery_id), inline=True)
            
            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "Invalid date format. Please use YYYY-MM-DD HH:MM format (e.g. '2024-03-20 18:00')",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while creating the lottery: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="select_winner", description="Select a winner for a lottery")
    @app_commands.describe(
        lottery_id="The ID of the lottery to select a winner for"
    )
    async def select_winner(
        self,
        interaction: discord.Interaction,
        lottery_id: int
    ):
        try:
            # Check if lottery exists and get its details
            lottery = self.bot.selectOne(f"""
                SELECT start_date, end_date, winner_id
                FROM lottery
                WHERE lottery_id = {lottery_id}
            """)
            
            if not lottery:
                await interaction.response.send_message(
                    f"Lottery with ID {lottery_id} not found.",
                    ephemeral=True
                )
                return
            
            # Check if lottery has already ended
            if datetime.datetime.now() < lottery[1]:  # end_date
                await interaction.response.send_message(
                    "This lottery is still ongoing. Cannot select a winner yet.",
                    ephemeral=True
                )
                return
            
            # Check if winner has already been selected
            if lottery[2] is not None:  # winner_id
                await interaction.response.send_message(
                    "A winner has already been selected for this lottery.",
                    ephemeral=True
                )
                return
            
            # Get all entries with their weights
            entries = self.bot.selectMany(f"""
                SELECT member_id, entries_purchased
                FROM lottery_entries
                WHERE lottery_id = {lottery_id}
            """)
            print(f"entries: {entries}")
            if not entries:
                await interaction.response.send_message(
                    "No entries found for this lottery.",
                    ephemeral=True
                )
                return
            
            # Create weighted list for random selection
            weighted_entries = []
            entries_by_member = {}
            for entry in entries:
                weighted_entries.extend([entry[0]] * entry[1])  # member_id, entries_purchased
                entries_by_member[entry[0]] = entry[1]
            print(f"weighted_entries: {weighted_entries}")
            # Select winner
            winner_id = random.choice(weighted_entries)
            
            # Update lottery with winner
            self.bot.execute_query(f"""
                UPDATE lottery
                SET winner_id = {winner_id}
                WHERE lottery_id = {lottery_id}
            """)
            
            # Get winner's member details
            winner = self.bot.selectOne(f"""
                SELECT rsn, discord_id
                FROM member
                WHERE _id = {winner_id}
            """)
            
            # Create embed for response
            embed = discord.Embed(
                title="🎉 Lottery Winner Selected!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Lottery ID", value=str(lottery_id), inline=True)
            embed.add_field(name="Winner", value=f"{winner[0]} (@{winner[1]})", inline=True)
            embed.add_field(name="Entries/Total", value=f"{entries_by_member[winner_id]}/{str(len(weighted_entries))}", inline=True)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while selecting the winner: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="lottery_status", description="Display the current status of the active lottery")
    async def lottery_status(
        self,
        interaction: discord.Interaction
    ):
        try:
            # Get the most recent active lottery
            lottery = self.bot.selectOne("""
                SELECT lottery_id, start_date, end_date, entry_fee, max_entries, winner_id
                FROM lottery
                WHERE start_date <= CURRENT_TIMESTAMP 
                AND end_date >= CURRENT_TIMESTAMP
                ORDER BY start_date DESC
                LIMIT 1
            """)
            
            if not lottery:
                await interaction.response.send_message(
                    "There is currently no active lottery.",
                    ephemeral=True
                )
                return

            # Get all entries with member details
            entries = self.bot.selectMany(f"""
                SELECT le.member_id, le.entries_purchased, m.rsn
                FROM lottery_entries le
                JOIN member m ON le.member_id = m._id
                WHERE le.lottery_id = {lottery[0]}
                ORDER BY le.entries_purchased DESC
            """)

            # Calculate time remaining
            now = datetime.datetime.now()
            time_remaining = lottery[2] - now  # end_date - now

            # Format time remaining
            if time_remaining.total_seconds() > 0:
                days = time_remaining.days
                hours = time_remaining.seconds // 3600
                minutes = (time_remaining.seconds % 3600) // 60
                time_str = f"{days}d {hours}h {minutes}m"
            else:
                time_str = "0d 0h 0m"

            # Create embed
            embed = discord.Embed(
                title=f"🎟️ Active Lottery #{lottery[0]}",
                color=discord.Color.blue()
            )

            # Add lottery details
            embed.add_field(
                name="Status",
                value=f"🎟️ Active\nTime Remaining: {time_str}",
                inline=False
            )
            embed.add_field(
                name="Entry Fee",
                value=self.bot.format_money(lottery[3], "gp"),
                inline=True
            )
            embed.add_field(
                name="Max Entries",
                value=str(lottery[4]),
                inline=True
            )

            # Add entries if any exist
            if entries:
                total_entries = sum(entry[1] for entry in entries)
                embed.add_field(
                    name="Total Entries",
                    value=str(total_entries),
                    inline=True
                )
                embed.add_field(
                    name="Total Pot",
                    value=self.bot.format_money(total_entries*lottery[3], "gp"),
                    inline=True
                )
                
                # Add top 5 entries
                entries_text = ""
                for i, (member_id, entries_purchased, rsn) in enumerate(entries[:5], 1):
                    entries_text += f"{i}. {rsn}: {entries_purchased} entries\n"
                if entries:
                    embed.add_field(
                        name="Top Entries",
                        value=entries_text,
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Total Entries",
                    value="0",
                    inline=True
                )
                embed.add_field(
                    name="Top Entries",
                    value="No entries yet",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while checking the lottery status: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="add_lottery_entry", description="Add entries to the active lottery for a user")
    @app_commands.describe(
        rsn="The RSN of the user to add entries for",
        num_entries="Number of entries to add"
    )
    async def add_lottery_entry(
        self,
        interaction: discord.Interaction,
        rsn: str,
        num_entries: int
    ):
        try:
            # Validate parameters
            if num_entries <= 0:
                await interaction.response.send_message(
                    "Number of entries must be greater than 0.",
                    ephemeral=True
                )
                return
                
            # Get the active lottery
            lottery = self.bot.selectOne("""
                SELECT lottery_id, start_date, end_date, entry_fee, max_entries
                FROM lottery
                WHERE start_date <= CURRENT_TIMESTAMP 
                AND end_date >= CURRENT_TIMESTAMP
                ORDER BY start_date DESC
                LIMIT 1
            """)
            
            if not lottery:
                await interaction.response.send_message(
                    "There is currently no active lottery to add entries to.",
                    ephemeral=True
                )
                return
                
            lottery_id, start_date, end_date, entry_fee, max_entries = lottery
            
            # Get the member ID for the RSN
            member = self.bot.selectOne(f"""
                SELECT _id, rsn
                FROM member
                WHERE rsn ILIKE '{rsn}'
            """)
            
            if not member:
                await interaction.response.send_message(
                    f"Member with RSN '{rsn}' not found.",
                    ephemeral=True
                )
                return
                
            member_id, member_rsn = member
            
            # Check if the member already has entries for this lottery
            existing_entries = self.bot.selectOne(f"""
                SELECT entries_purchased
                FROM lottery_entries
                WHERE lottery_id = {lottery_id}
                AND member_id = {member_id}
            """)
            
            current_entries = existing_entries[0] if existing_entries else 0
            total_entries = current_entries + num_entries
            
            # Check if adding these entries would exceed the maximum
            if total_entries > max_entries:
                await interaction.response.send_message(
                    f"Cannot add {num_entries} entries. {member_rsn} already has {current_entries} entries, "
                    f"and the maximum is {max_entries}.",
                    ephemeral=True
                )
                return
                
            # Insert or update the lottery entries
            if existing_entries:
                # Update existing entries
                self.bot.execute_query(f"""
                    UPDATE lottery_entries
                    SET entries_purchased = {total_entries}
                    WHERE lottery_id = {lottery_id}
                    AND member_id = {member_id}
                """)
            else:
                # Insert new entries
                self.bot.execute_query(f"""
                    INSERT INTO lottery_entries (lottery_id, member_id, entries_purchased)
                    VALUES ({lottery_id}, {member_id}, {num_entries})
                """)
                
            # Create embed for response
            embed = discord.Embed(
                title="🎟️ Lottery Entries Added!",
                color=discord.Color.green()
            )
            embed.add_field(name="Lottery ID", value=str(lottery_id), inline=True)
            embed.add_field(name="Member", value=member_rsn, inline=True)
            embed.add_field(name="Entries Added", value=str(num_entries), inline=True)
            embed.add_field(name="Total Entries", value=str(total_entries), inline=True)
            embed.add_field(name="Entry Fee", value=self.bot.format_money(entry_fee, "gp"), inline=True)
            embed.add_field(name="Total Cost", value=self.bot.format_money(entry_fee * num_entries, "gp"), inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while adding lottery entries: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Lotto(bot))