import aiohttp
import logging

from lib import IDs

LOGGER = logging.getLogger('Senpai')


# Method to edit the bot avatar
async def edit_avatar(client, image_url=None):
    # Change bot's profile picture
    if image_url:
        LOGGER.debug('Profile.edit_avatar: new avatar %s', image_url)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as r:
                    if r.status == 200:
                        new_image = await r.read()
                        await client.edit_profile(avatar=new_image)
                    else:
                        LOGGER.error('Profile.edit_avatar: bad status: %s', r.status)
        except Exception as e:
            LOGGER.exception(e)
