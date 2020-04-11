import shlex
import subprocess

from lib.Command import CommandType, register_command
from lib.Message import Message


@register_command(lambda m: m.content.startswith('/kick'), command_type=CommandType.OWNER)
async def kick(bot, message):
    """```
    Stop Senpai.

    Usage:
    * /kick user_name
    ```"""

    user = message.guild.get_member_named(message.content.split(' ')[1])
    await message.guild.kick(user)


@register_command(lambda m: m.content.startswith('/rename'), command_type=CommandType.OWNER)
async def rename(bot, message):
    """```
    Stop Senpai.

    Usage:
    * /rename current_name new_nick
    ```"""

    pieces = message.content.split(' ')
    user = message.guild.get_member(int(pieces[1]))
    await user.edit(nick=pieces[2])


@register_command(lambda m: m.content.startswith('/send'), command_type=CommandType.OWNER)
async def send(bot, message):
    """```
    Send a message as Senpai to a channel.

    Usage:
    * /send <channel_id> <message>
    ```"""

    pieces = message.content.split(' ')
    channel = int(pieces[1])
    message_to_send = ' '.join(pieces[2:])
    channel = bot.get_channel(channel)
    await channel.send(message_to_send)


@register_command(lambda m: m.content.startswith('/update'), command_type=CommandType.OWNER)
async def update(bot, message):
    """```
    Update pip libraries.

    Usage:
    * /update
    * /update <library>
    ```"""

    pieces = message.content.strip().split(' ')
    library = pieces[1] if len(pieces) > 1 else 'youtube_dl'
    command = 'sudo pip install -U {}'.format(library)
    subprocess.Popen(shlex.split(command)).communicate()
    return Message('Done')


# Stops the pm2 process that is used to run the bot, thus killing the bot on command
@register_command(lambda m: m.content.startswith('/sudoku'), command_type=CommandType.GENERAL)
async def sudoku(bot, message):
    """```
    Stop Senpai.

    Usage:
    * /sudoku
    ```"""

    await bot.logout()
    subprocess.call(['pm2', 'stop', 'Senpai'])


@register_command(lambda m: m.content.startswith('/restart'), command_type=CommandType.GENERAL)
async def restart(bot, message):
    """```
    Restart Senpai.

    Usage:
    * /sudoku
    ```"""

    await bot.logout()
    subprocess.call(['pm2', 'restart', 'Senpai'])


@register_command(lambda m: m.content.startswith('/cmd'), command_type=CommandType.OWNER)
async def cmd(bot, message):
    """```
    Run an arbitrary command on the server Senpai runs on.

    Usage:
    * /cmd sudo yum -y update
    ```"""

    pieces = message.content.strip().split(' ')
    if len(pieces) < 2:
        return

    command = ' '.join(pieces[1:])
    stdout, stderr = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()

    if stderr or stdout:
        return Message('```Output: {1}\n\nError: {0}```'.format(stdout, stderr))
