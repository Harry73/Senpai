import json
import logging
import os
import time

from datetime import datetime

from lib import Ids


LOG = logging.getLogger('Senpai')


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

    # Returns if the current time is within the event's defined time window
    def is_time(self):
        time_now = datetime.utcnow()
        tm = time.gmtime()
        time_window_start = time_now
        time_window_end = time_now

        # Check if current time is between given absolute start and end times
        if 'absolute_start' in self.event and 'absolute_end' in self.event:
            start = datetime.strptime(self.event['absolute_start'], Ids.ABSOLUTE_TIME_FORMAT)
            end = datetime.strptime(self.event['absolute_end'], Ids.ABSOLUTE_TIME_FORMAT)
            return start <= time_now <= end

        # Check if today is not the right day
        # Weekday isn't part of datetime.utcnow(), so it is checked against time.gmtime()
        elif 'day' in self.event['time_window_start']:
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

        async with self.LOCK:
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
                    self.cleanup()

            # If the day is out of date, update it and say we haven't completed the event today
            elif self.get_timing_info()['day'] != tm.tm_mday:
                self.write_timing_info(tm.tm_mday, False)

    # Real handlers should override this method
    async def run(self):
        LOG.error('EventHandler "run()" method should never be called')

    # Delete task if necessary
    def cleanup(self):
        if not self.event.get('cleanup'):
            return

        def event_name_matches(event):
            return event['name'] == self.name

        # Remove event entry from events file
        with Ids.FILE_LOCK:
            with open(Ids.EVENTS_FILE, 'r') as f:
                all_events = json.load(f)

            # Keep everything except the event with a matching name
            all_events[:] = [event for event in all_events if not event_name_matches(event)]

            with open(Ids.EVENTS_FILE, 'w') as f:
                json.dump(all_events, f, indent=4)
