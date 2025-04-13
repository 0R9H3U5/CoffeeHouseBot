import pytest
import discord
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import datetime
import json
import psycopg2

# Add the parent directory to the path so we can import the bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the CoffeeHouseBot class
from bot import CoffeeHouseBot

# Test the getNextMemLvlDate function with various inputs
def test_getNextMemLvlDate():
    # Create a mock bot
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Test with mem_lvl 0 and a join date of today
    today = datetime.date.today()
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, today)
    assert result == today + datetime.timedelta(days=14)
    
    # Test with mem_lvl 0 and a join date of 13 days ago
    thirteen_days_ago = today - datetime.timedelta(days=13)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, thirteen_days_ago)
    assert result == thirteen_days_ago + datetime.timedelta(days=14)
    
    # Test with mem_lvl 0 and a join date of 15 days ago
    fifteen_days_ago = today - datetime.timedelta(days=15)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, fifteen_days_ago)
    assert result == fifteen_days_ago + datetime.timedelta(days=84)
    
    # Test with mem_lvl 1 and a join date of 83 days ago
    eighty_three_days_ago = today - datetime.timedelta(days=83)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 1, eighty_three_days_ago)
    assert result == eighty_three_days_ago + datetime.timedelta(days=84)
    
    # Test with mem_lvl 1 and a join date of 85 days ago
    eighty_five_days_ago = today - datetime.timedelta(days=85)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 1, eighty_five_days_ago)
    assert result == eighty_five_days_ago + datetime.timedelta(days=182)
    
    # Test with mem_lvl 2 and a join date of 181 days ago
    one_eighty_one_days_ago = today - datetime.timedelta(days=181)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 2, one_eighty_one_days_ago)
    assert result == one_eighty_one_days_ago + datetime.timedelta(days=182)
    
    # Test with mem_lvl 2 and a join date of 183 days ago
    one_eighty_three_days_ago = today - datetime.timedelta(days=183)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 2, one_eighty_three_days_ago)
    assert result == one_eighty_three_days_ago + datetime.timedelta(days=365)
    
    # Test with mem_lvl 3 and a join date of 364 days ago
    three_sixty_four_days_ago = today - datetime.timedelta(days=364)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 3, three_sixty_four_days_ago)
    assert result == three_sixty_four_days_ago + datetime.timedelta(days=365)
    
    # Test with mem_lvl 3 and a join date of 366 days ago
    three_sixty_six_days_ago = today - datetime.timedelta(days=366)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 3, three_sixty_six_days_ago)
    assert result is None
    
    # Test with mem_lvl 4 (Tenured - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 4, today)
    assert result is None
    
    # Test with mem_lvl 5 (Esteemed - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 5, today)
    assert result is None
    
    # Test with mem_lvl 6 (Moderator - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 6, today)
    assert result is None
    
    # Test with mem_lvl 7 (Captain - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 7, today)
    assert result is None
    
    # Test with mem_lvl 8 (Owner - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 8, today)
    assert result is None
    
    # Test with string date
    date_str = today.strftime("%Y-%m-%d")
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, date_str)
    assert result == today + datetime.timedelta(days=14)
    
    # Test with invalid date string
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, "invalid-date")
    assert result is None
    
    # Test with datetime object
    datetime_obj = datetime.datetime.combine(today, datetime.time())
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, datetime_obj)
    assert result == today + datetime.timedelta(days=14)
    
    # Test with invalid date type
    result = CoffeeHouseBot.getNextMemLvlDate(mock_bot, 0, 12345)
    assert result is None

