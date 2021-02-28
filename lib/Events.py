import json
import logging
import time

from lib import Ids
from lib.DnD import DndPingEventHandler, DndBotherEventHandler
from lib.Reminder import ReminderEventHandler


LOG = logging.getLogger('Senpai')


# Keep track of timing for scheduled events
def timing(bot):
    while True:
        with Ids.FILE_LOCK:
            with open(Ids.EVENTS_FILE, 'r') as f:
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
    if event['handler'] == 'dnd_ping':
        handler = DndPingEventHandler(event, bot)
    elif event['handler'] == 'dnd_bother':
        handler = DndBotherEventHandler(event, bot)
    elif event['handler'] == 'reminder':
        handler = ReminderEventHandler(event, bot)

    if not handler:
        LOG.error('Event %s has unrecognized handler %s', event['name'], event['handler'])
        return

    bot.loop.create_task(handler.handle())
