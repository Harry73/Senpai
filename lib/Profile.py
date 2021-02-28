import aiohttp
import logging

from lib.Command import CommandType, register_command


LOG = logging.getLogger('Senpai')


# Method to edit the bot avatar
@register_command(lambda m: m.content.startswith('/profile'), command_type=CommandType.OWNER)
async def profile(bot, message):
    """```
    Set Senpai's profile picture from a given url.

    Usage:
    * /profile image_url
    ```"""
    image_url = message.content[8:].strip()

    if image_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as r:
                    if r.status == 200:
                        new_image = await r.read()
                        await bot.edit_profile(avatar=new_image)
                    else:
                        LOG.error('bad status: %s', r.status)
        except Exception as e:
            LOG.error('Error updating profile image', exc_info=e)
