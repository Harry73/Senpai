import json
import logging
import os

from datetime import datetime

# These all need to be imported so that the command list is built
from lib import Cat
from lib import Command
from lib import Dice
from lib import DnD
from lib import Ids
from lib import Hearthstone
from lib import Help
from lib import Management
from lib import Mtg
from lib import Names
from lib import Profile
from lib import Pun
from lib import Purge
from lib import React
from lib import Reminder
from lib import Spyfall
from lib import Translate
from lib import Voice


LOG = logging.getLogger('Senpai')
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

    if original_message.author.id == Ids.SENPAI_ID:
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

    if response:
        LOG.debug('responses, %s', response)

    if isinstance(response, list):
        return response
    elif response:
        return [response]
    else:
        return None