# Test the getExpectedMemLvlByJoinDate function with various inputs
def test_getExpectedMemLvlByJoinDate():
    # Create a mock bot
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Test with join date of today
    today = datetime.date.today()
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, today)
    assert result == 0
    
    # Test with join date of 13 days ago
    thirteen_days_ago = today - datetime.timedelta(days=13)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, thirteen_days_ago)
    assert result == 0
    
    # Test with join date of 15 days ago
    fifteen_days_ago = today - datetime.timedelta(days=15)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, fifteen_days_ago)
    assert result == 1
    
    # Test with join date of 83 days ago
    eighty_three_days_ago = today - datetime.timedelta(days=83)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, eighty_three_days_ago)
    assert result == 1
    
    # Test with join date of 85 days ago
    eighty_five_days_ago = today - datetime.timedelta(days=85)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, eighty_five_days_ago)
    assert result == 2
    
    # Test with join date of 181 days ago
    one_eighty_one_days_ago = today - datetime.timedelta(days=181)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, one_eighty_one_days_ago)
    assert result == 2
    
    # Test with join date of 183 days ago
    one_eighty_three_days_ago = today - datetime.timedelta(days=183)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, one_eighty_three_days_ago)
    assert result == 3
    
    # Test with join date of 364 days ago
    three_sixty_four_days_ago = today - datetime.timedelta(days=364)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, three_sixty_four_days_ago)
    assert result == 3
    
    # Test with join date of 366 days ago
    three_sixty_six_days_ago = today - datetime.timedelta(days=366)
    result = CoffeeHouseBot.getExpectedMemLvlByJoinDate(mock_bot, three_sixty_six_days_ago)
    assert result == 3

# Test the getNextMemLvl function with various inputs
def test_getNextMemLvl():
    # Create a mock bot with configs
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_bot.configs = {
        "mem_level_names": ["Trial", "Junior", "Member", "Senior", "Tenured", "Esteemed", "Moderator", "Captain", "Owner"]
    }
    
    # Test with mem_lvl 0 (Trial -> Junior)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 0)
    assert result == "Junior"
    
    # Test with mem_lvl 1 (Junior -> Member)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 1)
    assert result == "Member"
    
    # Test with mem_lvl 2 (Member -> Senior)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 2)
    assert result == "Senior"
    
    # Test with mem_lvl 3 (Senior -> Tenured)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 3)
    assert result == "Tenured"
    
    # Test with mem_lvl 4 (Tenured - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 4)
    assert result is None
    
    # Test with mem_lvl 5 (Esteemed - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 5)
    assert result is None
    
    # Test with mem_lvl 6 (Moderator - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 6)
    assert result is None
    
    # Test with mem_lvl 7 (Captain - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 7)
    assert result is None
    
    # Test with mem_lvl 8 (Owner - no automatic progression)
    result = CoffeeHouseBot.getNextMemLvl(mock_bot, 8)
    assert result is None

# Test the queryMembers function
def test_queryMembers():
    # Create a mock bot
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Mock the cursor and its execute method
    mock_cursor = MagicMock()
    mock_cursor.execute.return_value = [
        {"_id": 1, "rsn": "User1", "discord_id": "User1#1234"},
        {"_id": 2, "rsn": "User2", "discord_id": "User2#5678"}
    ]
    mock_bot.cursor = mock_cursor
    
    # Call the function
    result = CoffeeHouseBot.queryMembers(mock_bot, "key", "value")
    
    # Verify the result
    assert "ID |          RSN          |     Discord ID" in result
    assert "1   User1   User1#1234" in result
    assert "2   User2   User2#5678" in result

# Test the getConfigValue function
def test_getConfigValue():
    # Create a mock bot with configs
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_bot.configs = {
        "key1": "value1",
        "key2": "value2"
    }
    
    # Test with existing key
    result = CoffeeHouseBot.getConfigValue(mock_bot, "key1")
    assert result == "value1"
    
    # Test with another existing key
    result = CoffeeHouseBot.getConfigValue(mock_bot, "key2")
    assert result == "value2"

# Test the getDatabaseConnection function
@patch('psycopg2.connect')
def test_getDatabaseConnection(mock_connect):
    # Create a mock bot with configs
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_bot.configs = {
        "db_name": "test_db",
        "db_user": "test_user",
        "db_pw": "test_pw",
        "db_host": "test_host",
        "db_port": "25640"
    }

    # Mock the getConfigValue method to return the correct values
    def mock_get_config_value(key):
        return mock_bot.configs[key]
    mock_bot.getConfigValue = mock_get_config_value

    # Mock the connection
    mock_conn = MagicMock()
    mock_conn.get_dsn_parameters.return_value = {"dbname": "test_db"}
    mock_connect.return_value = mock_conn

    # Call the function
    CoffeeHouseBot.getDatabaseConnection(mock_bot)

    # Verify that connect was called with the correct parameters
    mock_connect.assert_called_once_with('postgres://test_user:test_pw@test_host:25640/test_db?sslmode=require')

    # Verify that the connection was assigned to the bot
    assert mock_bot.conn == mock_conn

