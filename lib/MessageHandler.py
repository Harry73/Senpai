import json
import logging
import os
import re

from datetime import datetime

# These all need to be imported so that the command list is built
from lib import Card
from lib import Cat
from lib import Command
from lib import Dice
from lib import IDs
from lib import Help
from lib import Names
from lib import Profile
from lib import Pun
from lib import Purge
from lib import React
from lib import Secrets
from lib import Spyfall
from lib import Translate
from lib import Voice

LOG = logging.getLogger('Senpai')
MTG_REGEX = re.compile('\[(?P<card>.*?)\]')
HS_REGEX = re.compile('\{(?P<card>.*?)\}')
COMMAND_CONDITIONS = Command.get_command_conditions()


def update_trackers(bot, original_message):
    for channel, file in bot.tracking.items():
        if original_message.channel.id == channel:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    history = json.load(f)
            else:
                history = {}

            history[original_message.author.id] = str(datetime.utcnow())

            with open(file, 'w') as f:
                json.dump(history, f)


async def handle_message(bot, original_message):
    response = None

    if original_message.author.id == IDs.SENPAI_ID:
        return

    # Update tracking files
    update_trackers(bot, original_message)

    # Check functions auto-collected by @register_command
    for function, condition in COMMAND_CONDITIONS.items():
        if condition(original_message):
            LOG.debug('request, channel %s, author %s, content %s', original_message.channel,
                      original_message.author, original_message.content)
            response = await function(bot, original_message)
            break

    # Search for regex matches
    matches_mtg = re.findall(MTG_REGEX, original_message.content)
    matches_hs = re.findall(HS_REGEX, original_message.content)
    if matches_mtg:
        LOG.debug('regex request, channel %s, author %s, content %s', original_message.channel,
                  original_message.author, original_message.content)
        response = await Card.mtg(bot, original_message, override_search_keys=matches_mtg)
    elif matches_hs:
        LOG.debug('regex request, channel %s, author %s, content %s', original_message.channel,
                  original_message.author, original_message.content)
        response = await Card.hs(bot, original_message, override_search_keys=matches_hs)

    if response:
        LOG.debug('responses, %s', response)

    if isinstance(response, list):
        return response
    elif response:
        return [response]
    else:
        return None
