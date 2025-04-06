import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import datetime
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Lotto cog
from cogs.lotto import Lotto

# Test the create_lottery command with valid parameters
@pytest.mark.asyncio
async def test_create_lottery_valid(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Mock the bot's selectOne method to return a lottery ID
    mock_bot.selectOne = MagicMock(return_value=(1,))
    
    # Access the callback function directly
    callback = lotto_cog.create_lottery.callback
    
    # Call the callback function directly with valid parameters
    future_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    await callback(lotto_cog, mock_interaction, future_date, 7, 1000, 5)
    
    # Verify that execute_query was called with the correct SQL
    mock_bot.execute_query.assert_called_once()
    
    # Verify that selectOne was called to get the lottery ID
    mock_bot.selectOne.assert_called_once()
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the first argument is an embed
    assert isinstance(call_args[1]['embed'], discord.Embed)
    embed = call_args[1]['embed']
    
    # Verify the embed properties
    assert embed.title == "🎟️ New Lottery Created!"
    assert embed.color == discord.Color.green()
    
    # Check that the fields contain the expected information
    field_names = [field.name for field in embed.fields]
    assert "Start Date" in field_names
    assert "End Date" in field_names
    assert "Entry Fee" in field_names
    assert "Max Entries" in field_names
    assert "Lottery ID" in field_names

# Test the create_lottery command with negative entry fee
@pytest.mark.asyncio
async def test_create_lottery_negative_entry_fee(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Access the callback function directly
    callback = lotto_cog.create_lottery.callback
    
    # Call the callback function directly with a negative entry fee
    future_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    await callback(lotto_cog, mock_interaction, future_date, 7, -100, 5)
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Entry fee cannot be negative.",
        ephemeral=True
    )
    
    # Verify that execute_query was not called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the create_lottery command with zero max entries
@pytest.mark.asyncio
async def test_create_lottery_zero_max_entries(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Access the callback function directly
    callback = lotto_cog.create_lottery.callback
    
    # Call the callback function directly with zero max entries
    future_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    await callback(lotto_cog, mock_interaction, future_date, 7, 1000, 0)
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Maximum entries must be greater than 0.",
        ephemeral=True
    )
    
    # Verify that execute_query was not called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the create_lottery command with past start date
@pytest.mark.asyncio
async def test_create_lottery_past_start_date(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Access the callback function directly
    callback = lotto_cog.create_lottery.callback
    
    # Call the callback function directly with a past start date
    past_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    await callback(lotto_cog, mock_interaction, past_date, 7, 1000, 5)
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Start date cannot be in the past.",
        ephemeral=True
    )
    
    # Verify that execute_query was not called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the create_lottery command with invalid date format
@pytest.mark.asyncio
async def test_create_lottery_invalid_date_format(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Access the callback function directly
    callback = lotto_cog.create_lottery.callback
    
    # Call the callback function directly with an invalid date format
    await callback(lotto_cog, mock_interaction, "invalid-date", 7, 1000, 5)
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Invalid date format. Please use YYYY-MM-DD HH:MM format (e.g. '2024-03-20 18:00')",
        ephemeral=True
    )
    
    # Verify that execute_query was not called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the create_lottery command with database error
@pytest.mark.asyncio
async def test_create_lottery_database_error(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's execute_query method to raise an exception
    mock_bot.execute_query = MagicMock(side_effect=Exception("Database error"))
    
    # Access the callback function directly
    callback = lotto_cog.create_lottery.callback
    
    # Call the callback function directly with valid parameters
    future_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    await callback(lotto_cog, mock_interaction, future_date, 7, 1000, 5)
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "An error occurred while creating the lottery: Database error",
        ephemeral=True
    )

# Test the select_winner command with valid lottery
@pytest.mark.asyncio
async def test_select_winner_valid(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return lottery details
    past_date = datetime.datetime.now() - datetime.timedelta(days=2)
    end_date = datetime.datetime.now() - datetime.timedelta(days=1)
    mock_bot.selectOne = MagicMock(side_effect=[
        (past_date, end_date, None),  # First call: lottery details
        ("TestUser", 123456789)       # Second call: winner details
    ])
    
    # Mock the bot's selectMany method to return entries
    mock_bot.selectMany = MagicMock(return_value=[
        (123456789, 3),  # discord_id, entries_purchased
        (987654321, 2)   # discord_id, entries_purchased
    ])
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Mock random.choice to return a predictable winner
    with patch('random.choice', return_value=123456789):
        # Access the callback function directly
        callback = lotto_cog.select_winner.callback
        
        # Call the callback function directly with a valid lottery ID
        await callback(lotto_cog, mock_interaction, 1)
        
        # Verify that selectOne was called to get lottery details
        mock_bot.selectOne.assert_called()
        
        # Verify that selectMany was called to get entries
        mock_bot.selectMany.assert_called_once()
        
        # Verify that execute_query was called to update the winner
        mock_bot.execute_query.assert_called_once()
        
        # Verify that response.send_message was called with an embed
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Check that the first argument is an embed
        assert isinstance(call_args[1]['embed'], discord.Embed)
        embed = call_args[1]['embed']
        
        # Verify the embed properties
        assert embed.title == "🎉 Lottery Winner Selected!"
        assert embed.color == discord.Color.gold()
        
        # Check that the fields contain the expected information
        field_names = [field.name for field in embed.fields]
        assert "Lottery ID" in field_names
        assert "Winner" in field_names
        assert "Entries/Total" in field_names

# Test the select_winner command with non-existent lottery
@pytest.mark.asyncio
async def test_select_winner_nonexistent(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return None (lottery not found)
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Access the callback function directly
    callback = lotto_cog.select_winner.callback
    
    # Call the callback function directly with a non-existent lottery ID
    await callback(lotto_cog, mock_interaction, 999)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Lottery with ID 999 not found.",
        ephemeral=True
    )
    
    # Verify that selectMany and execute_query were not called
    assert not hasattr(mock_bot, 'selectMany') or not mock_bot.selectMany.called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the select_winner command with ongoing lottery
@pytest.mark.asyncio
async def test_select_winner_ongoing(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return lottery details with future end date
    past_date = datetime.datetime.now() - datetime.timedelta(days=1)
    future_date = datetime.datetime.now() + datetime.timedelta(days=1)
    mock_bot.selectOne = MagicMock(return_value=(past_date, future_date, None))
    
    # Access the callback function directly
    callback = lotto_cog.select_winner.callback
    
    # Call the callback function directly with an ongoing lottery ID
    await callback(lotto_cog, mock_interaction, 1)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "This lottery is still ongoing. Cannot select a winner yet.",
        ephemeral=True
    )
    
    # Verify that selectMany and execute_query were not called
    assert not hasattr(mock_bot, 'selectMany') or not mock_bot.selectMany.called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the select_winner command with already selected winner
@pytest.mark.asyncio
async def test_select_winner_already_selected(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return lottery details with a winner
    past_date = datetime.datetime.now() - datetime.timedelta(days=2)
    end_date = datetime.datetime.now() - datetime.timedelta(days=1)
    mock_bot.selectOne = MagicMock(return_value=(past_date, end_date, 123456789))
    
    # Access the callback function directly
    callback = lotto_cog.select_winner.callback
    
    # Call the callback function directly with a lottery that already has a winner
    await callback(lotto_cog, mock_interaction, 1)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "A winner has already been selected for this lottery.",
        ephemeral=True
    )
    
    # Verify that selectMany and execute_query were not called
    assert not hasattr(mock_bot, 'selectMany') or not mock_bot.selectMany.called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the select_winner command with no entries
@pytest.mark.asyncio
async def test_select_winner_no_entries(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return lottery details
    past_date = datetime.datetime.now() - datetime.timedelta(days=2)
    end_date = datetime.datetime.now() - datetime.timedelta(days=1)
    mock_bot.selectOne = MagicMock(return_value=(past_date, end_date, None))
    
    # Mock the bot's selectMany method to return empty list (no entries)
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = lotto_cog.select_winner.callback
    
    # Call the callback function directly with a lottery that has no entries
    await callback(lotto_cog, mock_interaction, 1)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that selectMany was called to get entries
    mock_bot.selectMany.assert_called_once()
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "No entries found for this lottery.",
        ephemeral=True
    )
    
    # Verify that execute_query was not called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the lottery_status command with active lottery
@pytest.mark.asyncio
async def test_lottery_status_active(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return lottery details
    start_date = datetime.datetime.now() - datetime.timedelta(days=1)
    end_date = datetime.datetime.now() + datetime.timedelta(days=6)
    mock_bot.selectOne = MagicMock(return_value=(1, start_date, end_date, 1000, 5, None))
    
    # Mock the bot's selectMany method to return entries
    mock_bot.selectMany = MagicMock(return_value=[
        (123456789, 3, "User1"),  # discord_id, entries_purchased, rsn
        (987654321, 2, "User2")   # discord_id, entries_purchased, rsn
    ])
    
    # Access the callback function directly
    callback = lotto_cog.lottery_status.callback
    
    # Call the callback function directly
    await callback(lotto_cog, mock_interaction)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that selectMany was called to get entries
    mock_bot.selectMany.assert_called_once()
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the first argument is an embed
    assert isinstance(call_args[1]['embed'], discord.Embed)
    embed = call_args[1]['embed']
    
    # Verify the embed properties
    assert embed.title == "🎟️ Active Lottery #1"
    assert embed.color == discord.Color.blue()
    
    # Check that the fields contain the expected information
    field_names = [field.name for field in embed.fields]
    assert "Status" in field_names
    assert "Entry Fee" in field_names
    assert "Max Entries" in field_names
    assert "Total Entries" in field_names
    assert "Top Entries" in field_names

# Test the lottery_status command with no active lottery
@pytest.mark.asyncio
async def test_lottery_status_no_active(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return None (no active lottery)
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Access the callback function directly
    callback = lotto_cog.lottery_status.callback
    
    # Call the callback function directly
    await callback(lotto_cog, mock_interaction)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "There is currently no active lottery.",
        ephemeral=True
    )
    
    # Verify that selectMany was not called
    assert not hasattr(mock_bot, 'selectMany') or not mock_bot.selectMany.called

# Test the lottery_status command with active lottery but no entries
@pytest.mark.asyncio
async def test_lottery_status_no_entries(mock_bot, mock_interaction):
    # Create a Lotto cog with the mock bot
    lotto_cog = Lotto(mock_bot)
    
    # Mock the bot's selectOne method to return lottery details
    start_date = datetime.datetime.now() - datetime.timedelta(days=1)
    end_date = datetime.datetime.now() + datetime.timedelta(days=6)
    mock_bot.selectOne = MagicMock(return_value=(1, start_date, end_date, 1000, 5, None))
    
    # Mock the bot's selectMany method to return empty list (no entries)
    mock_bot.selectMany = MagicMock(return_value=[])
    
    # Access the callback function directly
    callback = lotto_cog.lottery_status.callback
    
    # Call the callback function directly
    await callback(lotto_cog, mock_interaction)
    
    # Verify that selectOne was called to get lottery details
    mock_bot.selectOne.assert_called_once()
    
    # Verify that selectMany was called to get entries
    mock_bot.selectMany.assert_called_once()
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the first argument is an embed
    assert isinstance(call_args[1]['embed'], discord.Embed)
    embed = call_args[1]['embed']
    
    # Verify the embed properties
    assert embed.title == "🎟️ Active Lottery #1"
    assert embed.color == discord.Color.blue()
    
    # Check that the fields contain the expected information
    field_names = [field.name for field in embed.fields]
    assert "Status" in field_names
    assert "Entry Fee" in field_names
    assert "Max Entries" in field_names
    assert "Total Entries" in field_names
    assert "Top Entries" in field_names
    
    # Check that the Total Entries field shows "0"
    total_entries_field = next(field for field in embed.fields if field.name == "Total Entries")
    assert total_entries_field.value == "0"
    
    # Check that the Top Entries field shows "No entries yet"
    top_entries_field = next(field for field in embed.fields if field.name == "Top Entries")
    assert top_entries_field.value == "No entries yet" 