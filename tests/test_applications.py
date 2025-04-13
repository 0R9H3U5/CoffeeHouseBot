import pytest
import discord
from unittest.mock import MagicMock, patch, AsyncMock
from cogs.applications import Applications

@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    bot = MagicMock()
    bot.getConfigValue = MagicMock(return_value="123456789")
    bot.execute_query = MagicMock(return_value=True)
    return bot

@pytest.fixture
def applications_cog(mock_bot):
    """Create an Applications cog instance with a mock bot."""
    return Applications(mock_bot)

@pytest.fixture
def mock_message():
    """Create a mock Discord message for testing."""
    message = MagicMock(spec=discord.Message)
    message.author = MagicMock(spec=discord.User)
    message.author.id = 123456789
    message.author.bot = False
    message.author.mention = "<@123456789>"
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = """
    What is your RSN? TestUser123
    How did you find out about the clan? Through a friend
    What are your favorite activities to do on Runescape? Skilling and PvM
    Where do you live and what timezone are you in? USA, EST
    How often do you play? Daily
    Have you read our ✅rules  and do you agree to abide by these rules? Yes
    Are you currently in another clan? No
    How do you drink your Coffee? Black
    """
    return message

@pytest.fixture
def mock_guild():
    """Create a mock Discord guild for testing."""
    guild = MagicMock(spec=discord.Guild)
    guild.get_member = MagicMock(return_value=MagicMock(spec=discord.Member))
    guild.get_role = MagicMock(return_value=MagicMock(spec=discord.Role))
    return guild

@pytest.fixture
def mock_member():
    """Create a mock Discord member for testing."""
    member = MagicMock(spec=discord.Member)
    member.add_roles = AsyncMock()  # Use AsyncMock for async methods
    return member

@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction for testing."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction

def test_is_application_message(applications_cog):
    """Test that the _is_application_message method correctly identifies application messages."""
    # Valid application message
    valid_message = """
    What is your RSN? TestUser123
    How did you find out about the clan? Through a friend
    What are your favorite activities to do on Runescape? Skilling and PvM
    Where do you live and what timezone are you in? USA, EST
    How often do you play? Daily
    Have you read our ✅rules  and do you agree to abide by these rules? Yes
    Are you currently in another clan? No
    How do you drink your Coffee? Black
    """
    assert applications_cog._is_application_message(valid_message) is True
    
    # Invalid application message (missing a question)
    invalid_message = """
    What is your RSN? TestUser123
    How did you find out about the clan? Through a friend
    What are your favorite activities to do on Runescape? Skilling and PvM
    Where do you live and what timezone are you in? USA, EST
    How often do you play? Daily
    Have you read our ✅rules  and do you agree to abide by these rules? Yes
    Are you currently in another clan? No
    """
    assert applications_cog._is_application_message(invalid_message) is False

def test_extract_answer(applications_cog):
    """Test that the _extract_answer method correctly extracts answers from application messages."""
    message = """
    What is your RSN? TestUser123
    How did you find out about the clan? Through a friend
    What are your favorite activities to do on Runescape? Skilling and PvM
    Where do you live and what timezone are you in? USA, EST
    How often do you play? Daily
    Have you read our ✅rules  and do you agree to abide by these rules? Yes
    Are you currently in another clan? No
    How do you drink your Coffee? Black
    """
    
    # Test extracting RSN
    rsn = applications_cog._extract_answer(message, "What is your RSN?")
    assert rsn == "TestUser123"
    
    # Test extracting location/timezone
    location = applications_cog._extract_answer(message, "Where do you live and what timezone are you in?")
    assert location == "USA, EST"
    
    # Test extracting a non-existent question
    nonexistent = applications_cog._extract_answer(message, "What is your favorite color?")
    assert nonexistent is None

