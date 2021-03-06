# tgbot-post-broadcaster v0.3

Channel Post Broadcaster Telegram Bot

This Telegram Bot can read channel posts and broadcast them to connected channels.

Bot does not require any permissions (except for posting messages in channel as admin) and functions well with privacy
mode enabled.

WIP - support for multiple sources (sender) channels. WIP - configurable channels for sourcing posts.

### Setup

To start the bot, please follow the steps below:

* install Python 3.8 or higher
* install Python packages with `poetry install` or `pip isntall -r requirements.txt`
* copy `example.env` as `.env` and edit variables inside (it needs your bot token at least)
* run the code with `python start_polling.py`

### Controls

* `/help` - get general information about bot

#### In-group commands

All commands below are admin-only:

* `/start` - initialise group chat
* `/enable` - enable forwarding to this group chat
* `/disable` - disable forwarding to this group chat
* `/status` - display group chat status
* `/tags` - manage tag subscriptions
* `/debug` - display debug info
