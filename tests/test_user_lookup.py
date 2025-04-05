import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the UserLookup cog
from cogs.user_lookup import UserLookup

# Test the list_members command with members
@pytest.mark.asyncio
async def test_list_members_with_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return member data
    mock_bot.selectMany = MagicMock(return_value=[
        ("User1", "User1#1234", ["Alt1", "Alt2"], ["Prev1"]),
        ("User2", "User2#5678", [], []),
        ("User3", None, ["Alt3"], ["Prev2", "Prev3"])
    ])
    
    # Access the callback function directly
    callback = user_lookup_cog.list_members.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member")
    
    # Verify that followup.send was called with a formatted member list
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the message contains the member list
    assert "```" in call_args[0][0]
    assert "User1" in call_args[0][0]
    assert "User2" in call_args[0][0]
    assert "User3" in call_args[0][0]
    assert "Alt1" in call_args[0][0]
    assert "Alt2" in call_args[0][0]
    assert "Alt3" in call_args[0][0]
    assert "Prev1" in call_args[0][0]
    assert "Prev2" in call_args[0][0]
    assert "Prev3" in call_args[0][0]
    assert "Not linked" in call_args[0][0]
    assert "Total: 3 members" in call_args[0][0]

# Test the list_members command with no members
@pytest.mark.asyncio
async def test_list_members_no_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return an empty list
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = user_lookup_cog.list_members.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with("No members found in the database.")

# Test the list_inactive command with members
@pytest.mark.asyncio
async def test_list_inactive_with_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return member data
    mock_bot.selectMany = MagicMock(return_value=[
        ("Inactive1", "Inactive1#1234", ["Alt1"], []),
        ("Inactive2", None, [], [])
    ])
    
    # Access the callback function directly
    callback = user_lookup_cog.list_inactive.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member WHERE active=false")
    
    # Verify that followup.send was called with a formatted member list
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the message contains the member list
    assert "```" in call_args[0][0]
    assert "Inactive1" in call_args[0][0]
    assert "Inactive2" in call_args[0][0]
    assert "Alt1" in call_args[0][0]
    assert "Not linked" in call_args[0][0]
    assert "Total: 2 members" in call_args[0][0]

# Test the list_inactive command with no members
@pytest.mark.asyncio
async def test_list_inactive_no_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return an empty list
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = user_lookup_cog.list_inactive.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member WHERE active=false")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with("No inactive members found in the database.")

# Test the list_onleave command with members
@pytest.mark.asyncio
async def test_list_onleave_with_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return member data
    mock_bot.selectMany = MagicMock(return_value=[
        ("OnLeave1", "OnLeave1#1234", [], []),
        ("OnLeave2", "OnLeave2#5678", ["Alt1"], ["Prev1"])
    ])
    
    # Access the callback function directly
    callback = user_lookup_cog.list_onleave.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member WHERE on_leave=true")
    
    # Verify that followup.send was called with a formatted member list
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the message contains the member list
    assert "```" in call_args[0][0]
    assert "OnLeave1" in call_args[0][0]
    assert "OnLeave2" in call_args[0][0]
    assert "Alt1" in call_args[0][0]
    assert "Prev1" in call_args[0][0]
    assert "Total: 2 members" in call_args[0][0]

# Test the list_onleave command with no members
@pytest.mark.asyncio
async def test_list_onleave_no_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return an empty list
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = user_lookup_cog.list_onleave.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id, alt_rsn, previous_rsn FROM member WHERE on_leave=true")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with("No members on leave found in the database.")

# Test the yellowpages command with members
@pytest.mark.asyncio
async def test_yellowpages_with_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return member data
    mock_bot.selectMany = MagicMock(return_value=[
        ("User1", "User1#1234"),
        ("User2", "User2#5678"),
        ("User3", None)
    ])
    
    # Access the callback function directly
    callback = user_lookup_cog.yellowpages.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id FROM member ORDER BY rsn")
    
    # Verify that followup.send was called with a formatted yellowpages
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the message contains the yellowpages
    assert "```" in call_args[0][0]
    assert "User1" in call_args[0][0]
    assert "User2" in call_args[0][0]
    assert "User3" in call_args[0][0]
    assert "User1#1234" in call_args[0][0]
    assert "User2#5678" in call_args[0][0]
    assert "Not linked" in call_args[0][0]
    assert "Total: 3 members" in call_args[0][0]
    
    # Check for table formatting
    assert "╔" in call_args[0][0]  # Header top border
    assert "║" in call_args[0][0]  # Column separators
    assert "╚" in call_args[0][0]  # Footer bottom border
    assert "RSN" in call_args[0][0]  # RSN column header
    assert "Discord ID" in call_args[0][0]  # Discord ID column header

