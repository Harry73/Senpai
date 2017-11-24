import logging
import aiohttp
from bs4 import BeautifulSoup as Bs

from lib.Message import Message

LOGGER = logging.getLogger("Senpai")


# Poll http://www.punoftheday.com/cgi-bin/randompun.pl for a random pun
async def pun():
	LOGGER.debug("Getting a pun...")

	text = None

	link = "http://www.punoftheday.com/cgi-bin/randompun.pl"
	async with aiohttp.ClientSession() as session:
		async with session.get(link) as r:
			if r.status == 200:
				source = await r.read()
				soup = Bs(source, "html.parser")

				section = soup.findAll("div", attrs={"class": "dropshadow1"})
				if len(section) > 0:
					text = section[0].p.text
			else:
				LOGGER.error("Can't find a pun. Status: {0}".format(r.status))

	if text:
		LOGGER.debug("Found pun: {0}".format(text))
		return Message(message=text)
	else:
		LOGGER.info("Something went wrong.")
		return Message(message="I don't know what happened, but no puns were found.")
