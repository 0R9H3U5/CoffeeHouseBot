# CoffeeHouseBot
A Discord bot for managing the Coffee House clan in Old School RuneScape.

## Features
- Member management
- Lottery system
- Skill and Boss competition tracking
- Development tools

## Requirements
```
apt install python3, python 3.10-venv, python3-pip, libpq-dev
```

## How to run it
1. Set up venv and install python reqs by running `source install.sh`
2. Run the bot `python3 bot.py`

## Template files
### config.json
Configuration values are loaded from config.json. There is a template file of sorts with sensitive information removed in the root directory. Simply rename this file to config.json and update with missing values such as database info and `test_server_guild_id`

### .env
This bot expects a .env file in the root of the project. This is how it obtains the guild id and the discord auth token.
Simply rename the .env.tmpl file to .env and update with missing values.<br>
**_NOTE:_**  For more info on obtaining an auth token see https://discord.com/developers/docs/quick-start/getting-started#fetching-your-credentials

## Design
### Database 
This bot uses a remote hosted PostgreSQL database. You can configure it to use any PostgreSQL instance by updating the database info in config.json.

In order to set up your database use a program such as DBeaver to connect to your database server and run `sql/create-db.sql`

There is a sample dataset in `sql/populate-test-data` which can be run to populate data for testing

## Unit Tests
There are a set of unit tests in the `tests` directory. To run these install the pip requirements in `requirements-test.txt` and then run the command `pytest` from the root of the project
