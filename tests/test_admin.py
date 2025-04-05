import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import datetime
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Admin cog
from cogs.admin import Admin

# Mock the bot class
class MockBot:
    def __init__(self):
        self.config = {
            "mem_level_names": ["Newbie", "Member", "Veteran", "Elite"]
        }
    
    def selectOne(self, query):
        # Return a mock member record
        return (
            1,  # _id
            "TestUser",  # rsn
            None,  # discord_id_num
            "123456789",  # discord_id
            1,  # membership_level
            datetime.datetime.now().date(),  # join_date
            None,  # special_status
            ["OldRSN1", "OldRSN2"],  # previous_rsn
            ["Alt1", "Alt2"],  # alt_rsn
            True,  # on_leave
            True,  # active
            100,  # skill_comp_points
            50,  # skill_comp_pts_life
            "US",  # loc
            "EST",  # timezone
            "Some notes"  # notes
        )
    
    def getConfigValue(self, key):
        return self.config.get(key)
    
    def getNextMemLvlDate(self, mem_lvl, join_date):
        # Return a mock next promotion date
        return datetime.datetime.now().date() + datetime.timedelta(days=30)

# Create a mock interaction class
class MockInteraction:
    def __init__(self, is_admin=True):
        self.user = MagicMock()
        self.user.guild_permissions = MagicMock()
        self.user.guild_permissions.administrator = is_admin
        self.user.name = "TestUser"
        self.user.display_avatar = MagicMock()
        self.user.display_avatar.url = "https://example.com/avatar.png"
        self.response = AsyncMock()
        self.followup = AsyncMock()

# Test the view_member command
@pytest.mark.asyncio
async def test_view_member_admin(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the followup.send method to return a value
    mock_interaction.followup.send = AsyncMock(return_value=None)
    
    # Access the callback function directly instead of the command object
    callback = admin_cog.view_member.callback
    
    # Call the callback function directly
    await callback(admin_cog, mock_interaction, "TestUser")
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that followup.send was called with an embed
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the first argument is an embed
    assert isinstance(call_args[1]['embed'], discord.Embed)
    embed = call_args[1]['embed']
    
    # Verify the embed properties
    assert embed.title == "Member Information: TestUser"
    assert embed.color == discord.Color.blue()
    
    # Check that the footer contains the user's name
    assert "TestUser" in embed.footer.text
    
    # Check that the fields contain the expected information
    field_names = [field.name for field in embed.fields]
    assert "RSN" in field_names
    assert "Discord ID" in field_names
    assert "Membership Level" in field_names
    assert "Next Promotion Date" in field_names
    assert "Skill Comp Points" in field_names
    assert "On Leave" in field_names
    assert "Active" in field_names
    assert "Alt RSNs" in field_names
    assert "Previous RSNs" in field_names
    assert "Other Notes" in field_names

# Test the view_member command with non-admin user
@pytest.mark.asyncio
async def test_view_member_non_admin(mock_bot):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Create a mock interaction without admin permissions
    interaction = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.view_member.callback
    
    # Call the callback function directly
    await callback(admin_cog, interaction, "TestUser")
    
    # Verify that the user was told they don't have permission
    interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.", 
        ephemeral=True
    )
    
    # Verify that defer was not called
    interaction.response.defer.assert_not_called()

# Test the view_member command with non-existent user
@pytest.mark.asyncio
async def test_view_member_not_found(mock_bot, mock_interaction):
    # Modify the mock bot to return None for selectOne
    mock_bot.selectOne = MagicMock(return_value=None)
    
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Access the callback function directly
    callback = admin_cog.view_member.callback
    
    # Call the callback function directly
    await callback(admin_cog, mock_interaction, "NonExistentUser")
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that followup.send was called with the not found message
    mock_interaction.followup.send.assert_called_once_with(
        "No members found with rsn or alt of NonExistentUser"
    )

