# Senpai
  
A discord bot written in python. Requires python3.5 or better  

`requirements.txt` should have all the pip packages needed, but they may need updates. 
Install requirements with:  

```
pip install -r requirements.txt
```

I run this on a bot account. Edit your bot token into `json/config.json` file like:

```
{
	"discord": "token"
}
```

Start the bot with: ```python3 Senpai.py```  
Alternatively, I recommend running under pm2: ```pm2 start Senpai.py```

When it's running, use the following help commands:

```
/senpai     -> Normal help function
/secrets    -> Owner-only commands
```

Owner and bot IDs live in `lib/IDs.py`, along with some channel IDs. 

The bot will clean up after itself if you give it the "Manage messages" permission.

Scheduled events are defined in `json/events.json`, and have corresponding event handlers in `lib/Events.py`.

See `lib/Command.py` for guidance on creating new commands for the bot, and/or use other commands as a model.

The GitHub version of Senpai is slightly modified, so I won't guarantee that this works out of the box, 
but it should mostly be functional. 
