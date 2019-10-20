import asyncio
import json
import logging
import pytz
import uuid

from datetime import datetime, timedelta

from lib import Ids
from lib.Command import register_command
from lib.EventHandler import EventHandler
from lib.Message import Message


LOG = logging.getLogger('Senpai')
valid_targets = ['me', 'here', 'everyone']


@register_command(lambda m: m.content.startswith('/remind'))
async def remind(bot, message):
    """```
    Ask Senpai to remind you, or a channel, about something at a given time.
    Times use 24-hour time and assume EST.

    Usages:
    * /remind me at 2019-05-01 08:00 this is my reminder
    * /remind me in 3 days this is my reminder
    * /remind here at 2019-05-01 14:00 this is my reminder
    * /remind here in 7 hours this is my reminder
    ```"""

    new_event = {
        'name': 'remind_{0}'.format(str(uuid.uuid4())),
        'handler': 'reminder',
        'frequency': 'once',  # for flavor, has no real use
        'channel_id': message.channel.id,
        'author_id': message.author.id,
        'cleanup': True,
    }

    pieces = message.content.split(' ')
    if len(pieces) < 6:
        return Message('Not enough arguments provided, see "/senpai remind" for example formats')

    # Figure out where to send the
    target = pieces[1]
    if target not in valid_targets:
        return Message('Invalid target "{0}", must be one of the following: {1}'.format(
            target, ', '.join(valid_targets)))

    new_event['target'] = target

    # Figure out what time to send the reminder
    keyword = pieces[2]
    if keyword == 'at':
        day_minute = ' '.join(pieces[3:5])

        try:
            target_time = datetime.strptime(day_minute, Ids.ABSOLUTE_TIME_FORMAT)
            # Assume given time is in EST, convert to UTC
            est_now = datetime.now(pytz.timezone('US/Eastern'))
            offset = (-1) * est_now.utcoffset().total_seconds() / 3600
            target_time += timedelta(hours=offset)
        except ValueError:
            return Message('Bad date format, expected something like "2019-01-01 01:05"')

        if target_time < datetime.utcnow():
            return Message('Scheduled time for the event, {0}, occurs in the past'.format(day_minute))

    elif keyword == 'in':
        count = pieces[3]

        try:
            n = int(count)
        except ValueError:
            return Message('Non-numeric value for "n"')

        if n <= 0:
            return Message('"n" must be greater than 0')

        period = pieces[4]
        valid_periods = ['months', 'days', 'hours', 'minutes']
        valid_periods_singular = [valid_period[:-1] for valid_period in valid_periods]
        if period not in valid_periods + valid_periods_singular:
            return Message('Invalid period "{0}", must be one of the following: {1}'.format(
                period, ', '.join(valid_periods)))

        if period in valid_periods_singular:
            period = period + 's'

        kwargs = {period: n}
        target_time = datetime.utcnow() + timedelta(**kwargs)

    else:
        return Message('Invalid keyword "{0}", must be one of the following: at, in'.format(keyword))

    new_event['absolute_start'] = datetime.strftime(target_time, Ids.ABSOLUTE_TIME_FORMAT)
    new_event['absolute_end'] = datetime.strftime(target_time + timedelta(minutes=5), Ids.ABSOLUTE_TIME_FORMAT)

    # Rest of the message is the reminder text to send
    reminder = ' '.join(pieces[5:])
    new_event['reminder'] = reminder

    with Ids.FILE_LOCK:
        with open(Ids.EVENTS_FILE, 'r') as f:
            events = json.load(f)

        events.append(new_event)

        with open(Ids.EVENTS_FILE, 'w') as f:
            json.dump(events, f, indent=4)

    return Message('Got it.')


class ReminderEventHandler(EventHandler):
    LOCK = asyncio.Lock()

    # Remind someone, or multiple people, about something.
    # The event, as set up by the remind command, contains all the values needed to send the reminder.
    async def run(self):
        LOG.debug('starting remind task')

        target = self.event.get('target')
        channel_id = self.event.get('channel_id')
        author_id = self.event.get('author_id')
        message = self.event.get('reminder')

        if not target or not channel_id or not author_id or not message:
            LOG.error('Missing event information, target=%s, channel_id=%s, author_id=%s, message=%s',
                      target, channel_id, author_id, message)
            return

        if target not in valid_targets:
            LOG.error('Unrecognized target option, target=%s', target)
            return

        if target == 'me':
            user = self.bot.get_user(author_id)
            target_channel = user.dm_channel
            if not target_channel:
                target_channel = await user.create_dm()
        else:
            target_channel = self.bot.get_channel(channel_id)
            message = '@{0} {1}'.format(target, message)

        await target_channel.send(message)

        LOG.debug('completed remind task')
