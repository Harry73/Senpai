import aiohttp
import logging

logger = logging.getLogger("Senpai")

# Method to edit the bot avatar
async def edit_avatar(client, image_url=None):
	# Change bot's profile picture
	if image_url:
		logger.info("Changing profile picture to {0}".format(image_url))
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(image_url) as r:
					if r.status == 200:
						new_image = await r.read()
						await client.edit_profile(password=client.config["discord"]["pass"], avatar=new_image)
					else:
						logger.error("Can't find picture. Status: {0}".format(r.status))
		except Exception as e:
			logger.exception(e)

# Method to edit the bot name
async def edit_username(client, new_username=None):
	# Change bot's username
	if new_username:
		logger.info("Changing username to {0}".format(new_username))
		try:
			await client.edit_profile(password=client.config["discord"]["pass"], username=new_username)
		except Exception as e:
			logger.exception(e)