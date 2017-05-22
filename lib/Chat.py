import logging
import aiohttp
from bs4 import BeautifulSoup as BS

from lib import Names

logger = logging.getLogger("Senpai")
sessions = {}

async def chat(authorID, message):
	global sessions
	logger.debug("Chat message: {0}".format(message))
	
	if authorID in sessions:
		session = sessions[authorID]
	else:
		session = aiohttp.ClientSession()
		sessions[authorID] = session
		await learnNewName(authorID)
		
	message = message.replace("Senpai", "Μitsuku")
	message = message.replace("senpai", "mitsuku")
	message = message.replace("Ian", "Mousebreaker")
	message = message.replace("ian", "mousebreaker")
	
	url = "https://kakko.pandorabots.com/pandora/talk?botid=f326d0be8e345a13"
	submission = {"input": message}

	# Post and get response
	async with session.post(url, data=submission) as r:
		if r.status == 200:
			source = await r.text()
		else:
			logger.error("Chat AI failed. Status: {0}".format(r.status))
			return {}
		r.release()
	
	# Parse response text
	if source:
		soup = BS(str(source).replace("<br>", "\n"), "html.parser")
		response = soup.findAll("font", attrs={"color": "#000000"})

		text = str(response[0].text).strip()
		
		text = text[text.find("Μitsuku:")+9:]
		if "You:" in text:
			text = text[:text.find("You:")]
		
		text = text.replace("Μitsuku", "Senpai")
		text = text.replace("Mousebreaker", "Ian")
		text = text.replace("mitsuku", "senpai")
		text = text.replace("mousebreaker", "ian")
		text = text.strip()
		
		logger.debug("Reply: {0}".format(text))
		return {"message": text}

# Have the chatbot learn the nickname of the author
async def learnNewName(authorID):
	if authorID in sessions:
		name = Names.getName(authorID)
		if name:
			session = sessions[authorID]
			url = "https://kakko.pandorabots.com/pandora/talk?botid=f326d0be8e345a13"
			
			# Normal kind of name-learning
			submission = {"input": "My name is {0}".format(name)}
			async with session.post(url, data=submission) as r:
				if r.status == 200:
					logger.debug("Chat AI normally learned nickname {0}".format(name))
				else:
					logger.error("Chat AI failed to normally learn nickname {0}. Status: {1}".format(name, r.status))
					return {}
				r.release()
				
			# Forced kind of name-learning
			submission = {"input": "learn My name is {0}".format(name)}
			async with session.post(url, data=submission) as r:
				if r.status == 200:
					logger.debug("Chat AI forcibly learned nickname {0}".format(name))
				else:
					logger.error("Chat AI failed to forcibly learn nickname {0}. Status: {1}".format(name, r.status))
					return {}
				r.release()
		else:
			logger.warning("Chat AI didn't learn nickname, no nickname found.")
	else:
		logger.warning("Chat AI didn't learn nickname, authorID session not found.")