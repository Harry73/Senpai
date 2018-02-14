import asyncio
import discord
import json
import logging
import os
import re
import shutil
from subprocess import Popen, PIPE
import sys

from lib import MessageHandler
from lib import Voice

# Set up logger
LOGGER = logging.getLogger('Senpai')
LOGGER.setLevel(logging.DEBUG)
ch = logging.FileHandler(os.path.join(os.getcwd(), 'Senpai.log'), mode='w')
ch.setFormatter(logging.Formatter('%(asctime)s %(message)s', '%Y-%m-%d %H:%M:%S'))
LOGGER.addHandler(ch)

CONFIG_FILE = os.path.join('json', 'config.json')
TIMING_FILE = os.path.join('json', 'mark.json')
CAN_CLEANUP = True


# Begin!
def main():
    cycle = 0
    while True:
        try:
            # Delete old audio files
            if os.path.isdir('audio_cache'):
                shutil.rmtree('./audio_cache')

            LOGGER.info('Senpai.main: beginning cycle %s', cycle)
            bot = discord.Client()

            # Get discord creds
            with open(CONFIG_FILE, 'r') as f:
                bot.config = json.load(f)

            bot.init_ok = False
            bot.music_player = Voice.Music(bot)

            async def cleanup(messages_to_delete):
                if CAN_CLEANUP:
                    await asyncio.sleep(5)
                    for message_to_delete in messages_to_delete:
                        if message_to_delete.channel and 'Direct Message' not in str(message_to_delete.channel):
                            try:
                                await bot.delete_message(message_to_delete)
                            except discord.errors.Forbidden:
                                    LOGGER.debug('Senpai.main: lacking permissions to complete cleanup')

            async def send_bot_response(message_to_send):
                if message_to_send.message:
                    await bot.wait_until_ready()
                    if len(message_to_send.message) > 2000:
                        return await bot.send_message(message_to_send.channel, 'The result is too big to print.')
                    else:
                        return await bot.send_message(message_to_send.channel, message_to_send.message)

            # Startup task
            @bot.event
            async def on_ready():
                LOGGER.info('Senpai.main: logged in username=%s, id=%s', bot.user.name, bot.user.id)
                LOGGER.info('--------------')
                bot.init_ok = True

            # Look for discord messages and ask MessageHandler to deal with any
            @bot.event
            async def on_message(original_message):
                messages_to_send = await MessageHandler.handle_message(bot, original_message)

                if messages_to_send:
                    messages_to_delete = []

                    should_cleanup_original = False
                    for message_to_send in messages_to_send:
                        if not message_to_send:
                            LOGGER.warning('Senpai.main: blank message in response to "%s"', original_message.content)
                            continue

                        message_to_send.set_channel(original_message.channel)
                        bot_response = await send_bot_response(message_to_send)
                        if message_to_send.cleanup_self:
                            messages_to_delete.append(bot_response)
                        if message_to_send.cleanup_original:
                            should_cleanup_original = True

                    if should_cleanup_original:
                        messages_to_delete.append(original_message)
                    await cleanup(messages_to_delete)

                elif original_message.content.startswith('/'):
                    await cleanup([original_message])

            bot.run(bot.config['discord'])
        except KeyboardInterrupt:
            break
        except Exception as e:
            LOGGER.error('Senpai.main: I died')
            LOGGER.exception(e)
            cycle += 1


# Check python version for 3.5 or better
if __name__ == '__main__':
    if sys.version_info >= (3, 5):
        main()
    else:
        raise Exception('Run with python 3.5 or greater')
