import logging
from mtgsdk import Card

from lib.Message import Message
from lib import IDs

LOGGER = logging.getLogger("Senpai")


# Find link to MTG card using magiccards.info queries
async def find_card(channel_id, search_key):
    if channel_id in IDs.MTG_CHANNELS:
        LOGGER.debug("MCI: Looking up '%s'", search_key)
        try:
            search_key = search_key.replace(" ", "+")
            url = "http://magiccards.info/query?q={0}&v=card&s=cname"
            return Message(message=url.format(search_key), cleanup_original=False, cleanup_self=False)
        except Exception as e:
            LOGGER.exception("Error: {0}".format(e))


# Find link to MTG card using mtgsdk
def mtg_find_card(search_key):
    LOGGER.debug("MTG: Looking up '%s'", search_key)

    if "|" in search_key:
        card_name = search_key.split("|")[0]
        set_id = search_key.split("|")[1]
    else:
        card_name = search_key
        set_id = ""

    try:
        cards = Card.where(name=card_name, set=set_id).all()
        if len(cards) == 0:
            if set_id:
                cards = Card.where(name=card_name).all()
                if len(cards) == 0:
                    return Message(message="Couldn't find a card for '{0}'".format(search_key), cleanup_original=False)
                else:
                    sets = set(card.set for card in cards)
                    response_string = "Possible sets: {0}. Showing {1}\n{2}".format(
                        ", ".join(sets),
                        cards[-1].set,
                        cards[-1].image_url
                    )
                    return Message(message=response_string, cleanup_original=False, cleanup_self=False)
            else:
                return Message(
                    message="Couldn't find a card for '{0}'".format(search_key),
                    cleanup_original=False,
                    cleanup_self=False
                )
        else:
            return Message(message=cards[-1].image_url, cleanup_original=False, cleanup_self=False)

    except Exception as e:
        LOGGER.exception("Error: {0}".format(e))
        return Message(message="Something broke :(", cleanup_original=False, cleanup_self=False)


async def mtg_find_cards(channel_id, search_keys):
    if channel_id in IDs.MTG_CHANNELS:
        response_messages = []
        for search_key in search_keys:
            response_messages.append(mtg_find_card(search_key))

        return response_messages
