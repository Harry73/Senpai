import aiohttp
import logging

from lib.Message import Message
from lib.Command import register_command


LOG = logging.getLogger('Senpai')


@register_command(lambda m: m.content == '/cat')
async def cat(bot, message):
    """```
    Links a random picture of a cat.

    Usage:
    * /cat
    ```"""

    url = 'http://aws.random.cat/meow'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                js = await r.json()
                return Message(message=js['file'])
            else:
                LOG.error('Bad status: %s', r.status)
