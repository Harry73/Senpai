import logging
import aiohttp
from bs4 import BeautifulSoup as BS

logger = logging.getLogger("Senpai")

async def chat(message):
	logger.debug("Chat message: {0}".format(message))

	message = message.replace("Senpai", "Mitsuku")

	url = "https://kakko.pandorabots.com/pandora/talk?botid=f326d0be8e345a13"
	submission = {"input": message}

	# Post and get response
	async with aiohttp.post(url, data=submission) as r:
		if r.status == 200:
			source = await r.text()
		else:
			logger.error("Chat AI failed. Status: {0}".format(r.status))
			return
	
	# Parse response text
	if source:
		soup = BS(source, "html.parser")
		response = soup.findAll("font", attrs={"color": "#000000"})
		text = response[0].text
		text = text[text.find("Mitsuku:")+9:]
		if "You:" in text:
			text = text[:test.find("You:")]
		text = text.replace("Mitsuku", "Senpai")
		text = text.replace("Mousebreaker", "Ian")
		text = text.strip()

		logger.debug("Reply: {0}".format(text))
		return text
