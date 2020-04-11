import asyncio
import json
import logging
import math
import os
import time

from datetime import datetime, timedelta

from lib import Ids
from lib.Command import CommandType, register_command
from lib.EventHandler import EventHandler

LOG = logging.getLogger('Senpai')


# Global since it's used by two events
CAMPAIGNS = [
    {
        'name': 'Singularity',
        'players': ['adam', 'ian', 'dan', 'ravi', 'nevil', 'sanjay'],
    },
    {
        'name': 'End\'s Respite',
        'players': ['dan', 'adam', 'nevil', 'ian', 'matt'],
    },
    {
        'name': 'Dark Tides',
        'players': ['nevil', 'ian', 'matt', 'adam', 'sanjay', 'dan', 'jason', 'steve'],
    },
    {
        'name': 'Zenith',
        'players': ['adam', 'ahasan', 'steve', 'matt', 'jason'],
    },
]

DND_CHANNEL = 'dnd'

PING_CYCLE = [
    ['Singularity', 'Dark Tides'],
    ['End\'s Respite', 'Singularity'],
    ['Singularity', 'Dark Tides'],
    ['Dark Tides', 'End\'s Respite'],
]

PING_CYCLE_OFFSET_FILE = os.path.join('bot_state', 'dnd_cycle_offset.json')


@register_command(lambda m: m.content.startswith('/set_offset'), command_type=CommandType.OWNER)
async def set_offset(bot, message):
    """```
    Set the offset for the DnD ping cycle.

    Usage:
    * /set_offset N
    ```"""

    new_offset = message.content[12:].strip()

    try:
        new_offset = int(new_offset)
    except ValueError:
        pass

    with open(PING_CYCLE_OFFSET_FILE, 'w') as f:
        json.dump(new_offset, f)


class DndEventHandler(EventHandler):
    @staticmethod
    def get_campaign(name):
        for campaign in CAMPAIGNS:
            if campaign['name'].lower() == name.lower():
                return campaign

        raise Exception('Campaign {} not found'.format(name))


class DndPingEventHandler(DndEventHandler):
    LOCK = asyncio.Lock()

    # Ping for all players in this week's campaigns once
    async def run(self):
        LOG.debug('starting ping task')
        if not os.path.exists(PING_CYCLE_OFFSET_FILE):
            with open(PING_CYCLE_OFFSET_FILE, 'w') as f:
                f.write('0')

        with open(PING_CYCLE_OFFSET_FILE, 'r') as f:
            ping_cycle_offset = int(f.read())

        ping_string = '{mentions}: When are you available this week for {name}?'
        week_num = math.floor(((time.time() / (60 * 60 * 24 * 7)) + ping_cycle_offset) % len(PING_CYCLE))
        week_cycle = PING_CYCLE[week_num]
        campaign_string = '/'.join(week_cycle)
        channel = self.bot.get_channel(Ids.NAMES_TO_CHANNELS[DND_CHANNEL])

        # Collect campaign dicts
        campaigns = []
        for campaign_name in week_cycle:
            campaigns.append(self.get_campaign(campaign_name))

        # Collect players in campaigns
        players = []
        for campaign in campaigns:
            players.extend(campaign['players'])

        # Convert players to mentions, removing duplicates
        mentions = []
        for player in set(players):
            user = self.bot.get_user(Ids.NAMES_TO_USERS[player])
            mentions.append(user.mention)

        if mentions:
            await channel.send(ping_string.format(mentions=' '.join(mentions), name=campaign_string))

        LOG.debug('ping cycle message sent')


class DndBotherEventHandler(DndEventHandler):
    LOCK = asyncio.Lock()

    # Ping any players in this week's campaigns again if they haven't said anything recently
    async def run(self):
        LOG.debug('starting bother task')

        bother_string = '{mentions}: Pinging again for {name}, what\'s your availability this week?'
        week_num = math.floor((time.time() / (60 * 60 * 24 * 7)) % len(PING_CYCLE))
        week_cycle = PING_CYCLE[week_num]
        campaign_string = '/'.join(week_cycle)
        channel = self.bot.get_channel(Ids.NAMES_TO_CHANNELS[DND_CHANNEL])

        # Collect campaign dicts
        campaigns = []
        for campaign_name in week_cycle:
            campaigns.append(self.get_campaign(campaign_name))

        # Collect players in campaigns
        players = []
        for campaign in campaigns:
            players.extend(campaign['players'])

        # Convert to user ids
        users = []
        for player in players:
            user = self.bot.get_user(Ids.NAMES_TO_USERS[player])
            users.append(user.id)

        # Get tracking info in datetime objects
        channel_tracking = {}
        channel_tracking_file = self.bot.tracking[channel]
        with open(channel_tracking_file, 'r') as f:
            channel_tracking_strings = json.load(f)
        for user, last_message_time in channel_tracking_strings.items():
            channel_tracking[user] = datetime.strptime(last_message_time, '%Y-%m-%d %H:%M:%S.%f')

        # Check which users haven't posted in the channel in the last day
        now = datetime.utcnow()
        mentions = []
        for user, last_message_time in channel_tracking.items():
            if now > last_message_time + timedelta(days=1):
                member = self.bot.get_user(Ids.NAMES_TO_USERS[user])
                mentions.append(member.mention)

        if mentions:
            await channel.send(bother_string.format(mentions=' '.join(mentions), name=campaign_string))

        LOG.debug('completed bother task')
