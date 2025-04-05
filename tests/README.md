# Unit Tests for CoffeeHouseBot

This directory contains unit tests for the CoffeeHouseBot Discord bot.

## Setup

1. Install the required packages:

```bash
pip install -r requirements-test.txt
```

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_admin.py
```

To run a specific test function:

```bash
pytest tests/test_admin.py::test_view_member_admin
```

To run tests with coverage report:

```bash
pytest --cov=cogs tests/
```

## Test Structure

- `conftest.py`: Contains common fixtures used across multiple test files
- `test_admin.py`: Tests for the Admin cog
- `test_dev.py`: Tests for the Dev cog (to be implemented)
- `test_user_lookup.py`: Tests for the UserLookup cog (to be implemented)
- `test_lottery.py`: Tests for the Lottery cog (to be implemented)

## Writing New Tests

When writing new tests:

1. Create a new test file if testing a new cog
2. Use the fixtures from `conftest.py` when possible
3. Follow the pattern of the existing tests
4. Make sure to test both success and failure cases
5. Use descriptive test names that explain what is being tested 