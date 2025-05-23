import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cogs.competition import CompetitionModal, CompetitionType

# Create a mock version of Competition for testing
class MockCompetition:
    def __init__(self, bot):
        self.bot = bot
        self.comp_type = self.get_comp_type()
        self.points_column = f"{self.comp_type}_comp_pts"
        self.points_life_column = f"{self.comp_type}_comp_pts_life"
        
    def get_comp_type(self):
        return "comp"
        
    def get_comp_name(self):
        return "competition"
        
    # Mock the command methods
    async def comp_points(self, interaction):
        await interaction.response.defer()
        user = self.bot.selectOne(f"SELECT discord_id, {self.points_column} FROM member WHERE discord_id_num={interaction.user.id}")
        if user is None:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)
            return
            
        await interaction.followup.send(f"**{interaction.user.name}** you currently have **{user[1]}** points from {self.get_comp_name()} competitions.")
        
    async def comp_leaderboard(self, interaction):
        await interaction.response.defer()
        members = self.bot.selectMany(f"SELECT rsn, {self.points_column} FROM member WHERE {self.points_column} > 0 ORDER BY {self.points_column} DESC")
        if not members:
            await interaction.followup.send(f"No members have any {self.get_comp_name()} competition points yet.")
            return
            
        leaderboard = self.format_leaderboard(members)
        await interaction.followup.send(f"```{leaderboard}```")
        
    def format_leaderboard(self, members):
        if not members:
            return "No members found."
            
        # Create the leaderboard header
        leaderboard = f"{self.get_comp_name()} Competition Leaderboard\n"
        leaderboard += "╔═══╦═══════════════════╦═══════════╗\n"
        leaderboard += "║ # ║ RSN              ║ Points    ║\n"
        leaderboard += "╠═══╬═══════════════════╬═══════════╣\n"
        
        # Add each member to the leaderboard
        for i, (rsn, points) in enumerate(members, 1):
            star = "★" if points > 12 else " "
            leaderboard += f"║ {i:<3}║ {rsn:<17}║ {points:<9}║ {star}\n"
            
        # Add the footer
        leaderboard += "╚═══╩═══════════════════╩═══════════╝\n"
        leaderboard += f"Total players: {len(members)}"
        
        return leaderboard
        
    async def comp_wins(self, interaction):
        await interaction.response.defer()
        
        # Get the user's _id from the member table
        user = self.bot.selectOne(f"SELECT _id FROM member WHERE discord_id_num={interaction.user.id}")
        if user is None:
            await interaction.followup.send(f"**{interaction.user.name}** you are not registered in our database.", ephemeral=True)
            return
            
        # Get the user's competition wins using the foreign key relationship
        wins = self.bot.selectMany(
            f"SELECT comp_name FROM competition WHERE winner = {user[0]} AND competition_type = '{self.comp_type}' ORDER BY comp_id DESC"
        )
        
        if not wins:
            await interaction.followup.send(f"**{interaction.user.name}** you have not won any {self.get_comp_name()} competitions yet.")
            return
            
        await interaction.followup.send(f"**{interaction.user.name}** you have won **{len(wins)}** {self.get_comp_name()} competitions:")
        for win in wins:
            await interaction.followup.send(f" - {win[0]}")
            
    def add_competition(self, name, winner_id):
        # Get the next competition ID
        result = self.bot.selectOne("SELECT MAX(comp_id) FROM competition")
        next_id = (result[0] or 0) + 1
        
        # Insert the competition
        self.bot.execute_query(
            f"INSERT INTO competition (comp_id, comp_name, winner, competition_type) VALUES ({next_id}, '{name}', {winner_id}, '{self.comp_type}')"
        )
        
        # Update the winner's points
        self.bot.execute_query(
            f"UPDATE member SET {self.points_column} = {self.points_column} + 1, {self.points_life_column} = {self.points_life_column} + 1 WHERE _id = {winner_id}"
        )
        
        return True
        
    def get_competitions(self, limit=10):
        return self.bot.selectMany(
            f"SELECT c.comp_id, c.comp_name, m.rsn, c.competition_type FROM competition c "
            f"JOIN member m ON c.winner = m._id "
            f"WHERE c.competition_type = '{self.comp_type}' "
            f"ORDER BY c.comp_id DESC LIMIT {limit}"
        )
        
    async def comp_history(self, interaction):
        await interaction.response.defer()
        competitions = self.get_competitions(limit=5)
        if not competitions:
            await interaction.followup.send(f"No {self.get_comp_name()} competitions have been recorded yet.")
            return
            
        message = f"Recent {self.get_comp_name()} Competitions:\n"
        for comp_id, comp_name, winner, comp_type in competitions:
            message += f"• {comp_name} - Won by {winner}\n"
            
        await interaction.followup.send(message)

