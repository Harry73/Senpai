import aiohttp
import logging

from bs4 import BeautifulSoup as Bs

from lib.Message import Message
from lib.Command import register_command

LOG = logging.getLogger('Senpai')


# Poll http://www.punoftheday.com/cgi-bin/randompun.pl for a random pun
@register_command(lambda m: m.content == '/pun')
async def pun(bot, message):
    """```
    Say a pun.

    Usage:
    * /pun
    ```"""

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
                LOG.error('Pun.pun: bad status: %s', r.status)

    if text:
        return Message(message=text)
    else:
        LOG.info('something went wrong.')
        return Message(message='Sorry, but no puns were found.')
