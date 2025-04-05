import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import datetime
import sys
import os
import pandas as pd
import asyncio

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Dev cog
from cogs.dev import Dev

# Test the db_status command with admin permissions and successful connection
@pytest.mark.asyncio
async def test_db_status_admin_success(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the bot's check_database_connection method to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Mock the bot's selectOne method to return database version
    mock_bot.selectOne = MagicMock(return_value=("PostgreSQL 13.4",))
    
    # Mock the bot's getConfigValue method to return database config values
    mock_bot.getConfigValue = MagicMock(side_effect=lambda key: {
        "db_user": "testuser",
        "db_host": "testhost",
        "db_name": "testdb"
    }.get(key))
    
    # Create a mock embed that will be returned by followup.send
    mock_embed = discord.Embed(
        title="✅ Database Connection Status",
        description="The database connection is active and working properly.",
        color=discord.Color.green()
    )
    mock_embed.add_field(name="Database Version", value="PostgreSQL 13.4")
    mock_embed.add_field(name="Connection String", value="postgresql://testuser@testhost/testdb")
    
    # Mock the followup.send method to be an async mock that returns our mock embed
    mock_interaction.followup.send = AsyncMock(return_value=mock_embed)
    
    # Access the callback function directly
    callback = dev_cog.db_status.callback
    
    # Call the callback function directly
    await callback(dev_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that selectOne was called to get database version
    mock_bot.selectOne.assert_called_once_with("SELECT version()")
    
    # Verify that getConfigValue was called for each config value
    assert mock_bot.getConfigValue.call_count == 3
    
    # Verify that followup.send was called with an embed
    mock_interaction.followup.send.assert_called_once()
    
    # Get the arguments that were passed to followup.send
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the first argument is an embed
    print(f"call_args: {call_args[0]}")
    assert isinstance(call_args[0], discord.Embed)
    embed = call_args[0]
    
    # Verify the embed properties
    assert embed.title == "✅ Database Connection Status"
    assert embed.description == "The database connection is active and working properly."
    assert embed.color == discord.Color.green()
    
    # Check that the fields contain the expected information
    field_names = [field.name for field in embed.fields]
    assert "Database Version" in field_names
    assert "Connection String" in field_names

# Test the db_status command with admin permissions but failed connection
@pytest.mark.asyncio
async def test_db_status_admin_failure(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the bot's check_database_connection method to return False
    mock_bot.check_database_connection = MagicMock(return_value=False)
    
    # Access the callback function directly
    callback = dev_cog.db_status.callback
    
    # Call the callback function directly
    await callback(dev_cog, mock_interaction)
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that selectOne was not called
    assert not hasattr(mock_bot, 'selectOne') or not mock_bot.selectOne.called
    
    # Verify that followup.send was called with an error message
    mock_interaction.followup.send.assert_called_once_with(
        "❌ Database connection is not active. Check the logs for more information.",
        ephemeral=True
    )

# Test the db_status command with non-admin permissions
@pytest.mark.asyncio
async def test_db_status_non_admin(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to not have admin permissions
    mock_interaction.user.guild_permissions.administrator = False
    
    # Access the callback function directly
    callback = dev_cog.db_status.callback
    
    # Call the callback function directly
    await callback(dev_cog, mock_interaction)
    
    # Verify that the interaction was not deferred
    assert not mock_interaction.response.defer.called
    
    # Verify that check_database_connection was not called
    assert not hasattr(mock_bot, 'check_database_connection') or not mock_bot.check_database_connection.called
    
    # Verify that response.send_message was called with a permission error message
    mock_interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.",
        ephemeral=True
    )

# Test the reload_cog command with admin permissions and successful reload
@pytest.mark.asyncio
async def test_reload_cog_admin_success(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the bot's reload_extension method
    mock_bot.reload_extension = MagicMock()
    
    # Access the callback function directly
    callback = dev_cog.reload_cog.callback
    
    # Call the callback function directly with a cog name
    await callback(dev_cog, mock_interaction, "admin")
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that reload_extension was called with the correct cog name
    mock_bot.reload_extension.assert_called_once_with("cogs.admin")
    
    # Verify that followup.send was called with a success message
    mock_interaction.followup.send.assert_called_once_with(
        "✅ Successfully reloaded cog: **cogs.admin**"
    )

# Test the reload_cog command with admin permissions but failed reload
@pytest.mark.asyncio
async def test_reload_cog_admin_failure(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the bot's reload_extension method to raise an exception
    mock_bot.reload_extension = MagicMock(side_effect=Exception("Failed to reload"))
    
    # Access the callback function directly
    callback = dev_cog.reload_cog.callback
    
    # Call the callback function directly with a cog name
    await callback(dev_cog, mock_interaction, "admin")
    
    # Verify that the interaction was deferred
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that reload_extension was called with the correct cog name
    mock_bot.reload_extension.assert_called_once_with("cogs.admin")
    
    # Verify that followup.send was called with an error message
    mock_interaction.followup.send.assert_called_once_with(
        "❌ Failed to reload cog **cogs.admin**: Failed to reload",
        ephemeral=True
    )

# Test the reload_cog command with non-admin permissions
@pytest.mark.asyncio
async def test_reload_cog_non_admin(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to not have admin permissions
    mock_interaction.user.guild_permissions.administrator = False
    
    # Access the callback function directly
    callback = dev_cog.reload_cog.callback
    
    # Call the callback function directly with a cog name
    await callback(dev_cog, mock_interaction, "admin")
    
    # Verify that the interaction was not deferred
    assert not mock_interaction.response.defer.called
    
    # Verify that reload_extension was not called
    assert not hasattr(mock_bot, 'reload_extension') or not mock_bot.reload_extension.called
    
    # Verify that response.send_message was called with a permission error message
    mock_interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.",
        ephemeral=True
    )

# Test the format_sql_array method with a comma-separated string
def test_format_sql_array_comma_separated():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Test with a comma-separated string
    result = dev_cog.format_sql_array("value1, value2, value3")
    
    # Verify the result is a PostgreSQL array
    assert result == "ARRAY['value1', 'value2', 'value3']"

# Test the format_sql_array method with a list
def test_format_sql_array_list():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Test with a list
    result = dev_cog.format_sql_array(["value1", "value2", "value3"])
    
    # Verify the result is a PostgreSQL array
    assert result == "ARRAY['value1', 'value2', 'value3']"

# Test the format_sql_array method with an empty string
def test_format_sql_array_empty_string():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Test with an empty string
    result = dev_cog.format_sql_array("")
    
    # Verify the result is NULL
    assert result == "NULL"

# Test the format_sql_array method with an empty list
def test_format_sql_array_empty_list():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Test with an empty list
    result = dev_cog.format_sql_array([])
    
    # Verify the result is NULL
    assert result == "NULL"

# Test the format_sql_array method with None
def test_format_sql_array_none():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Test with None
    result = dev_cog.format_sql_array(None)
    
    # Verify the result is NULL
    assert result == "NULL"

# Test the format_sql_array method with a string containing single quotes
def test_format_sql_array_with_quotes():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Test with a string containing single quotes
    result = dev_cog.format_sql_array("value1, O'Neil, value3")
    
    # Verify the result is a PostgreSQL array with escaped quotes
    assert result == "ARRAY['value1', 'O''Neil', 'value3']"

# Test the load_member_data command with admin permissions and successful data load
@pytest.mark.asyncio
async def test_load_member_data_admin_success(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the os.path.exists method to return True for credentials file
    with patch('os.path.exists', return_value=True):
        # Create a proper mock chain for the Google Sheets service
        mock_values = MagicMock()
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            'values': [
                ['RSN', 'Discord', 'Active', 'Level', 'Previous', 'Alt', 'Discord ID', 'Join Date'],
                ['User1', 'Yes', 'Yes', 'Member', 'OldUser1', 'Alt1', '123456789', '01/01/2023'],
                ['User2', 'Yes', 'Yes', 'Senior Member', 'OldUser2', 'Alt2', '987654321', '02/02/2023']
            ]
        }
        mock_values.get.return_value = mock_get
        
        mock_spreadsheets = MagicMock()
        mock_spreadsheets.values.return_value = mock_values
        
        mock_service = MagicMock()
        mock_service.spreadsheets.return_value = mock_spreadsheets
        
        # Mock the get_google_sheets_service method
        dev_cog.get_google_sheets_service = MagicMock(return_value=mock_service)
        
        # Mock the followup.send method to return a message that we can edit
        mock_message = MagicMock()
        mock_interaction.followup.send.return_value = mock_message
        
        # Mock the wait_for method to simulate a button click
        mock_button_interaction = MagicMock()
        mock_button_interaction.data = {'custom_id': 'confirm_insert'}
        mock_button_interaction.response.defer = AsyncMock()
        mock_button_interaction.followup.send = AsyncMock()
        
        # Mock the bot's wait_for method with the exact parameters used in the implementation
        async def mock_wait_for(event_type, check=None, timeout=None):
            # Verify the parameters
            assert event_type == "interaction"
            assert timeout == 60.0
            # Return the mock button interaction
            return mock_button_interaction
            
        mock_bot.wait_for = mock_wait_for
        
        # Mock the bot's getConfigValue method to return membership levels
        mock_bot.getConfigValue = MagicMock(return_value=["Member", "Senior Member", "Admin"])
        
        # Mock the bot's selectOne method to return None (member not found)
        mock_bot.selectOne = MagicMock(return_value=None)
        
        # Mock the bot's execute_query method
        mock_bot.execute_query = MagicMock()
        
        # Mock the format_sql_array method to return a simple array string
        dev_cog.format_sql_array = MagicMock(return_value="ARRAY['test']")
        
        # Access the callback function directly
        callback = dev_cog.load_member_data.callback
        
        # Call the callback function directly with sheet parameters
        await callback(dev_cog, mock_interaction, "sheet_id", "Sheet1", "A1:H10")
        
        # Verify that the interaction was deferred
        mock_interaction.response.defer.assert_called_once()
        
        # Verify that get_google_sheets_service was called
        dev_cog.get_google_sheets_service.assert_called_once()
        
        # Verify that the Google Sheets API was called with the correct parameters
        mock_values.get.assert_called_once_with(
            spreadsheetId="sheet_id",
            range="Sheet1!A1:H10"
        )
        
        # Verify that followup.send was called with an embed
        mock_interaction.followup.send.assert_called()
        
        # Verify that wait_for was called to wait for button interaction
        # We can't use assert_called_once() because we're using a custom function
        # Instead, we'll check that execute_query was called, which happens after wait_for
        
        # Verify that execute_query was called to insert the data
        assert mock_bot.execute_query.call_count == 2  # One for each row
        
        # Verify that the final followup.send was called with a summary embed
        mock_button_interaction.followup.send.assert_called_once()
        call_args = mock_button_interaction.followup.send.call_args
        
        # Check that the first argument is an embed
        assert isinstance(call_args[1]['embed'], discord.Embed)
        embed = call_args[1]['embed']
        
        # Verify the embed properties
        assert embed.title == "✅ Database Update Complete"
        assert embed.description == "Successfully processed data from Google Sheet."
        assert embed.color == discord.Color.green()
        
        # Check that the fields contain the expected information
        field_names = [field.name for field in embed.fields]
        assert "Inserted" in field_names
        assert "Updated" in field_names
        assert "Skipped" in field_names
        assert "Errors" in field_names

# Test the load_member_data command with admin permissions but no credentials file
@pytest.mark.asyncio
async def test_load_member_data_admin_no_credentials(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the os.path.exists method to return False for credentials file
    with patch('os.path.exists', return_value=False):
        # Mock the get_google_sheets_service method
        dev_cog.get_google_sheets_service = MagicMock()
        
        # Access the callback function directly
        callback = dev_cog.load_member_data.callback
        
        # Call the callback function directly with sheet parameters
        await callback(dev_cog, mock_interaction, "sheet_id", "Sheet1", "A1:H10")
        
        # Verify that the interaction was deferred
        mock_interaction.response.defer.assert_called_once()
        
        # Verify that get_google_sheets_service was not called
        assert not dev_cog.get_google_sheets_service.called
        
        # Verify that followup.send was called with an error message
        mock_interaction.followup.send.assert_called_once_with(
            "❌ Google Sheets credentials file not found. Please place 'credentials.json' in the bot's root directory.",
            ephemeral=True
        )

# Test the load_member_data command with admin permissions but failed authentication
@pytest.mark.asyncio
async def test_load_member_data_admin_auth_failure(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to have admin permissions
    mock_interaction.user.guild_permissions.administrator = True
    
    # Mock the os.path.exists method to return True for credentials file
    with patch('os.path.exists', return_value=True):
        # Mock the get_google_sheets_service method to return None (auth failure)
        dev_cog.get_google_sheets_service = MagicMock(return_value=None)
        
        # Access the callback function directly
        callback = dev_cog.load_member_data.callback
        
        # Call the callback function directly with sheet parameters
        await callback(dev_cog, mock_interaction, "sheet_id", "Sheet1", "A1:H10")
        
        # Verify that the interaction was deferred
        mock_interaction.response.defer.assert_called_once()
        
        # Verify that get_google_sheets_service was called
        dev_cog.get_google_sheets_service.assert_called_once()
        
        # Verify that followup.send was called with an error message
        mock_interaction.followup.send.assert_called_once_with(
            "❌ Failed to authenticate with Google Sheets API. Check the logs for details.",
            ephemeral=True
        )

# Test the load_member_data command with non-admin permissions
@pytest.mark.asyncio
async def test_load_member_data_non_admin(mock_bot, mock_interaction):
    # Create a Dev cog with the mock bot
    dev_cog = Dev(mock_bot)
    
    # Mock the interaction user to not have admin permissions
    mock_interaction.user.guild_permissions.administrator = False
    
    # Mock the get_google_sheets_service method
    dev_cog.get_google_sheets_service = MagicMock()
    
    # Access the callback function directly
    callback = dev_cog.load_member_data.callback
    
    # Call the callback function directly with sheet parameters
    await callback(dev_cog, mock_interaction, "sheet_id", "Sheet1", "A1:H10")
    
    # Verify that the interaction was not deferred
    assert not mock_interaction.response.defer.called
    
    # Verify that get_google_sheets_service was not called
    assert not dev_cog.get_google_sheets_service.called
    
    # Verify that response.send_message was called with a permission error message
    mock_interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.",
        ephemeral=True
    )

# Test the get_google_sheets_service method with existing token
@pytest.mark.asyncio
async def test_get_google_sheets_service_existing_token():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Mock the os.path.exists method to return True for token file
    with patch('os.path.exists', return_value=True):
        # Mock the Credentials.from_authorized_user_file method
        mock_creds = MagicMock()
        mock_creds.valid = True
        
        with patch('google.oauth2.credentials.Credentials.from_authorized_user_file', return_value=mock_creds):
            # Mock the build method
            mock_service = MagicMock()
            with patch('googleapiclient.discovery.build', return_value=mock_service):
                # Call the method
                result = dev_cog.get_google_sheets_service()
                
                # Verify the result is the mock service
                assert result == mock_service

# Test the get_google_sheets_service method with expired token
@pytest.mark.asyncio
async def test_get_google_sheets_service_expired_token():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Mock the os.path.exists method to return True for token file
    with patch('os.path.exists', return_value=True):
        # Mock the Credentials.from_authorized_user_file method
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = True
        
        with patch('google.oauth2.credentials.Credentials.from_authorized_user_file', return_value=mock_creds):
            # Mock the Request class
            mock_request = MagicMock()
            with patch('google.auth.transport.requests.Request', return_value=mock_request):
                # Mock the refresh method
                mock_creds.refresh = MagicMock()
                
                # Mock the build method
                mock_service = MagicMock()
                with patch('googleapiclient.discovery.build', return_value=mock_service):
                    # Call the method
                    result = dev_cog.get_google_sheets_service()
                    
                    # Verify that refresh was called with the mock request
                    mock_creds.refresh.assert_called_once_with(mock_request)
                    
                    # Verify the result is the mock service
                    assert result == mock_service

# Test the get_google_sheets_service method with no token
@pytest.mark.asyncio
async def test_get_google_sheets_service_no_token():
    # Create a Dev cog with a mock bot
    dev_cog = Dev(MagicMock())
    
    # Mock the os.path.exists method to return False for token file
    with patch('os.path.exists', return_value=False):
        # Mock the InstalledAppFlow.from_client_secrets_file method
        mock_flow = MagicMock()
        mock_flow.run_local_server = MagicMock(return_value=MagicMock())
        
        with patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file', return_value=mock_flow):
            # Mock the build method
            mock_service = MagicMock()
            with patch('googleapiclient.discovery.build', return_value=mock_service):
                # Call the method
                result = dev_cog.get_google_sheets_service()
                
                # Verify that run_local_server was called
                mock_flow.run_local_server.assert_called_once_with(port=0)
                
                # Verify the result is the mock service
                assert result == mock_service 