# Test the yellowpages command with no members
@pytest.mark.asyncio
async def test_yellowpages_no_members(mock_bot, mock_interaction):
    # Create a UserLookup cog with the mock bot
    user_lookup_cog = UserLookup(mock_bot)
    
    # Mock the bot's selectMany method to return an empty list
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = user_lookup_cog.yellowpages.callback
    
    # Call the callback function directly
    await callback(user_lookup_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectMany was called with the correct query
    mock_bot.selectMany.assert_called_once_with("SELECT rsn, discord_id FROM member ORDER BY rsn")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with("No members found in the database.")

# Test the format_user_list method with members
def test_format_user_list_with_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Test data
    members = [
        ("User1", "User1#1234", ["Alt1", "Alt2"], ["Prev1"]),
        ("User2", "User2#5678", [], []),
        ("User3", None, ["Alt3"], ["Prev2", "Prev3"])
    ]
    
    # Call the method
    result = user_lookup_cog.format_user_list(members)
    
    # Verify the result contains the expected elements
    assert "User1" in result
    assert "User2" in result
    assert "User3" in result
    assert "User1#1234" in result
    assert "User2#5678" in result
    assert "Not linked" in result
    assert "Alt1" in result
    assert "Alt2" in result
    assert "Alt3" in result
    assert "Prev1" in result
    assert "Prev2" in result
    assert "Prev3" in result
    assert "Total: 3 members" in result

# Test the format_user_list method with no members
def test_format_user_list_no_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Call the method with an empty list
    result = user_lookup_cog.format_user_list([])
    
    # Verify the result is the expected message
    assert result == "No members found."

# Test the format_yellowpages method with members
def test_format_yellowpages_with_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Test data
    members = [
        ("User1", "User1#1234"),
        ("User2", "User2#5678"),
        ("User3", None)
    ]
    
    # Call the method
    result = user_lookup_cog.format_yellowpages(members)
    
    # Verify the result contains the expected elements
    assert "User1" in result
    assert "User2" in result
    assert "User3" in result
    assert "User1#1234" in result
    assert "User2#5678" in result
    assert "Not linked" in result
    assert "Total: 3 members" in result
    
    # Verify the structure of the yellowpages
    assert "╔" in result  # Header top border
    assert "║" in result  # Column separators
    assert "╚" in result  # Footer bottom border
    assert "RSN" in result  # RSN column header
    assert "Discord ID" in result  # Discord ID column header

# Test the format_yellowpages method with no members
def test_format_yellowpages_no_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Call the method with an empty list
    result = user_lookup_cog.format_yellowpages([])
    
    # Verify the result is the expected message
    assert result == "No members found."

# Test the split_yellowpages method with members
def test_split_yellowpages_with_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Test data - create a large list to ensure splitting
    members = [("User" + str(i), "User" + str(i) + "#1234") for i in range(1, 101)]
    
    # Call the method
    chunks = user_lookup_cog.split_yellowpages(members)
    
    # Verify we got multiple chunks
    assert len(chunks) > 1
    
    # Verify each chunk has the expected structure
    for chunk in chunks:
        assert "╔" in chunk  # Header top border
        assert "║" in chunk  # Column separators
        assert "╚" in chunk  # Footer bottom border
        assert "RSN" in chunk  # RSN column header
        assert "Discord ID" in chunk  # Discord ID column header
        assert "Showing" in chunk  # Chunk indicator
        assert "of 100 members" in chunk  # Total count

# Test the split_yellowpages method with no members
def test_split_yellowpages_no_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Call the method with an empty list
    chunks = user_lookup_cog.split_yellowpages([])
    
    # Verify we got a single chunk with the expected message
    assert len(chunks) == 1
    assert chunks[0] == "No members found."

# Test the split_user_list method with members
def test_split_user_list_with_members():
    # Create a UserLookup cog with a mock bot
    user_lookup_cog = UserLookup(MagicMock())
    
    # Test data - create a large list to ensure splitting
    members = [("User" + str(i), "User" + str(i) + "#1234", [], []) for i in range(1, 101)]
    
    # Call the method
    chunks = user_lookup_cog.split_user_list(members)
    
    # Verify we got multiple chunks
    assert len(chunks) > 1
    
    # Verify each chunk has the expected structure
    for chunk in chunks:
        assert "Member List" in chunk
        assert "User" in chunk
        assert "Discord:" in chunk
        assert "Showing" in chunk  # Check for the chunk indicator
        assert "of 100 members" in chunk  # Check for the total count 