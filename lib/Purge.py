from lib import IDs
from lib.Command import CommandType, register_command
from lib.Message import Message


@register_command(lambda m: m.content.startswith('/purge'), command_type=CommandType.OWNER)
async def purge(bot, message):
    """```
    Delete prior commands and messages from Senpai from a channel.

    Usage:
    * /purge N
    ```"""

    channel = message.channel
    count = message.content[6:].strip()

    if 'Direct Message' in str(channel):
        return Message('Cannot purge DMs')

    try:
        limit = int(count)
    except ValueError:
        return Message('non-numeric purge value')

    if limit < 1:
        return Message('non-positive purge value')

    if limit > 100:
        limit = 100

    def delete_condition(msg):
        return msg.author.id == IDs.SENPAI_ID or msg.content.startswith('/')

    await bot.purge_from(channel, limit=limit, check=delete_condition)