# Test the check_database_connection function with active connection
@patch('psycopg2.connect')
def test_check_database_connection_active(mock_connect):
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_bot.conn = mock_conn
    
    # Call the function
    result = CoffeeHouseBot.check_database_connection(mock_bot)
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with('SELECT 1')
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is True
    assert result is True
    
    # Verify that connect was not called
    mock_connect.assert_not_called()

# Test the check_database_connection function with lost connection
@patch('psycopg2.connect')
def test_check_database_connection_lost(mock_connect):
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = psycopg2.OperationalError()
    mock_bot.conn = mock_conn

    # Mock the new connection
    mock_new_conn = MagicMock()
    mock_connect.return_value = mock_new_conn

    # Mock the getDatabaseConnection method to use our patched connect function
    mock_get_database_connection = MagicMock()
    mock_get_database_connection.return_value = True
    mock_bot.getDatabaseConnection = mock_get_database_connection

    # Call the function
    result = CoffeeHouseBot.check_database_connection(mock_bot)

    # Verify that getDatabaseConnection was called
    mock_bot.getDatabaseConnection.assert_called_once()

    # Verify the result is True
    assert result is True

# Test the check_database_connection function with failed reconnection
@patch('psycopg2.connect')
def test_check_database_connection_failed_reconnect(mock_connect):
    # Create a mock bot with a connection that raises an error
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = psycopg2.OperationalError()
    mock_bot.conn = mock_conn
    
    # Mock the getDatabaseConnection method
    mock_get_database_connection = MagicMock()
    mock_get_database_connection.side_effect = lambda: setattr(mock_bot, 'conn', mock_connect())
    mock_bot.getDatabaseConnection = mock_get_database_connection
    
    # Mock the new connection to raise an error
    mock_connect.side_effect = Exception("Connection failed")
    
    # Call the function
    result = CoffeeHouseBot.check_database_connection(mock_bot)
    
    # Verify that connect was called
    mock_connect.assert_called_once()
    
    # Verify that getDatabaseConnection was called
    assert mock_bot.getDatabaseConnection.call_count == 1
    
    # Verify the result is False
    assert result is False

# Test the selectMany function with active connection
def test_selectMany_active_connection():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("row1",), ("row2",)]
    mock_bot.conn = mock_conn
    
    # Mock the check_database_connection function to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Call the function
    result = CoffeeHouseBot.selectMany(mock_bot, "SELECT * FROM table")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT * FROM table")
    mock_cursor.fetchall.assert_called_once()
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is correct
    assert result == [("row1",), ("row2",)]

# Test the selectMany function with lost connection
def test_selectMany_lost_connection():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Mock the check_database_connection function to return False
    mock_bot.check_database_connection = MagicMock(return_value=False)
    
    # Call the function
    result = CoffeeHouseBot.selectMany(mock_bot, "SELECT * FROM table")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the result is None
    assert result is None

# Test the selectMany function with error
def test_selectMany_error():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error()
    mock_bot.conn = mock_conn
    
    # Mock the check_database_connection function to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Call the function
    result = CoffeeHouseBot.selectMany(mock_bot, "SELECT * FROM table")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT * FROM table")
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is None
    assert result is None

# Test the selectOne function with active connection
def test_selectOne_active_connection():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("row1",)
    mock_bot.conn = mock_conn
    
    # Mock the check_database_connection function to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Call the function
    result = CoffeeHouseBot.selectOne(mock_bot, "SELECT * FROM table")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT * FROM table")
    mock_cursor.fetchone.assert_called_once()
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is correct
    assert result == ("row1",)

