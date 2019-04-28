import json
import logging
import os
import requests
import string

from bs4 import BeautifulSoup as Bs
from mtgsdk import Card

from lib import IDs
from lib.Command import register_command
from lib.Message import Message


LOG = logging.getLogger('Senpai')
SAFE_STRING = set(string.ascii_letters + string.digits + ' ,\|\'"-')
HS_FILE = os.path.join('bot_state', 'hs.json')


@register_command(lambda m: m.channel.id in IDs.CARD_CHANNELS and m.content.startswith('/card'))
async def card(bot, message):
    """```
    Provides a link to a search from magiccards.info.
    This command only works in specific MTG/Hearthstone channels.

    Usage:
    * /card card_name
    ```"""

    search_key = message.content[6:].strip()
    search_key = search_key.replace(' ', '+')
    url = 'http://magiccards.info/query?q={0}&v=card&s=cname'.format(search_key)
    return Message(message=url, cleanup_original=False, cleanup_self=False)


# Find link to MTG card using mtgsdk
def _mtg_find_card(search_key):
    if not set(search_key) <= SAFE_STRING:
        LOG.debug('bad characters, early ditch')
        return Message(message='Bad characters in card name. Bother Ian if there is a problem.')

    if '|' in search_key:
        card_name = search_key.split('|')[0]
        set_id = search_key.split('|')[1]
    else:
        card_name = search_key
        set_id = ''

    try:
        cards = Card.where(name=card_name, set=set_id).all()
        cards = [card for card in cards if card.image_url]
        # No exact matches found
        if len(cards) == 0:
            if set_id:
                cards = Card.where(name=card_name).all()
                cards = [card for card in cards if card.image_url]
                if len(cards) == 0:
                    LOG.debug('no match for %s in set %s', search_key, set_id)
                    return Message(message='No match for "{0}"'.format(search_key), cleanup_original=False)
                else:
                    LOG.debug('multiple sets for %s', search_key)
                    sets = set(card.set for card in cards)
                    response_string = 'Possible sets: {0}. Showing {1}\n{2}'.format(
                        ', '.join(sets),
                        cards[-1].set,
                        cards[-1].image_url
                    )
                    return Message(message=response_string, cleanup_original=False, cleanup_self=False)
            else:
                LOG.debug('no match for %s', search_key)
                return Message(message='No match for "{0}"'.format(search_key),
                               cleanup_original=False, cleanup_self=False)
        # One or more matches found
        else:
            for card in cards:
                if search_key.lower() == card.name.lower():
                    return Message(message=card.image_url, cleanup_original=False, cleanup_self=False)
            cards.sort(key=lambda x: 0 if x.multiverse_id is None else x.multiverse_id, reverse=True)
            return Message(message=cards[0].image_url, cleanup_original=False, cleanup_self=False)

    except Exception as e:
        LOG.exception(e)
        return Message(message='Something broke, ask Ian about the card you were looking for',
                       cleanup_original=False, cleanup_self=False)


@register_command(lambda m: m.channel.id in IDs.CARD_CHANNELS and m.content.startswith('/mtg'))
async def mtg(bot, message, override_search_keys=None):
    """```
    Searches for a MTG card using the standard API.
    This command only works in specific MTG/Hearthstone channels.

    Usage:
    * /mtg card_name
    * /mtg card_name|set
    * inline [card_name] request
    * inline [card_name|set] request
    ```"""

    search_keys = override_search_keys or [message.content[5:].strip()]

    responses = []
    for search_key in search_keys:
        responses.append(_mtg_find_card(search_key))

    return responses


@register_command(lambda m: m.channel.id in IDs.CARD_CHANNELS and m.content.startswith('/hs_update'))
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


@register_command(lambda m: m.channel.id in IDs.CARD_CHANNELS and m.content.startswith('/hs'))
async def hs(bot, message, override_search_keys=None):
    """```
    Search local Hearthstone data file for information about a specified card.
    This command only works in specific MTG/Hearthstone channels.

    Usage:
    * /hs card_name
    * inline {card_name} request
    ```"""

    if not os.path.exists(HS_FILE):
        return Message('No local Hearthstone data file found, run "/hs_update" to generate one')

    with open(HS_FILE, 'r') as f:
        data = json.load(f)

    search_keys = override_search_keys or [message.content[4:].strip()]
    responses = []
    for search_key in search_keys:
        responses.append(_hs_find_card(data, search_key))

    return responses

