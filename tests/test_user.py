import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the User cog
from cogs.user import User, ProfileField

# Test the update_profile command with LOC field - valid input
@pytest.mark.asyncio
async def test_update_profile_loc_valid(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Mock the bot's selectOne method to return user data (user exists)
    mock_bot.selectOne = MagicMock(return_value=("user_id",))
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with LOC field
    await callback(user_cog, mock_interaction, ProfileField.LOC, "us")
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"""
                SELECT _id FROM member
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that execute_query was called with the correct query
    mock_bot.execute_query.assert_called_once_with(f"""
                UPDATE member
                SET {ProfileField.LOC.value} = 'US'
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the message is ephemeral
    assert call_args[1]["ephemeral"] is True
    
    # Check that an embed was sent
    assert "embed" in call_args[1]
    embed = call_args[1]["embed"]
    
    # Check the embed properties
    assert embed.title == "Profile Updated"
    assert embed.color == discord.Color.green()
    
    # Check that the embed has the correct field
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "Loc"
    assert embed.fields[0].value == "US"
    assert embed.fields[0].inline is True

# Test the update_profile command with LOC field - invalid input (not 2 letters)
@pytest.mark.asyncio
async def test_update_profile_loc_invalid_length(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with LOC field
    await callback(user_cog, mock_interaction, ProfileField.LOC, "usa")
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Location must be a 2-letter country code (e.g. US, UK, CA)",
        ephemeral=True
    )
    
    # Verify that selectOne and execute_query were not called
    mock_bot.selectOne.assert_not_called()
    mock_bot.execute_query.assert_not_called()

# Test the update_profile command with ALT_RSN field - valid input
@pytest.mark.asyncio
async def test_update_profile_alt_rsn_valid(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Mock the bot's selectOne method to return user data (user exists)
    mock_bot.selectOne = MagicMock(return_value=("user_id",))
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with ALT_RSN field
    await callback(user_cog, mock_interaction, ProfileField.ALT_RSN, "Alt1, Alt2, Alt3")
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"""
                SELECT _id FROM member
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that execute_query was called with the correct query
    mock_bot.execute_query.assert_called_once()
    call_args = mock_bot.execute_query.call_args
    
    # Check that the query contains the correct field and values
    assert ProfileField.ALT_RSN.value in call_args[0][0]
    assert "Alt1" in call_args[0][0]
    assert "Alt2" in call_args[0][0]
    assert "Alt3" in call_args[0][0]
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the message is ephemeral
    assert call_args[1]["ephemeral"] is True
    
    # Check that an embed was sent
    assert "embed" in call_args[1]
    embed = call_args[1]["embed"]
    
    # Check the embed properties
    assert embed.title == "Profile Updated"
    assert embed.color == discord.Color.green()
    
    # Check that the embed has the correct field
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "Alt Rsn"
    assert embed.fields[0].value == "Alt1, Alt2, Alt3"
    assert embed.fields[0].inline is True

# Test the update_profile command with ALT_RSN field - invalid input (too long)
@pytest.mark.asyncio
async def test_update_profile_alt_rsn_invalid_length(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with ALT_RSN field
    await callback(user_cog, mock_interaction, ProfileField.ALT_RSN, "ThisNameIsTooLong, Alt2")
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Alternate RSNs cannot be longer than 12 characters",
        ephemeral=True
    )
    
    # Verify that selectOne and execute_query were not called
    mock_bot.selectOne.assert_not_called()
    mock_bot.execute_query.assert_not_called()

# Test the update_profile command with PREVIOUS_RSN field - valid input
@pytest.mark.asyncio
async def test_update_profile_previous_rsn_valid(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Mock the bot's selectOne method to return user data (user exists)
    mock_bot.selectOne = MagicMock(return_value=("user_id",))
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with PREVIOUS_RSN field
    await callback(user_cog, mock_interaction, ProfileField.PREVIOUS_RSN, "OldName")
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"""
                SELECT _id FROM member
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that execute_query was called with the correct query
    mock_bot.execute_query.assert_called_once_with(f"""
                UPDATE member
                SET {ProfileField.PREVIOUS_RSN.value} = 'OldName'
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the message is ephemeral
    assert call_args[1]["ephemeral"] is True
    
    # Check that an embed was sent
    assert "embed" in call_args[1]
    embed = call_args[1]["embed"]
    
    # Check the embed properties
    assert embed.title == "Profile Updated"
    assert embed.color == discord.Color.green()
    
    # Check that the embed has the correct field
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "Previous Rsn"
    assert embed.fields[0].value == "OldName"
    assert embed.fields[0].inline is True

# Test the update_profile command with PREVIOUS_RSN field - invalid input (too long)
@pytest.mark.asyncio
async def test_update_profile_previous_rsn_invalid_length(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with PREVIOUS_RSN field
    await callback(user_cog, mock_interaction, ProfileField.PREVIOUS_RSN, "ThisNameIsTooLong")
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "Previous RSN cannot be longer than 12 characters",
        ephemeral=True
    )
    
    # Verify that selectOne and execute_query were not called
    mock_bot.selectOne.assert_not_called()
    mock_bot.execute_query.assert_not_called()

# Test the update_profile command with TIMEZONE field - valid input
@pytest.mark.asyncio
async def test_update_profile_timezone_valid(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Mock the bot's selectOne method to return user data (user exists)
    mock_bot.selectOne = MagicMock(return_value=("user_id",))
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with TIMEZONE field
    await callback(user_cog, mock_interaction, ProfileField.TIMEZONE, "est")
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"""
                SELECT _id FROM member
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that execute_query was called with the correct query
    mock_bot.execute_query.assert_called_once_with(f"""
                UPDATE member
                SET {ProfileField.TIMEZONE.value} = 'EST'
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that response.send_message was called with an embed
    mock_interaction.response.send_message.assert_called_once()
    call_args = mock_interaction.response.send_message.call_args
    
    # Check that the message is ephemeral
    assert call_args[1]["ephemeral"] is True
    
    # Check that an embed was sent
    assert "embed" in call_args[1]
    embed = call_args[1]["embed"]
    
    # Check the embed properties
    assert embed.title == "Profile Updated"
    assert embed.color == discord.Color.green()
    
    # Check that the embed has the correct field
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "Timezone"
    assert embed.fields[0].value == "EST"
    assert embed.fields[0].inline is True

# Test the update_profile command with user not in database
@pytest.mark.asyncio
async def test_update_profile_user_not_found(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Mock the bot's selectOne method to return None (user not found)
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with any field
    await callback(user_cog, mock_interaction, ProfileField.LOC, "us")
    
    # Verify that selectOne was called with the correct query
    mock_bot.selectOne.assert_called_once_with(f"""
                SELECT _id FROM member
                WHERE discord_id_num = {mock_interaction.user.id}
            """)
    
    # Verify that execute_query was not called
    mock_bot.execute_query.assert_not_called()
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "You are not registered in the member database. Please contact an admin.",
        ephemeral=True
    )

# Test the update_profile command with an exception
@pytest.mark.asyncio
async def test_update_profile_exception(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    user_cog = User(mock_bot)
    
    # Mock the bot's selectOne method to raise an exception
    mock_bot.selectOne = MagicMock(side_effect=Exception("Database error"))
    
    # Access the callback function directly
    callback = user_cog.update_profile.callback
    
    # Call the callback function directly with any field
    await callback(user_cog, mock_interaction, ProfileField.LOC, "us")
    
    # Verify that response.send_message was called with an error message
    mock_interaction.response.send_message.assert_called_once_with(
        "An error occurred while updating your profile: Database error",
        ephemeral=True
    ) 