# Test the selectOne function with lost connection
def test_selectOne_lost_connection():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Mock the check_database_connection function to return False
    mock_bot.check_database_connection = MagicMock(return_value=False)
    
    # Call the function
    result = CoffeeHouseBot.selectOne(mock_bot, "SELECT * FROM table")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the result is None
    assert result is None

# Test the selectOne function with error
def test_selectOne_error():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error()
    mock_bot.conn = mock_conn
    
    # Mock the check_database_connection function to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Call the function
    result = CoffeeHouseBot.selectOne(mock_bot, "SELECT * FROM table")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT * FROM table")
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is None
    assert result is None

# Test the execute_query function with active connection
def test_execute_query_active_connection():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_bot.conn = mock_conn
    
    # Mock the check_database_connection function to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Call the function
    result = CoffeeHouseBot.execute_query(mock_bot, "UPDATE table SET column = 'value'")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("UPDATE table SET column = 'value'")
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is True
    assert result is True

# Test the execute_query function with lost connection
def test_execute_query_lost_connection():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Mock the check_database_connection function to return False
    mock_bot.check_database_connection = MagicMock(return_value=False)
    
    # Call the function
    result = CoffeeHouseBot.execute_query(mock_bot, "UPDATE table SET column = 'value'")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the result is False
    assert result is None

# Test the execute_query function with error
def test_execute_query_error():
    # Create a mock bot with a connection
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error()
    mock_bot.conn = mock_conn
    
    # Mock the check_database_connection function to return True
    mock_bot.check_database_connection = MagicMock(return_value=True)
    
    # Call the function
    result = CoffeeHouseBot.execute_query(mock_bot, "UPDATE table SET column = 'value'")
    
    # Verify that check_database_connection was called
    mock_bot.check_database_connection.assert_called_once()
    
    # Verify that the cursor was created and closed
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("UPDATE table SET column = 'value'")
    mock_cursor.close.assert_called_once()
    
    # Verify that the result is False
    assert result is None

# Test the format_money function with various inputs
def test_format_money():
    # Create a mock bot
    mock_bot = MagicMock(spec=CoffeeHouseBot)
    
    # Test with amounts less than 1000
    assert CoffeeHouseBot.format_money(mock_bot, 0) == "0 gp"
    assert CoffeeHouseBot.format_money(mock_bot, 100) == "100 gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999) == "999 gp"
    
    # Test with amounts in thousands (K)
    assert CoffeeHouseBot.format_money(mock_bot, 1000) == "1K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 1009) == "1K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 1500) == "1.5K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 99900) == "99.9K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 99950) == "99.9K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 99999) == "99.9K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999500) == "999.5K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999600) == "999.6K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999700) == "999.7K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999800) == "999.8K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999900) == "999.9K gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999999) == "999.9K gp"
    
    # Test with amounts in millions (M)
    assert CoffeeHouseBot.format_money(mock_bot, 1000000) == "1M gp"
    assert CoffeeHouseBot.format_money(mock_bot, 1500000) == "1.5M gp"
    assert CoffeeHouseBot.format_money(mock_bot, 2000400) == "2M gp"
    assert CoffeeHouseBot.format_money(mock_bot, 755200080) == "755.2M gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999999999) == "999.9M gp"
    
    # Test with amounts in trillions (T)
    assert CoffeeHouseBot.format_money(mock_bot, 1000000000) == "1T gp"
    assert CoffeeHouseBot.format_money(mock_bot, 1500000000) == "1.5T gp"
    assert CoffeeHouseBot.format_money(mock_bot, 4000000000) == "4T gp"
    assert CoffeeHouseBot.format_money(mock_bot, 999999999999) == "999.9T gp"
    
    # Test with custom unit
    assert CoffeeHouseBot.format_money(mock_bot, 1000, "coins") == "1K coins"
    assert CoffeeHouseBot.format_money(mock_bot, 1000000, "coins") == "1M coins"
    assert CoffeeHouseBot.format_money(mock_bot, 1000000000, "coins") == "1T coins" 