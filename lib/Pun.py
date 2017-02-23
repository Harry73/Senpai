import logging
import aiohttp
from bs4 import BeautifulSoup as BS

logger = logging.getLogger("Senpai")

# Poll http://www.punoftheday.com/cgi-bin/randompun.pl for a random pun
async def pun():
	logger.debug("Getting a pun...")

	text = None

	link = "http://www.punoftheday.com/cgi-bin/randompun.pl"
	async with aiohttp.get(link) as r:
		if r.status == 200:
			source = await r.read()
			soup = BS(source, "html.parser")

			section = soup.findAll("div", attrs={"class": "dropshadow1"})
			if len(section) > 0:
				text = section[0].p.text
		else:
			logger.error("Can't find a pun. Status: {0}".format(r.status))

	if text:
		logger.debug("Found pun: {0}".format(text))
		return {"message": text}
	else:
		logger.info("Something went wrong.")
		return {"message": "I don't know what happened, but no puns were found."}
