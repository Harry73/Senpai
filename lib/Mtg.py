import logging
import re
import string

from mtgsdk import Card

from lib import Ids
from lib.Command import register_command
from lib.Message import Message


LOG = logging.getLogger('Senpai')
SAFE_STRING = set(string.ascii_letters + string.digits + ' ,\|\'"-')
MTG_REGEX = re.compile('\[(?P<card>.*?)\]')


@register_command(lambda m: m.channel.id in Ids.CARD_CHANNELS and m.content.startswith('/card'))
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


@register_command(lambda m: m.channel.id in Ids.CARD_CHANNELS and (
        m.content.startswith('/mtg') or re.findall(MTG_REGEX, m.content)))
async def mtg(bot, message):
    """```
    Searches for a MTG card using the standard API.
    This command only works in specific MTG/Hearthstone channels.

    Usage:
    * /mtg card_name
    * /mtg card_name|set
    * inline [card_name] request
    * inline [card_name|set] request
    ```"""

    # Check for regex match
    matches_mtg = re.findall(MTG_REGEX, message.content)
    search_keys = matches_mtg or [message.content[5:].strip()]

    responses = []
    for search_key in search_keys:
        responses.append(_mtg_find_card(search_key))

    return responses
