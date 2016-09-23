import aiohttp
import logging

logger = logging.getLogger("Senpai")

# Method to edit the bot account
async def edit_profile(client, image_url=None):
	# Change bot's profile picture
	if image_url:
		logger.info("Changing profile picture to {0}".format(image_url))
		try:
			async with aiohttp.get(image_url) as r:
				if r.status == 200:
					new_image = await r.read()
					await client.edit_profile(password=client.config["discord"]["pass"], avatar=new_image)
				else:
					logger.error("Can't find picture. Status: {0}".format(r.status))
		except Exception as e:
			logger.exception(e)