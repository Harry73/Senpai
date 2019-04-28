import asyncio
import discord
import json
import logging
import os
import shutil
import sys
import threading

from lib import Events
from lib import IDs
from lib import MessageHandler
from lib import Voice


# Save old log file, if it exists
if os.path.exists('Senpai.log'):
    os.rename('Senpai.log', 'Senpai.log_old')

# Set up logger
LOG = logging.getLogger('Senpai')
LOG.setLevel(logging.DEBUG)
ch = logging.FileHandler(os.path.join(os.getcwd(), 'Senpai.log'), mode='w')
ch.setFormatter(logging.Formatter('%(asctime)s - %(module)s: %(message)s', '%Y-%m-%d %H:%M:%S'))
LOG.addHandler(ch)

AUDIO_CACHE_DIR = 'audio_cache'
REQUIRED_DIRS = ['event_state', 'bot_state']
CONFIG_FILE = os.path.join('json', 'config.json')
DND_TRACKING_FILE = os.path.join('event_state', 'dnd_latest.json')
CAN_CLEANUP = True


def main():

    # Create necessary directories
    for directory in REQUIRED_DIRS:
        if not os.path.exists(directory):
            os.makedirs(directory)

    bot = None

    try:
        LOG.info('startup')

        # Delete old audio files
        if os.path.isdir(AUDIO_CACHE_DIR):
            shutil.rmtree('./{0}'.format(AUDIO_CACHE_DIR))

        bot = discord.Client()

        # Get discord credentials
        with open(CONFIG_FILE, 'r') as f:
            bot.config = json.load(f)

        # Set up variables under "bot" that are used elsewhere in the implementation
        bot.downloader = Voice.Downloader(download_folder=AUDIO_CACHE_DIR)
        bot.voice_states = {}
        bot.tracking = {
            IDs.NAMES_TO_CHANNELS['dnd']: DND_TRACKING_FILE,
        }

        # Startup task
        @bot.event
        async def on_ready():
            LOG.info('logged in username=%s, id=%s', bot.user.name, bot.user.id)

            # Create separate thread for scheduled events
            t = threading.Thread(target=Events.timing, args=(bot,))
            t.daemon = True
            t.start()

        # Attempt to clean up the original message and Senpai's response(s)
        async def cleanup(messages_to_delete):
            if CAN_CLEANUP:
                await asyncio.sleep(5)
                for message_to_delete in messages_to_delete:
                    if message_to_delete.channel and 'Direct Message' not in str(message_to_delete.channel):
                        try:
                            await bot.delete_message(message_to_delete)
                        except discord.errors.Forbidden:
                            LOG.debug('lacking permissions to complete cleanup')
                        except discord.errors.NotFound:
                            LOG.debug('ignoring failure, message missing when cleaning up')

        # Send a message, with a little safety checking
        async def send_response(message_to_send):
            if message_to_send.message:
                await bot.wait_until_ready()
                if len(message_to_send.message) > 2000:
                    return await bot.send_message(message_to_send.channel,
                                                  'My response was too big to send, ask Ian about this')
                else:
                    return await bot.send_message(message_to_send.channel, message_to_send.message)

        # Watch for discord messages and ask MessageHandler to deal with any
        @bot.event
        async def on_message(original_message):
            messages_to_send = await MessageHandler.handle_message(bot, original_message)

            if messages_to_send:
                messages_to_delete = []

                should_cleanup_original = False
                for message_to_send in messages_to_send:
                    if not message_to_send:
                        LOG.warning('blank message in response to "%s"', original_message.content)
                        continue

                    message_to_send.set_channel(original_message.channel)
                    bot_response = await send_response(message_to_send)
                    if message_to_send.cleanup_self:
                        messages_to_delete.append(bot_response)
                    if message_to_send.cleanup_original:
                        should_cleanup_original = True

                if should_cleanup_original:
                    messages_to_delete.append(original_message)
                await cleanup(messages_to_delete)

            elif original_message.content.startswith('/'):
                await cleanup([original_message])

        # Run the bot
        bot.run(bot.config['discord'])

    except KeyboardInterrupt:
        if bot:
            bot.logout()

    except Exception as e:
        if bot:
            bot.logout()
        LOG.error('I died')
        LOG.exception(e)

    sys.exit(1)


# Check python version for 3.5 or better
if __name__ == '__main__':
    if sys.version_info >= (3, 5):
        main()
    else:
        raise Exception('Run with python 3.5 or greater')
