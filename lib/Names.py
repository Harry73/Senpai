import os
import json
import logging

from lib import Chat

logger = logging.getLogger("Senpai")

# Say hi to the user, and use the nickname they've chosen
async def hi(authorID):
	if os.path.isfile("names.txt"):		
		with open("names.txt", "r") as f:
			names = json.load(f)
			
		if authorID in names:
			return {"message": "Hi {0}.".format(names[authorID])}
		else:
			return {"message": "Hi. I don't have a name for you, use /callme <name> to pick your name."}
	else:
		with open("names.txt", "w") as f:
			f.write("{}")
		return {"message": "Hi. I don't have a name for you, use /callme <name> to pick your name."}
	
# Update "names.txt" with the new nickname
async def callme(authorID, newName):
	with open("names.txt", "r") as f:
		names = json.load(f)
		
	names[authorID] = newName
		
	with open("names.txt", "w") as f:
		json.dump(names, f)
		
	# Update the chatbot part with the new name
	await Chat.learnNewName(authorID)
		
	return {"message": "Got it {0}!".format(newName)}
	
def getName(authorID):
	if os.path.isfile("names.txt"):
		with open("names.txt", "r") as f:
			names = json.load(f)
			
		if authorID in names:
			return names[authorID]
	
	return None