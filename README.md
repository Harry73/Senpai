# Senpai
  
A discord bot written in python. Expects python3.5 or better  

I believe requirements.txt has all the pip packages needed, but it may be missing something. Install requirements with:  
```pip install -r requirements.txt```

I run this on a bot account, and use a "json/config.json" file like:
```
{
	"discord": "token"
}
```

Changes may be needed to run this as a bot account.

Start the bot with: ```python3.5 Senpai.py```  
Or run it under nohup with: ```bash start.sh```  

When it's running, use the following help commands:
```
    /senpai         -> Normal help function
    /secrets        -> Owner-only commands
```
Owner and bot IDs live in lib/IDs.py, along with some channel IDs. 

The bot will clean up after itself if you give it the "Manage messages" permission.
