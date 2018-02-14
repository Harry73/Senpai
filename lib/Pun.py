import logging
import aiohttp
from bs4 import BeautifulSoup as Bs

from lib.Message import Message

LOGGER = logging.getLogger('Senpai')


# Poll http://www.punoftheday.com/cgi-bin/randompun.pl for a random pun
async def pun():
    LOGGER.debug('Pun.pun: request')

    text = None

    link = 'http://www.punoftheday.com/cgi-bin/randompun.pl'
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as r:
            if r.status == 200:
                source = await r.read()
                soup = Bs(source, 'html.parser')

                section = soup.findAll('div', attrs={'class': 'dropshadow1'})
                if len(section) > 0:
                    text = section[0].p.text
            else:
                LOGGER.error('Pun.pun: bad status: %s', r.status)

    if text:
        LOGGER.debug('Pun.pun: response %s', text)
        return Message(message=text)
    else:
        LOGGER.info('Pun.pun: something went wrong.')
        return Message(message='Sorry, but no puns were found.')