# Test the view_member command with different data types for alt_rsn and prev_rsn
@pytest.mark.asyncio
async def test_view_member_different_data_types(mock_bot, mock_interaction):
    # Create a mock bot with different data types for alt_rsn and prev_rsn
    mock_bot.selectOne = MagicMock(return_value=(
        1,  # _id
        "TestUser",  # rsn
        None,  # discord_id_num
        "123456789",  # discord_id
        1,  # membership_level
        datetime.datetime.now().date(),  # join_date
        None,  # special_status
        None,  # previous_rsn - test with None
        None,  # alt_rsn - test with None
        True,  # on_leave
        True,  # active
        100,  # skill_comp_points
        50,  # skill_comp_pts_life
        "US",  # loc
        "EST",  # timezone
        "Some notes"  # notes
    ))
    
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the followup.send method to return a value
    mock_interaction.followup.send = AsyncMock(return_value=None)
    
    # Access the callback function directly
    callback = admin_cog.view_member.callback
    
    # Call the callback function directly
    await callback(admin_cog, mock_interaction, "TestUser")
    
    # Verify that followup.send was called with an embed
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    
    # Check that the first argument is an embed
    assert isinstance(call_args[1]['embed'], discord.Embed)
    embed = call_args[1]['embed']
    
    # Check that the fields contain the expected information
    field_names = [field.name for field in embed.fields]
    assert "Alt RSNs" in field_names
    assert "Previous RSNs" in field_names
    
    # Find the Alt RSNs and Previous RSNs fields
    alt_rsn_field = next(field for field in embed.fields if field.name == "Alt RSNs")
    prev_rsn_field = next(field for field in embed.fields if field.name == "Previous RSNs")
    
    # Check that the values are "None"
    assert alt_rsn_field.value == "None"
    assert prev_rsn_field.value == "None"

# Test the shutdown command with admin user
@pytest.mark.asyncio
async def test_shutdown_admin(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the bot's close method
    mock_bot.close = AsyncMock()
    
    # Mock the database connection close method
    mock_bot.conn = MagicMock()
    mock_bot.conn.close = MagicMock()
    
    # Mock sys.exit to prevent the test from actually exiting
    with patch('sys.exit') as mock_exit:
        # Access the callback function directly
        callback = admin_cog.shutdown.callback
        
        # Call the callback function directly
        await callback(admin_cog, mock_interaction)
        
        # Verify that the user was told the bot is shutting down
        mock_interaction.response.send_message.assert_called_once_with('**Shutting Down...**')
        
        # Verify that the database connection was closed
        mock_bot.conn.close.assert_called_once()
        
        # Verify that the bot was closed
        mock_bot.close.assert_called_once()
        
        # Verify that sys.exit was called with 0
        mock_exit.assert_called_once_with(0)

# Test the shutdown command with non-admin user
@pytest.mark.asyncio
async def test_shutdown_non_admin(mock_bot):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Create a mock interaction without admin permissions
    interaction = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.shutdown.callback
    
    # Call the callback function directly
    await callback(admin_cog, interaction)
    
    # Verify that the user was told they don't have permission
    interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.", 
        ephemeral=True
    )
    
    # Verify that the database connection was not closed
    assert not hasattr(mock_bot, 'conn') or not mock_bot.conn.close.called
    
    # Verify that the bot was not closed
    assert not hasattr(mock_bot, 'close') or not mock_bot.close.called

# Test the update_member command with admin user
@pytest.mark.asyncio
async def test_update_member_admin(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Mock the bot's getConfigValue method for datetime_fmt
    mock_bot.getConfigValue = MagicMock(return_value="%Y-%m-%d")
    
    # Access the callback function directly
    callback = admin_cog.update_member.callback
    
    # Call the callback function directly
    await callback(admin_cog, mock_interaction, "TestUser", "active", "true")
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that execute_query was called with the correct SQL
    mock_bot.execute_query.assert_called_once_with(
        "UPDATE member SET active=true WHERE rsn ILIKE 'TestUser'"
    )
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once_with(
        "Updated user TestUser. Key active set to value true."
    )

# Test the update_member command with non-admin user
@pytest.mark.asyncio
async def test_update_member_non_admin(mock_bot):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Create a mock interaction without admin permissions
    interaction = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.update_member.callback
    
    # Call the callback function directly
    await callback(admin_cog, interaction, "TestUser", "active", "true")
    
    # Verify that the user was told they don't have permission
    interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.", 
        ephemeral=True
    )
    
    # Verify that defer was not called
    interaction.response.defer.assert_not_called()
    
    # Verify that execute_query was not called
    assert not hasattr(mock_bot, 'execute_query') or not mock_bot.execute_query.called

