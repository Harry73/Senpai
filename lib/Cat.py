import logging
import aiohttp

from lib.Message import Message

LOGGER = logging.getLogger("Senpai")

async def cat():
	url = "http://random.cat/meow"

	async with aiohttp.ClientSession() as session:
		async with session.get(url) as r:
			if r.status == 200:
				js = await r.json()
				LOGGER.debug("Cat picture: {0}".format(js["file"]))
				return Message(message=js["file"])
			else:
				LOGGER.error("Can't find a cat. Status: {0}".format(r.status))
