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

## Scopes and Permissions
### Scopes
Currently this bot expects to be added to a sever with the `bot` and `applictions.commands` scopes

### Roles
Permissions:
----------------------------------------------
| Permission                         | Value |
|-------------------------------------|-------|
| add_reactions                      | True  |
| attach_files                        | True  |
| change_nickname                     | True  |
| connect                             | True  |
| create_expressions                  | True  |
| create_events                       | True  |
| create_instant_invite              | True  |
| create_private_threads              | True  |
| create_public_threads               | True  |
| deafen_members                      | False |
| embed_links                         | True  |
| environment_stickers                | True  |
| external_emojis                     | True  |
| external_stickers                   | True  |
| manage_channels                     | True  |
| manage_expressions                  | True  |
| manage_events                       | True  |
| manage_guild                        | True  |
| manage_messages                     | True  |
| manage_nicknames                    | True  |
| manage_roles                        | True  |
| manage_threads                      | True  |
| manage_webhooks                     | True  |
| mention_everyone                    | True  |
| move_members                        | False |
| mute_members                        | False |
| priority_speaker                    | False |
| read_message_history                | True  |
| read_messages                       | True  |
| request_to_speak                    | True  |
| send_messages                       | True  |
| send_messages_in_threads            | True  |
| send_polls                          | True  |
| send_tts_messages                   | False |
| send_voice_messages                 | True  |
| speak                               | True  |
| stream                              | True  |
| use_application_commands            | True  |
| use_embedded_activities             | True  |
| use_external_apps                   | True  |
| use_external_sounds                 | True  |
| use_soundboard                      | True  |
| use_voice_activation                | True  |
| view_audit_log                      | False |
| view_creator_monetization_analytics | False |
| view_guild_insights                 | False |
-----------------------------------------------