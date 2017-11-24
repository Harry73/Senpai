import aiohttp
import logging

LOGGER = logging.getLogger("Senpai")


# Method to edit the bot avatar
async def editAvatar(client, image_url=None):
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
						LOGGER.error("Can't find picture. Status: {0}".format(r.status))
		except Exception as e:
			LOGGER.exception(e)


# Method to edit the bot name
async def editUsername(client, new_username=None):
	# Change bot's username
	if new_username:
		LOGGER.info("Changing username to {0}".format(new_username))
		try:
			await client.edit_profile(password=client.config["discord"]["pass"], username=new_username)
		except Exception as e:
			LOGGER.exception(e)
