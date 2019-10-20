import json
import logging
import os
import re
import requests

from bs4 import BeautifulSoup as Bs

from lib import Ids
from lib.Command import register_command
from lib.Message import Message


LOG = logging.getLogger('Senpai')
HS_FILE = os.path.join('bot_state', 'hs.json')
HS_REGEX = re.compile('\{(?P<card>.*?)\}')


@register_command(lambda m: m.channel.id in Ids.CARD_CHANNELS and m.content.startswith('/hs_update'))
async def hs_update(bot, message):
    """```
    Download the newest data set of Hearthstone cards.
    This command only works in specific MTG/Hearthstone channels.

    Usage:
    * /hs_update
    ```"""

    base_api_url = 'https://api.hearthstonejson.com/v1'
    error_message = Message(message='Error querying hearthstone api', cleanup_original=False)
    r = requests.get(base_api_url)
    if r.status_code != 200:
        LOG.error('error fetching versions from %s, status_code=%s', base_api_url, r.status_code)
        return error_message

    versions = []
    soup = Bs(r.content, 'html.parser')
    for a in soup.findAll('a'):
        href = a.get('href')
        try:
            pieces = href.split('/')
            if len(pieces) >= 3:
                version = int(pieces[2])
                versions.append(version)
        except ValueError:
            pass

    if not versions:
        return error_message

    api_url = '{0}/{1}/enUS/cards.json'.format(base_api_url, max(versions))
    r = requests.get(api_url)
    if r.status_code != 200:
        LOG.error('error fetching cards.json from %s, status_code=%s', api_url, r.status_code)
        return error_message

    try:
        json_data = r.json()
        with open(HS_FILE, 'w') as f:
            json.dump(json_data, f)
    except json.JSONDecodeError:
        LOG.error('error parsing cards.json')
        return error_message

    return Message('Updated successfully')


# Find link to Hearthstone card using the given data
def _hs_find_card(data, search_key):
    base_image_url = 'https://art.hearthstonejson.com/v1/render/latest/enUS/512x/{0}.png'

    near_matches = []
    for crd in data:
        if 'name' not in crd or 'id' not in crd:
            continue

        if crd['name'].lower() == search_key.lower():
            return Message(message=base_image_url.format(crd['id']), cleanup_original=False, cleanup_self=False)

        if crd['name'].lower().startswith(search_key):
            near_matches.append(crd)

    if near_matches:
        image_url = base_image_url.format(near_matches[0].get('id'))
        return Message(message='Multiple matches found, showing first\n{0}'.format(image_url),
                       cleanup_original=False, cleanup_self=False)

    return Message(message='No match found for {0}'.format(search_key), cleanup_original=False)


@register_command(lambda m: m.channel.id in Ids.CARD_CHANNELS and (
        m.content.startswith('/hs') or re.findall(HS_REGEX, m.content)))
async def hs(bot, message):
    """```
    Search local Hearthstone data file for information about a specified card.
    This command only works in specific MTG/Hearthstone channels.

    Usage:
    * /hs card_name
    * inline {card_name} request
    ```"""

    if not os.path.exists(HS_FILE):
        return Message('No local Hearthstone data file found, run "/hs_update" to generate one', cleanup_original=False)

    with open(HS_FILE, 'r') as f:
        data = json.load(f)

    # Check for regex match
    matches_hs = re.findall(HS_REGEX, message.content)
    search_keys = matches_hs or [message.content[4:].strip()]
    responses = []
    for search_key in search_keys:
        responses.append(_hs_find_card(data, search_key))

    return responses
