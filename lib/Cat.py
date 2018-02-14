import logging
import aiohttp

from lib.Message import Message

LOGGER = logging.getLogger('Senpai')


async def cat():
    LOGGER.debug('Cat.cat: request')

    url = 'http://random.cat/meow'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                js = await r.json()
                LOGGER.debug('Cat.cat: response, %s', js['file'])
                return Message(message=js['file'])
            else:
                LOGGER.error('Bad status: %s', r.status)
