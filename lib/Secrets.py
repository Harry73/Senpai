from subprocess import call

from lib.Command import CommandType, register_command


# Stops the pm2 process that is used to run the bot, thus killing the bot on command
@register_command(lambda m: m.content.startswith('/sudoku'), command_type=CommandType.OWNER)
async def sudoku(bot, message):
    """```
    Stop Senpai.

    Usage:
    * /sudoku
    ```"""

    await bot.logout()
    call(['pm2', 'stop', 'Senpai'])


@register_command(lambda m: m.content.startswith('/restart'), command_type=CommandType.OWNER)
async def restart(bot, message):
    """```
    Restart Senpai.

    Usage:
    * /sudoku
    ```"""

    await bot.logout()
    call(['pm2', 'restart', 'Senpai'])
