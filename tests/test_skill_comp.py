import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SkillComp cog
from cogs.skill_comp import SkillComp

# Test the skill_comp_points command with a registered user
@pytest.mark.asyncio
async def test_skill_comp_points_registered_user(mock_bot, mock_interaction):
    # Create a SkillComp cog with the mock bot
    skill_comp_cog = SkillComp(mock_bot)
    
    # Mock the bot's selectOne method to return user data
    mock_bot.selectOne = MagicMock(return_value=("User#1234", 15))
    
    # Access the callback function directly
    callback = skill_comp_cog.skill_comp_points.callback
    
    # Call the callback function directly
    await callback(skill_comp_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"SELECT discord_id, skill_comp_pts FROM member WHERE discord_id_num={mock_interaction.user.id}")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you currently have **15** points from skill week competitions."
    )

# Test the skill_comp_points command with an unregistered user
@pytest.mark.asyncio
async def test_skill_comp_points_unregistered_user(mock_bot, mock_interaction):
    # Create a SkillComp cog with the mock bot
    skill_comp_cog = SkillComp(mock_bot)
    
    # Mock the bot's selectOne method to return None (user not found)
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Access the callback function directly
    callback = skill_comp_cog.skill_comp_points.callback
    
    # Call the callback function directly
    await callback(skill_comp_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"SELECT discord_id, skill_comp_pts FROM member WHERE discord_id_num={mock_interaction.user.id}")
    
    # Verify that followup.send was called with the correct error message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you are not registered in our database.",
        ephemeral=True
    )

# Test the skill_comp_leaderboard command with members having points
@pytest.mark.asyncio
async def test_skill_comp_leaderboard_with_members(mock_bot, mock_interaction):
    # Create a SkillComp cog with the mock bot
    skill_comp_cog = SkillComp(mock_bot)
    
    # Mock the bot's selectMany method to return member data
    mock_bot.selectMany = MagicMock(return_value=[
        ("User1", 20),
        ("User2", 15),
        ("User3", 10),
        ("User4", 5)
    ])
    
    # Access the callback function directly
    callback = skill_comp_cog.skill_comp_leaderboard.callback
    
    # Call the callback function directly
    await callback(skill_comp_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        "SELECT rsn, skill_comp_pts FROM member WHERE skill_comp_pts > 0 ORDER BY skill_comp_pts DESC"
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

# Test the skill_comp_leaderboard command with no members having points
@pytest.mark.asyncio
async def test_skill_comp_leaderboard_no_members(mock_bot, mock_interaction):
    # Create a SkillComp cog with the mock bot
    skill_comp_cog = SkillComp(mock_bot)
    
    # Mock the bot's selectMany method to return an empty list
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = skill_comp_cog.skill_comp_leaderboard.callback
    
    # Call the callback function directly
    await callback(skill_comp_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with(
        "SELECT rsn, skill_comp_pts FROM member WHERE skill_comp_pts > 0 ORDER BY skill_comp_pts DESC"
    )
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        "No members have any skill competition points yet."
    )

# Test the format_leaderboard method with members
def test_format_leaderboard_with_members():
    # Create a SkillComp cog with a mock bot
    skill_comp_cog = SkillComp(MagicMock())
    
    # Test data
    members = [
        ("User1", 20),
        ("User2", 15),
        ("User3", 10),
        ("User4", 5)
    ]
    
    # Call the method
    result = skill_comp_cog.format_leaderboard(members)
    
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
    # Create a SkillComp cog with a mock bot
    skill_comp_cog = SkillComp(MagicMock())
    
    # Call the method with an empty list
    result = skill_comp_cog.format_leaderboard([])
    
    # Verify the result is the expected message
    assert result == "No members found." 