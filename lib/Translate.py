import logging

import aiohttp

from lib.Command import register_command
from lib.Message import Message

LOG = logging.getLogger('Senpai')


@register_command(lambda m: m.content.startswith('/translate'))
async def translate(bot, message):
    """```
    Use jisho.org to translate the given text.

    Usage:
    * /translate <text>
    ```"""

    text = message.content[11:].strip()
    url = 'http://jisho.org/api/v1/search/words?'

    try:
        if text:
            url += 'keyword={0}'.format(text.replace(' ', '+'))
            js = None

            # Fetch json from url
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        js = await r.json()
                    else:
                        LOG.error('bad status, %s', r.status)

            # Get translations from resulting data structure
            if js:
                data = js['data']
                if data:
                    japanese = data[0]['japanese'][0]
                    english = data[0]['senses'][0]['english_definitions']

                    output = ''
                    if 'word' in japanese:
                        output += 'Japanese: {0}\n'.format(japanese['word'])
                    if 'reading' in japanese:
                        output += 'Reading: {0}\n'.format(japanese['reading'])
                    if english:
                        output += 'English: {0}'.format(', '.join(english))
                    return Message(message=output)
                else:
                    return Message(message='No translations found')
        else:
            return Message(message='Usage: /translate <text>')

    except Exception as e:
        LOG.error('Error translating', exc_info=e)
