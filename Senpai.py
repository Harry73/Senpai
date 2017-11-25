import os
import re
import sys
import time
import json
import asyncio
import shutil
import logging
import discord
from subprocess import Popen, PIPE
from threading import Thread

from lib import MessageHandler
from lib import Voice

# Set up logger
LOGGER = logging.getLogger("Senpai")
LOGGER.setLevel(logging.DEBUG)
ch = logging.FileHandler(os.path.join(os.getcwd(), "Senpai.log"), mode="w")
ch.setLevel(logging.DEBUG)
LOGGER.addHandler(ch)

CAN_CLEANUP = True
SPECIAL_CLEANUP_REGEX = re.compile("/(summon|play|skip|pause|stop|gtfo).*")


# Begin!
def main():
    cycle = 0
    while True:
        try:
            # Delete old audio files
            if os.path.isdir("audio_cache"):
                shutil.rmtree("./audio_cache")

            LOGGER.info("Beginning cycle {0}".format(cycle))
            bot = discord.Client()

            # Get discord creds
            with open("Config.json", "r") as f:
                bot.config = json.load(f)

            bot.init_ok = False
            bot.music_player = Voice.Music(bot)

            async def cleanup(messages_to_delete):
                if CAN_CLEANUP:
                    await asyncio.sleep(5)
                    for message_to_delete in messages_to_delete:
                        try:
                            await bot.delete_message(message_to_delete)
                        except discord.errors.Forbidden:
                                LOGGER.warning("Lacking permissions to complete cleanup")

            async def send_bot_response(message_to_send):
                if message_to_send.message:
                    await bot.wait_until_ready()
                    return await bot.send_message(message_to_send.channel, message_to_send.message)

            # Startup task
            @bot.event
            async def on_ready():
                LOGGER.info("Logged in as:")
                LOGGER.info(bot.user.name)
                LOGGER.info(bot.user.id)
                LOGGER.info("--------------")
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
                            LOGGER.warning("Blank message in response to '{0}'".format(original_message.content))
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

                elif SPECIAL_CLEANUP_REGEX.match(original_message.content):
                    await cleanup([original_message])

            bot.run(bot.config["discord"]["email"], bot.config["discord"]["pass"])
        except KeyboardInterrupt:
            break
        except Exception as e:
            LOGGER.error("I died")
            LOGGER.exception(e)
            cycle += 1


# Check python version for 3.5 or better
if __name__ == "__main__":
    if sys.version_info >= (3, 5):
        main()
    else:
        raise Exception("Run with python 3.5 or greater")
