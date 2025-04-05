import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import datetime
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the General cog
from cogs.general import General

# Test the promotion_when command with a registered user who has a next promotion date
@pytest.mark.asyncio
async def test_promotion_when_with_next_promotion(mock_bot, mock_interaction):
    # Create a General cog with the mock bot
    general_cog = General(mock_bot)
    
    # Mock the bot's selectOne method to return user data
    join_date = datetime.datetime.now() - datetime.timedelta(days=30)
    mock_bot.selectOne = MagicMock(return_value=("TestUser#1234", "Member", join_date))
    
    # Mock the bot's getNextMemLvlDate method to return a future date
    next_promotion_date = datetime.datetime.now() + datetime.timedelta(days=30)
    mock_bot.getNextMemLvlDate = MagicMock(return_value=next_promotion_date)
    
    # Mock the bot's getNextMemLvl method to return the next membership level
    mock_bot.getNextMemLvl = MagicMock(return_value="Senior Member")
    
    # Access the callback function directly
    callback = general_cog.promotion_when.callback
    
    # Call the callback function directly
    await callback(general_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called to get user data
    mock_bot.selectOne.assert_called_once()
    
    # Verify that getNextMemLvlDate was called with the correct arguments
    mock_bot.getNextMemLvlDate.assert_called_once_with("Member", join_date)
    
    # Verify that getNextMemLvl was called with the correct arguments
    mock_bot.getNextMemLvl.assert_called_once_with("Member")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you are eligible for promotion to **Senior Member** on **{next_promotion_date.strftime('%Y-%m-%d')}**."
    )

# Test the promotion_when command with a registered user who is already at max level
@pytest.mark.asyncio
async def test_promotion_when_max_level(mock_bot, mock_interaction):
    # Create a General cog with the mock bot
    general_cog = General(mock_bot)
    
    # Mock the bot's selectOne method to return user data
    join_date = datetime.datetime.now() - datetime.timedelta(days=365)
    mock_bot.selectOne = MagicMock(return_value=("TestUser#1234", "Senior Member", join_date))
    
    # Mock the bot's getNextMemLvlDate method to return None (max level)
    mock_bot.getNextMemLvlDate = MagicMock(return_value=None)
    
    # Access the callback function directly
    callback = general_cog.promotion_when.callback
    
    # Call the callback function directly
    await callback(general_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called to get user data
    mock_bot.selectOne.assert_called_once()
    
    # Verify that getNextMemLvlDate was called with the correct arguments
    mock_bot.getNextMemLvlDate.assert_called_once_with("Senior Member", join_date)
    
    # Verify that getNextMemLvl was not called
    assert not hasattr(mock_bot, 'getNextMemLvl') or not mock_bot.getNextMemLvl.called
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you are already eligible for all ranks."
    )

# Test the promotion_when command with an unregistered user
@pytest.mark.asyncio
async def test_promotion_when_unregistered(mock_bot, mock_interaction):
    # Create a General cog with the mock bot
    general_cog = General(mock_bot)
    
    # Mock the bot's selectOne method to return None (user not found)
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Access the callback function directly
    callback = general_cog.promotion_when.callback
    
    # Call the callback function directly
    await callback(general_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called to get user data
    mock_bot.selectOne.assert_called_once()
    
    # Verify that getNextMemLvlDate was not called
    assert not hasattr(mock_bot, 'getNextMemLvlDate') or not mock_bot.getNextMemLvlDate.called
    
    # Verify that getNextMemLvl was not called
    assert not hasattr(mock_bot, 'getNextMemLvl') or not mock_bot.getNextMemLvl.called
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you are not registered in our database.",
        ephemeral=True
    )

# Test the promotion_when command with a user who has a string join date
@pytest.mark.asyncio
async def test_promotion_when_string_join_date(mock_bot, mock_interaction):
    # Create a General cog with the mock bot
    general_cog = General(mock_bot)
    
    # Mock the bot's selectOne method to return user data with a string join date
    join_date_str = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    mock_bot.selectOne = MagicMock(return_value=("TestUser#1234", "Member", join_date_str))
    
    # Mock the bot's getNextMemLvlDate method to return a future date
    next_promotion_date = datetime.datetime.now() + datetime.timedelta(days=30)
    mock_bot.getNextMemLvlDate = MagicMock(return_value=next_promotion_date)
    
    # Mock the bot's getNextMemLvl method to return the next membership level
    mock_bot.getNextMemLvl = MagicMock(return_value="Senior Member")
    
    # Access the callback function directly
    callback = general_cog.promotion_when.callback
    
    # Call the callback function directly
    await callback(general_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that selectOne was called to get user data
    mock_bot.selectOne.assert_called_once()
    
    # Verify that getNextMemLvlDate was called with the correct arguments
    # The join_date should be converted from string to date object
    expected_join_date = datetime.datetime.strptime(join_date_str, "%Y-%m-%d").date()
    mock_bot.getNextMemLvlDate.assert_called_once_with("Member", expected_join_date)
    
    # Verify that getNextMemLvl was called with the correct arguments
    mock_bot.getNextMemLvl.assert_called_once_with("Member")
    
    # Verify that followup.send was called with the correct message
    mock_interaction.followup.send.assert_called_once_with(
        f"**{mock_interaction.user.name}** you are eligible for promotion to **Senior Member** on **{next_promotion_date.strftime('%Y-%m-%d')}**."
    ) 