@pytest.mark.asyncio
async def test_process_application_success(applications_cog, mock_message, mock_guild, mock_member, mock_interaction):
    """Test successful application processing."""
    # Set up mocks
    applications_cog.bot.execute_query = MagicMock(return_value=True)
    mock_message.guild = mock_guild
    mock_guild.get_member.return_value = mock_member
    
    # Mock the role object
    mock_role = MagicMock()
    mock_role.name = "Trial Member"
    mock_guild.get_role.return_value = mock_role
    
    # Mock the selectOne to return None (user not found)
    applications_cog.bot.selectOne = MagicMock(return_value=None)
    
    # Process the application
    await applications_cog._process_application(mock_message, mock_interaction)
    
    # Verify database query was executed with correct parameters
    applications_cog.bot.execute_query.assert_called_once()
    query = applications_cog.bot.execute_query.call_args[0][0]
    assert "INSERT INTO member" in query
    assert "TestUser123" in query  # RSN
    assert "USA" in query  # Location
    assert "EST" in query  # Timezone
    assert "123456789" in query  # Discord ID
    assert "membership_level" in query
    assert "0" in query  # Membership level
    assert "active" in query
    assert "true" in query
    assert "on_leave" in query
    assert "false" in query
    assert "skill_comp_pts" in query
    assert "0" in query
    assert "skill_comp_pts_life" in query
    assert "0" in query
    assert "boss_comp_pts" in query
    assert "0" in query
    assert "boss_comp_pts_life" in query
    assert "0" in query
    assert "Through a friend" in query  # How found clan
    assert "Skilling and PvM" in query  # Favorite activities
    assert "Daily" in query  # Play frequency
    assert "Black" in query  # Coffee preference
    
    # Verify role was added
    mock_member.add_roles.assert_called_once_with(mock_role)
    
    # Verify confirmation message was sent
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args[1]  # Use kwargs instead of args
    assert "embed" in call_args
    embed = call_args["embed"]
    assert embed.title == "Application Accepted!"
    assert "TestUser123" in embed.description

@pytest.mark.asyncio
async def test_process_application_db_error(applications_cog, mock_message, mock_interaction):
    """Test application processing when database query fails."""
    # Set up mocks
    applications_cog.bot.execute_query = MagicMock(return_value=False)
    applications_cog.bot.selectOne = MagicMock(return_value=None)  # User not found
    
    # Process the application
    await applications_cog._process_application(mock_message, mock_interaction)
    
    # Verify error message was sent
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args[0]
    assert "error" in call_args[0].lower()
    assert "contact an admin" in call_args[0].lower()

@pytest.mark.asyncio
async def test_process_application_missing_rsn(applications_cog, mock_message, mock_interaction):
    """Test application processing when RSN is missing."""
    # Modify message to remove RSN
    mock_message.content = """
    What is your RSN? 
    How did you find out about the clan? Through a friend
    What are your favorite activities to do on Runescape? Skilling and PvM
    Where do you live and what timezone are you in? USA, EST
    How often do you play? Daily
    Have you read our ✅rules  and do you agree to abide by these rules? Yes
    Are you currently in another clan? No
    How do you drink your Coffee? Black
    """
    
    # Process the application
    await applications_cog._process_application(mock_message, mock_interaction)
    
    # Verify error message was sent
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args[0]
    assert "i couldn't find the rsn in the application" in call_args[0].lower()
    
    # Verify database query was not executed
    applications_cog.bot.execute_query.assert_not_called()

@pytest.mark.asyncio
async def test_process_application_duplicate_user(applications_cog, mock_message, mock_interaction):
    """Test application processing when user is already registered."""
    # Set up mocks
    applications_cog.bot.selectOne = MagicMock(return_value=("TestUser123", 123456789))  # User already exists
    
    # Process the application
    await applications_cog._process_application(mock_message, mock_interaction)
    
    # Verify error message was sent
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args[0]
    assert "both rsn 'testuser123' and discord id 123456789 are already registered in the clan" in call_args[0].lower()
    
    # Verify database query was not executed
    applications_cog.bot.execute_query.assert_not_called() 