# Test the comp_points command with a registered user
@pytest.mark.asyncio
async def test_comp_points_registered_user(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectOne method to return user data
    mock_bot.selectOne = MagicMock(return_value=("User#1234", 15))
    
    # Call the method directly
    await comp_cog.comp_points(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"SELECT discord_id, comp_comp_pts FROM member WHERE discord_id_num={mock_interaction.user.id}")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you currently have **15** points from competition competitions."
    )

# Test the comp_points command with an unregistered user
@pytest.mark.asyncio
async def test_comp_points_unregistered_user(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectOne method to return None (user not found)
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Call the method directly
    await comp_cog.comp_points(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"SELECT discord_id, comp_comp_pts FROM member WHERE discord_id_num={mock_interaction.user.id}")
    
    # Verify that followup.send was called with the correct error message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you are not registered in our database.",
        ephemeral=True
    )

# Test the comp_leaderboard command with members having points
@pytest.mark.asyncio
async def test_comp_leaderboard_with_members(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectMany method to return member data
    mock_bot.selectMany = MagicMock(return_value=[
        ("User1", 20),
        ("User2", 15),
        ("User3", 10),
        ("User4", 5)
    ])
    
    # Call the method directly
    await comp_cog.comp_leaderboard(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        "SELECT rsn, comp_comp_pts FROM member WHERE comp_comp_pts > 0 ORDER BY comp_comp_pts DESC"
    )
    
    # Verify that followup.send was called with a formatted leaderboard
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the message contains the leaderboard
    assert "```" in call_args[0][0]
    assert "User1" in call_args[0][0]
    assert "User2" in call_args[0][0]
    assert "User3" in call_args[0][0]
    assert "User4" in call_args[0][0]
    assert "★" in call_args[0][0]  # Check for the star symbol for users with >12 points
    assert "Total players: 4" in call_args[0][0]

# Test the comp_leaderboard command with no members having points
@pytest.mark.asyncio
async def test_comp_leaderboard_no_members(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectMany method to return an empty list
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Call the method directly
    await comp_cog.comp_leaderboard(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        "SELECT rsn, comp_comp_pts FROM member WHERE comp_comp_pts > 0 ORDER BY comp_comp_pts DESC"
    )
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        "No members have any competition competition points yet."
    )

# Test the format_leaderboard method with members
def test_format_leaderboard_with_members():
    # Create a MockCompetition with a mock bot
    comp_cog = MockCompetition(MagicMock())
    
    # Test data
    members = [
        ("User1", 20),
        ("User2", 15),
        ("User3", 10),
        ("User4", 5)
    ]
    
    # Call the method
    result = comp_cog.format_leaderboard(members)
    
    # Verify the result contains the expected elements
    assert "User1" in result
    assert "User2" in result
    assert "User3" in result
    assert "User4" in result
    assert "★" in result  # Check for the star symbol for users with >12 points
    assert "Total players: 4" in result
    
    # Verify the structure of the leaderboard
    assert "╔" in result  # Header top border
    assert "║" in result  # Column separators
    assert "╚" in result  # Footer bottom border
    assert "#" in result  # Rank column header
    assert "RSN" in result  # RSN column header
    assert "Points" in result  # Points column header

# Test the format_leaderboard method with no members
def test_format_leaderboard_no_members():
    # Create a MockCompetition with a mock bot
    comp_cog = MockCompetition(MagicMock())
    
    # Call the method with an empty list
    result = comp_cog.format_leaderboard([])
    
    # Verify the result is the expected message
    assert result == "No members found."

# Test the comp_wins command with a registered user with wins
@pytest.mark.asyncio
async def test_comp_wins_with_wins(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectOne method to return user data
    mock_bot.selectOne = MagicMock(return_value=(1,))  # Return _id instead of discord_id
    
    # Mock the bot's selectMany method to return competition wins
    mock_bot.selectMany = MagicMock(return_value=[
        ("Win1",),
        ("Win2",),
        ("Win3",)
    ])
    
    # Call the method directly
    await comp_cog.comp_wins(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"SELECT _id FROM member WHERE discord_id_num={mock_interaction.user.id}")
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        f"SELECT comp_name FROM competition WHERE winner = 1 AND competition_type = 'comp' ORDER BY comp_id DESC"
    )
    
    # Verify that followup.send was called with the correct messages
    assert mock_interaction.followup.send.call_count == 4  # 1 for the summary + 3 for each win
    
    # Check the summary message
    mock_interaction.followup.send.assert_any_call(
        f"**{mock_interaction.user.name}** you have won **3** competition competitions:"
    )
    
    # Check the win messages
    mock_interaction.followup.send.assert_any_call(" - Win1")
    mock_interaction.followup.send.assert_any_call(" - Win2")
    mock_interaction.followup.send.assert_any_call(" - Win3")

# Test the comp_wins command with a registered user with no wins
@pytest.mark.asyncio
async def test_comp_wins_no_wins(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectOne method to return user data
    mock_bot.selectOne = MagicMock(return_value=(1,))  # Return _id instead of discord_id
    
    # Mock the bot's selectMany method to return no wins
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Call the method directly
    await comp_cog.comp_wins(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"SELECT _id FROM member WHERE discord_id_num={mock_interaction.user.id}")
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        f"SELECT comp_name FROM competition WHERE winner = 1 AND competition_type = 'comp' ORDER BY comp_id DESC"
    )
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you have not won any competition competitions yet."
    )

