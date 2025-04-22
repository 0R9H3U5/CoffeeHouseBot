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
        # Return a mock member record with the correct column names and order
        # based on the member table definition in sql/create-db.sql
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
            100,  # skill_comp_pts
            50,  # skill_comp_pts_life
            50,  # boss_comp_pts
            25,  # boss_comp_pts_life
            "US",  # loc
            "EST",  # timezone
            "Some notes"  # notes
        )
    
    def selectMany(self, query):
        # Return column names for the member table based on sql/create-db.sql
        if "information_schema.columns" in query:
            # Return column names in the format expected by the Admin cog
            # The Admin cog expects a list of tuples where each tuple has a single string element
            return [
                ("_id",),
                ("rsn",),
                ("discord_id_num",),
                ("discord_id",),
                ("membership_level",),
                ("join_date",),
                ("special_status",),
                ("previous_rsn",),
                ("alt_rsn",),
                ("on_leave",),
                ("active",),
                ("skill_comp_pts",),
                ("skill_comp_pts_life",),
                ("boss_comp_pts",),
                ("boss_comp_pts_life",),
                ("loc",),
                ("timezone",),
                ("notes",)
            ]
        return []
    
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

# Test the set_onleave command in User cog
@pytest.mark.asyncio
async def test_set_onleave_admin(mock_bot, mock_interaction):
    # Create a User cog with the mock bot
    from cogs.user import User
    user_cog = User(mock_bot)
    
    # Mock the execute_query method
    mock_bot.execute_query = MagicMock(return_value=True)
    
    # Access the callback function directly
    callback = user_cog.set_onleave.callback
    
    # Call the callback function directly
    await callback(user_cog, mock_interaction, "TestUser", True)
    
    # Verify that defer was called
    mock_interaction.response.defer.assert_called_once()
    
    # Verify that followup.send was called with the success message
    mock_interaction.followup.send.assert_called_once_with(
        'Updated user TestUser. Key on_leave set to value true.'
        )

# Test the shutdown command in Admin cog
@pytest.mark.asyncio
async def test_shutdown_admin(mock_bot, mock_interaction):
    # Create an Admin cog with the mock bot
    admin_cog = Admin(mock_bot)

    # Mock the bot's close method
    mock_bot.close = AsyncMock()

    # Mock the BaseCog cog and its check_category method
    mock_basecog = AsyncMock()
    mock_basecog.check_category.return_value = True
    mock_basecog.check_permissions.return_value = True
    mock_bot.get_cog.return_value = mock_basecog

    # Mock sys.exit
    with patch('sys.exit') as mock_exit:
        # Access the callback function directly
        callback = admin_cog.shutdown.callback

        # Call the callback function directly
        await callback(admin_cog, mock_interaction)

        # Verify the shutdown sequence
        mock_interaction.response.send_message.assert_called_once_with('**Shutting Down...**')
        mock_bot.conn.close.assert_called_once()
        mock_bot.close.assert_called_once()
        mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    pytest.main([__file__]) 