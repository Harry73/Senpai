import asyncio
import discord
import json
import logging
import math
import os
import praw
import time

from datetime import datetime, timedelta

from lib import IDs
from lib.Command import CommandType, register_command

LOG = logging.getLogger('Senpai')
EVENTS_FILE = os.path.join('json', 'events.json')

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
        'players': ['nevil', 'ian', 'matt', 'adam', 'sanjay', 'dan', 'jason'],
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
if not os.path.exists(PING_CYCLE_OFFSET_FILE):
    with open(PING_CYCLE_OFFSET_FILE, 'w') as file:
        json.dump(0, file)


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


# Periodically check if any events should be run
def timing(bot):
    while True:
        with open(EVENTS_FILE, 'r') as f:
            events = json.load(f)

        for event in events:
            handle_event(event, bot)

        time.sleep(5)


# Create a handler based on event['handler'] and run handle()
def handle_event(event, bot):
    if 'handler' not in event:
        LOG.error('Event %s does not have a handler defined', event['name'])
        return

    handler = None
    elif event['handler'] == 'dnd_ping':
        handler = DndPingEventHandler(event, bot)
    elif event['handler'] == 'dnd_bother':
        handler = DndBotherEventHandler(event, bot)

    if not handler:
        LOG.error('Event %s has unrecognized handler %s', event['name'], event['handler'])
        return

    bot.loop.create_task(handler.handle())


# Parent event handler class that does the work of determining if an event should be run based on their defined windows.
# Subclass this and override run() to define what a scheduled task should do.
class EventHandler:
    LOCK = None

    def __init__(self, event, bot):
        self.event = event
        self.bot = bot
        self.name = event['name']

    # Returns a path to the timing file for the event
    def get_timing_file(self):
        return os.path.join(os.path.join('event_state', '{0}_event.json'.format(self.event['name'])))

    # Returns the contents of the timing file for the event, or a default dict if the file does not exist
    def get_timing_info(self):
        timing_file = self.get_timing_file()

        if os.path.isfile(timing_file):
            with open(timing_file, 'r') as f:
                timing_info = json.load(f)
        else:
            timing_info = {'day': 0, 'posted': False}

        return timing_info

    # Returns if the current time is within the event's defined time window, i.e. the event should be run now
    def is_time(self):
        time_now = datetime.utcnow()
        tm = time.gmtime()
        time_window_start = time_now
        time_window_end = time_now

        # Weekday isn't part of datetime.utcnow(), so it is checked against time.gmtime()
        if 'day' in self.event['time_window_start']:
            day_start = self.event['time_window_start']['day']
            day_end = self.event['time_window_end']['day']
            if not (day_start <= tm.tm_wday <= day_end):
                return False

        # For hour/minute, build a time window from datetime objects
        if 'hour' in self.event['time_window_start']:
            time_window_start = time_window_start.replace(hour=self.event['time_window_start']['hour'])
            time_window_end = time_window_end.replace(hour=self.event['time_window_end']['hour'])
        if 'minute' in self.event['time_window_start']:
            time_window_start = time_window_start.replace(minute=self.event['time_window_start']['minute'])
            time_window_end = time_window_end.replace(minute=self.event['time_window_end']['minute'])

        time_window_start = time_window_start.replace(second=0, microsecond=0)
        time_window_end = time_window_end.replace(second=0, microsecond=0)

        return time_window_start <= time_now <= time_window_end

    # Returns whether or not the event has already completed today
    def has_posted_today(self):
        timing_info = self.get_timing_info()
        tm = time.gmtime()
        return timing_info['posted'] and timing_info['day'] == tm.tm_mday

    # Updates timing file for the event
    def write_timing_info(self, day, success):
        mark = {'day': day, 'posted': success}

        timing_file = self.get_timing_file()
        with open(timing_file, 'w') as f:
            json.dump(mark, f)

    # Checks if anything should be run right now for the event, and schedules the task if necessary
    async def handle(self):
        # Synchronization lock is required to prevent multiple events of the same type from running simultaneously.
        # Each subclass defines a static lock for that purpose.
        if not self.LOCK:
            return

        try:
            await self.LOCK.acquire()

            tm = time.gmtime()
            # If we are in the time window and we haven't successfully completed the event today, try the event
            if self.is_time() and not self.has_posted_today():
                try:
                    LOG.debug('day %s, hour %s, minute %s, scheduled %s task',
                              tm.tm_mday, tm.tm_hour, tm.tm_min, self.name)
                    task = self.bot.loop.create_task(self.run())
                    await task
                except Exception as e:
                    LOG.exception('task %s failed to run at %s.\nError: %s',
                                  self.name, tm, e)
                else:
                    # Mark event as successful if there were no errors
                    self.write_timing_info(tm.tm_mday, True)
                    LOG.debug('marked task %s as successful', self.name)

            # If the day is out of date, update it and say we haven't completed the event today
            elif self.get_timing_info()['day'] != tm.tm_mday:
                self.write_timing_info(tm.tm_mday, False)

        finally:
            self.LOCK.release()

    # Real handlers should override this method
    async def run(self):
        LOG.error('EventHandler "run()" method should never be called')


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
        LOG.info('starting ping task')
        with open(PING_CYCLE_OFFSET_FILE, 'r') as f:
            ping_cycle_offset = json.load(f)

        ping_string = '{mentions}: When are you available this week for {name}?'
        week_num = math.floor(((time.time() / (60 * 60 * 24 * 7)) + ping_cycle_offset) % len(PING_CYCLE))
        week_cycle = PING_CYCLE[week_num]
        campaign_string = '/'.join(week_cycle)
        channel = self.bot.get_channel(IDs.NAMES_TO_CHANNELS[DND_CHANNEL])

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
            user = await self.bot.get_user_info(IDs.NAMES_TO_USERS[player])
            mentions.append(user.mention)

        if mentions:
            await self.bot.send_message(channel, ping_string.format(mentions=' '.join(mentions), name=campaign_string))
        
        LOG.info('ping cycle message sent')


class DndBotherEventHandler(DndEventHandler):
    LOCK = asyncio.Lock()

    # Ping any players in this week's campaigns again if they haven't said anything recently
    async def run(self):
        LOG.info('starting bother task')

        bother_string = '{mentions}: Pinging again for {name}, what\'s your availability this week?'
        week_num = math.floor((time.time() / (60 * 60 * 24 * 7)) % len(PING_CYCLE))
        week_cycle = PING_CYCLE[week_num]
        campaign_string = '/'.join(week_cycle)
        channel = self.bot.get_channel(IDs.NAMES_TO_CHANNELS[DND_CHANNEL])

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
            user = await self.bot.get_user_info(IDs.NAMES_TO_USERS[player])
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
                member = await self.bot.get_user_info(IDs.NAMES_TO_USERS[user])
                mentions.append(member.mention)

        if mentions:
            await self.bot.send_message(channel,
                                        bother_string.format(mentions=' '.join(mentions), name=campaign_string))

        LOG.info('completed bother task')
