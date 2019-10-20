# Senpai

A discord bot written in python. Requires python3.6 or better

## Installing Requirements

Install OS packages first:

```
sudo apt install libffi-dev libopus0 python3 python3-pip
```

`requirements.txt` should have all the pip packages needed, but they may need updates.
Install requirements with:

```
pip install -r requirements.txt
```

## Config

I run this on a bot account. Edit your bot token into `json/config.json` file like:

```
{
	"discord": "token"
}
```

## Running

Start the bot with:

```
python3 Senpai.py
```

### Run under `pm2`

```
sudo apt install npm
npm install pm2 -g
pm2 start Senpai.py --interpreter=python3
```

## Usage

When it's running, use the following help commands from discord:

```
/senpai     -> Normal help function
/secrets    -> Owner-only commands
```

The bot will clean up after itself if you give it the "Manage messages" permission.

## Code Structure

Owner and bot IDs live in `lib/Ids.py`, along with some channel IDs.

Scheduled events are defined in `json/events.json`, and have corresponding event handlers in `lib/Events.py`.

See `lib/Command.py` for guidance on creating new commands for the bot, or use pre-existing commands as models.

The GitHub version of Senpai is slightly modified, so I won't guarantee that this works out of the box,
but it should mostly be functional.
