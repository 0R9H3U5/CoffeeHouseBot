import pytest
import discord
from unittest.mock import AsyncMock, MagicMock
import datetime
import sys
import os

# Add the parent directory to the path so we can import the cogs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Common fixtures for all tests

@pytest.fixture
def mock_bot():
    """Create a mock bot with common methods."""
    bot = MagicMock()
    bot.config = {
        "mem_level_names": ["Newbie", "Member", "Veteran", "Elite"]
    }
    
    # Mock the selectOne method
    bot.selectOne = MagicMock(return_value=(
        1,  # _id
        "TestUser",  # rsn
        None,  # discord_id_num
        "123456789",  # discord_id
        1,  # membership_level
        datetime.datetime.now().date(),  # join_date
        None,  # special_status
        ["OldRSN1", "OldRSN2"],  # previous_rsn - ensure this is a list or None
        ["Alt1", "Alt2"],  # alt_rsn - ensure this is a list or None
        True,  # on_leave
        True,  # active
        100,  # skill_comp_points
        50,  # skill_comp_pts_life
        "US",  # loc
        "EST",  # timezone
        "Some notes"  # notes
    ))
    
    # Mock the getConfigValue method
    bot.getConfigValue = MagicMock(return_value=["Newbie", "Member", "Veteran", "Elite"])
    
    # Mock the getNextMemLvlDate method
    bot.getNextMemLvlDate = MagicMock(return_value=datetime.datetime.now().date() + datetime.timedelta(days=30))
    
    return bot

@pytest.fixture
def mock_interaction():
    """Create a mock interaction with admin permissions."""
    interaction = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.guild_permissions = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.user.name = "TestUser"
    interaction.user.display_avatar = MagicMock()
    interaction.user.display_avatar.url = "https://example.com/avatar.png"
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    return interaction 