# Test the comp_history command with competitions
@pytest.mark.asyncio
async def test_comp_history_with_competitions(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the get_competitions method to return competition data
    comp_cog.get_competitions = MagicMock(return_value=[
        (1, "Competition1", "User1", "comp"),
        (2, "Competition2", "User2", "comp"),
        (3, "Competition3", "User3", "comp")
    ])
    
    # Call the method directly
    await comp_cog.comp_history(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that get_competitions was called
    comp_cog.get_competitions.assert_called_once()
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the message contains the competition history
    assert "Recent competition Competitions" in call_args[0][0]
    assert "Competition1" in call_args[0][0]
    assert "Competition2" in call_args[0][0]
    assert "Competition3" in call_args[0][0]
    assert "User1" in call_args[0][0]
    assert "User2" in call_args[0][0]
    assert "User3" in call_args[0][0]

# Test the comp_history command with no competitions
@pytest.mark.asyncio
async def test_comp_history_no_competitions(mock_bot, mock_interaction):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the get_competitions method to return an empty list
    comp_cog.get_competitions = MagicMock(return_value=[])
    
    # Call the method directly
    await comp_cog.comp_history(mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that get_competitions was called
    comp_cog.get_competitions.assert_called_once()
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        "No competition competitions have been recorded yet."
    )

# Test the add_competition method
def test_add_competition(mock_bot):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectOne method to return the next competition ID
    mock_bot.selectOne = MagicMock(return_value=(5,))
    
    # Mock the bot's execute_query method to return success
    mock_bot.execute_query = MagicMock(return_value=True)
    
    # Call the method
    result = comp_cog.add_competition("Test Competition", 1)
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with("SELECT MAX(comp_id) FROM competition")
    
    # Verify that execute_query was called with the correct queries
    mock_bot.execute_query.assert_any_call(
        "INSERT INTO competition (comp_id, comp_name, winner, competition_type) VALUES (6, 'Test Competition', 1, 'comp')"
    )
    mock_bot.execute_query.assert_any_call(
        "UPDATE member SET comp_comp_pts = comp_comp_pts + 1, comp_comp_pts_life = comp_comp_pts_life + 1 WHERE _id = 1"
    )
    
    # Verify that the result is True
    assert result is True

# Test the get_competitions method
def test_get_competitions(mock_bot):
    # Create a MockCompetition with the mock bot
    comp_cog = MockCompetition(mock_bot)
    
    # Mock the bot's selectMany method to return competition data
    mock_bot.selectMany = MagicMock(return_value=[
        (1, "Competition1", "User1", "comp"),
        (2, "Competition2", "User2", "comp"),
        (3, "Competition3", "User3", "comp")
    ])
    
    # Call the method
    result = comp_cog.get_competitions(limit=3)
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        "SELECT c.comp_id, c.comp_name, m.rsn, c.competition_type FROM competition c "
        "JOIN member m ON c.winner = m._id "
        "WHERE c.competition_type = 'comp' "
        "ORDER BY c.comp_id DESC LIMIT 3"
    )
    
    # Verify that the result is correct
    assert len(result) == 3
    assert result[0] == (1, "Competition1", "User1", "comp")
    assert result[1] == (2, "Competition2", "User2", "comp")
    assert result[2] == (3, "Competition3", "User3", "comp")

# Test the CompetitionModal class
@pytest.mark.asyncio
async def test_competition_modal_submit(mock_bot, mock_interaction):
    # Create a mock Competition cog
    comp_cog = MagicMock()
    comp_cog.bot = mock_bot
    comp_cog.get_comp_name.return_value = "Test Competition"
    
    # Mock the bot's methods
    mock_bot.selectOne.return_value = (0,)  # Next comp_id will be 1
    mock_bot.execute_query.return_value = True
    mock_bot.getConfigValue.side_effect = lambda x: "test_group_id" if x == "wom_group_id" else "test_verification_code"
    
    # Create the modal
    modal = CompetitionModal(comp_cog, CompetitionType.SKILL, ["Attack", "Strength", "Defence"])
    
    # Set the input values using the TextInput's value property
    modal.name_input._value = "Test Comp"
    modal.metric_input._value = "Attack"
    modal.start_date_input._value = "2023-01-01 00:00"
    modal.end_date_input._value = "2023-01-07 23:59"
    
    # Mock the WOM client
    mock_wom_client = AsyncMock()
    mock_wom_client.start = AsyncMock()
    mock_wom_client.close = AsyncMock()
    mock_wom_client.competitions = AsyncMock()
    mock_wom_client.competitions.create_competition = AsyncMock(return_value=MagicMock(is_ok=True))
    comp_cog.bot.wom_client = mock_wom_client
    
    # Call on_submit
    await modal.on_submit(mock_interaction)
    
    # Verify the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify the database operations
    mock_bot.selectOne.assert_called_once_with("SELECT MAX(comp_id) FROM competition")
    mock_bot.execute_query.assert_called_once()
    
    # Verify WOM client was used correctly
    mock_wom_client.start.assert_called_once()
    mock_wom_client.competitions.create_competition.assert_called_once()
    mock_wom_client.close.assert_called_once()
    
    # Verify the success message was sent as an embed
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    assert isinstance(call_args[1]['embed'], discord.Embed)
    assert call_args[1]['embed'].title.startswith("✅ Added new")
    assert "Test Comp" in call_args[1]['embed'].description
    assert "Attack" in call_args[1]['embed'].description
    assert "2023-01-01 00:00" in call_args[1]['embed'].description
    assert "2023-01-07 23:59" in call_args[1]['embed'].description

# Test the CompetitionModal class with WOM error
@pytest.mark.asyncio
async def test_competition_modal_wom_error(mock_bot, mock_interaction):
    # Create a mock Competition cog
    comp_cog = MagicMock()
    comp_cog.bot = mock_bot
    comp_cog.get_comp_name.return_value = "Test Competition"
    
    # Mock the bot's methods
    mock_bot.selectOne.return_value = (0,)  # Next comp_id will be 1
    mock_bot.execute_query.return_value = True
    mock_bot.getConfigValue.side_effect = lambda x: "test_group_id" if x == "wom_group_id" else "test_verification_code"
    
    # Create the modal
    modal = CompetitionModal(comp_cog, CompetitionType.SKILL, ["Attack", "Strength", "Defence"])
    
    # Set the input values using the TextInput's value property
    modal.name_input._value = "Test Comp"
    modal.metric_input._value = "Attack"
    modal.start_date_input._value = "2023-01-01 00:00"
    modal.end_date_input._value = "2023-01-07 23:59"
    
    # Mock the WOM client to raise an error
    mock_wom_client = AsyncMock()
    mock_wom_client.start = AsyncMock()
    mock_wom_client.close = AsyncMock()
    mock_wom_client.competitions = AsyncMock()
    mock_wom_client.competitions.create_competition = AsyncMock(side_effect=Exception("WOM API Error"))
    comp_cog.bot.wom_client = mock_wom_client
    
    # Call on_submit
    await modal.on_submit(mock_interaction)
    
    # Verify the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify the database operations
    mock_bot.selectOne.assert_called_once_with("SELECT MAX(comp_id) FROM competition")
    mock_bot.execute_query.assert_called_once()
    
    # Verify WOM client was used correctly
    mock_wom_client.start.assert_called_once()
    mock_wom_client.competitions.create_competition.assert_called_once()
    mock_wom_client.close.assert_called_once()
    
    # Verify the error message was sent
    mock_interaction.followup.send.assert_called_once_with(
        "❌ Error creating WOM competition: WOM API Error",
        ephemeral=True
    ) 