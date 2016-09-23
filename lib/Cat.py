import json
import logging
import aiohttp

logger = logging.getLogger("Senpai")

async def cat():
	url = "http://random.cat/meow"
	
	async with aiohttp.get(url) as r:
		if r.status == 200:
			js = await r.json()
			logger.debug("Cat picture: {0}".format(js["file"]))
			return js["file"]
		else:
			logger.error("Can't find a cat. Status: {0}".format(r.status))
			