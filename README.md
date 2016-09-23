# Senpai
  
A discord bot written in python  
Expects python3.5  

I believe requirements.txt has all the pip packages needed, but it may be missing something. Install requirements with:  
	pip install -r requirements.txt  

You must provide a "Config.json" file with:
	{
		"discord": {
			"email": "example@email.com",
			"pass": "example_Password"
		},
	}
	
Start the bot with:  
	bash start.sh  
	
When it's running, use the following help commands:
	/senpai			-> Normal help function
	/secrets		-> Owner-only commands