# Test the update_member command with join_date field
@pytest.mark.asyncio
async def test_update_member_join_date(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the bot's execute_query method
    mock_bot.execute_query = MagicMock()
    
    # Mock the bot's getConfigValue method for datetime_fmt
    mock_bot.getConfigValue = MagicMock(return_value="%Y-%m-%d")
    
    # Access the callback function directly
    callback = admin_cog.update_member.callback
    
    # Call the callback function directly with a join_date
    await callback(admin_cog, mock_interaction, "TestUser", "join_date", "2023-01-01")
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that getConfigValue was called with "datetime_fmt"
    mock_bot.getConfigValue.assert_called_once_with("datetime_fmt")
    
    # Verify that execute_query was called with the correct SQL
    # Note: We can't directly check the value of the datetime object in the SQL string
    # So we just check that execute_query was called
    mock_bot.execute_query.assert_called_once()
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once()
    assert "Updated user TestUser" in mock_interaction.followup.send.call_args[0][0]
    assert "Key join_date" in mock_interaction.followup.send.call_args[0][0]

# Test the set_active command with admin user
@pytest.mark.asyncio
async def test_set_active_admin(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the update_member method to avoid testing its implementation
    admin_cog.update_member = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.set_active.callback
    
    # Call the callback function directly
    await callback(admin_cog, mock_interaction, "TestUser", True)
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that update_member was called with the correct arguments
    admin_cog.update_member.assert_called_once_with(mock_interaction, "TestUser", "active", True)
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once_with(
        "TestUser inactive flag set to True"
    )

# Test the set_active command with non-admin user
@pytest.mark.asyncio
async def test_set_active_non_admin(mock_bot):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Create a mock interaction without admin permissions
    interaction = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response = AsyncMock()
    
    # Mock the update_member method to track if it's called
    admin_cog.update_member = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.set_active.callback
    
    # Call the callback function directly
    await callback(admin_cog, interaction, "TestUser", True)
    
    # Verify that the user was told they don't have permission
    interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.", 
        ephemeral=True
    )
    
    # Verify that defer was not called
    interaction.response.defer.assert_not_called()
    
    # Verify that update_member was not called
    admin_cog.update_member.assert_not_called()

# Test the set_active command with False value
@pytest.mark.asyncio
async def test_set_active_false(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the update_member method to avoid testing its implementation
    admin_cog.update_member = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.set_active.callback
    
    # Call the callback function directly with False
    await callback(admin_cog, mock_interaction, "TestUser", False)
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that update_member was called with the correct arguments
    admin_cog.update_member.assert_called_once_with(mock_interaction, "TestUser", "active", False)
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once_with(
        "TestUser inactive flag set to False"
    )

# Test the set_onleave command with admin user
@pytest.mark.asyncio
async def test_set_onleave_admin(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the update_member method to avoid testing its implementation
    admin_cog.update_member = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.set_onleave.callback
    
    # Call the callback function directly
    await callback(admin_cog, mock_interaction, "TestUser", True)
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that update_member was called with the correct arguments
    admin_cog.update_member.assert_called_once_with(mock_interaction, "TestUser", "on_leave", True)
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once_with(
        "TestUser on_leave flag set to True"
    )

# Test the set_onleave command with non-admin user
@pytest.mark.asyncio
async def test_set_onleave_non_admin(mock_bot):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Create a mock interaction without admin permissions
    interaction = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response = AsyncMock()
    
    # Mock the update_member method to track if it's called
    admin_cog.update_member = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.set_onleave.callback
    
    # Call the callback function directly
    await callback(admin_cog, interaction, "TestUser", True)
    
    # Verify that the user was told they don't have permission
    interaction.response.send_message.assert_called_once_with(
        "You don't have permission to use this command.", 
        ephemeral=True
    )
    
    # Verify that defer was not called
    interaction.response.defer.assert_not_called()
    
    # Verify that update_member was not called
    admin_cog.update_member.assert_not_called()

# Test the set_onleave command with False value
@pytest.mark.asyncio
async def test_set_onleave_false(mock_bot, mock_interaction):
    # Create an admin cog with the mock bot
    admin_cog = Admin(mock_bot)
    
    # Mock the update_member method to avoid testing its implementation
    admin_cog.update_member = AsyncMock()
    
    # Access the callback function directly
    callback = admin_cog.set_onleave.callback
    
    # Call the callback function directly with False
    await callback(admin_cog, mock_interaction, "TestUser", False)
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that update_member was called with the correct arguments
    admin_cog.update_member.assert_called_once_with(mock_interaction, "TestUser", "on_leave", False)
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once_with(
        "TestUser on_leave flag set to False"
    )

if __name__ == "__main__":
    pytest.main([__file__]) 