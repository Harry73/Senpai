import shlex
import subprocess

from lib.Command import CommandType, register_command
from lib.Message import Message


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

    Usgae:
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
