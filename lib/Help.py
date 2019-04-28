from lib import Command
from lib.Command import CommandType, register_command
from lib.Message import Message


def _get_help(request, author, channel, command_types, base_command):
    # Generate list of all available commands
    commands = {}
    for command_type in command_types:
        for command, help_text in Command.HELP_TEXT[command_type].items():
            commands[command] = help_text

    responses = []

    if not request:
        # Compile default help text
        help_text = '```'
        help_text += 'Use /{0} <command> for more information about a command.\n\n'.format(base_command)
        for command_type in command_types:
            # Skip reporting the clips, they make the help text too large
            if command_type == CommandType.CLIP:
                continue

            help_text += '{0} commands: \n{1}\n\n'.format(
                command_type.name.capitalize(),
                ', '.join(sorted(['/{0}'.format(command) for command in Command.HELP_TEXT[command_type]]))
            )
        help_text += '```'

        responses.append(Message(
            message=help_text,
            channel=author,
            cleanup_original=False,
            cleanup_self=False
        ))

    else:
        if request not in commands:
            return Message(
                message='No {0} command'.format(request),
                channel=author,
                cleanup_original=False,
                cleanup_self=False
            )

        responses.append(Message(
            message=commands[request],
            channel=author,
            cleanup_original=False,
            cleanup_self=False
        ))

    if 'Direct Message' not in str(channel) and responses:
        responses.append(Message(message='Sent you a DM.'))

    return responses


@register_command(lambda m: m.content.startswith('/senpai'))
async def senpai(bot, message):
    """```
    Senpai's help function. Responses will be PM'd.

    Usages:
    * /senpai            -> gives a list of available commands
    * /senpai command    -> gives information about a specific command
    ```"""

    return _get_help(message.content[8:].strip(), message.author, message.channel,
                     [CommandType.GENERAL, CommandType.VOICE, CommandType.CLIP], 'senpai')


@register_command(lambda m: m.content.startswith('/secrets'), command_type=CommandType.OWNER)
async def secrets(bot, message):
    """```
    List Senpai's owner-only commands. Responses will be PM'd.

    Usage:
    * /secrets
    ```"""

    return _get_help(message.content[9:].strip(), message.author, message.channel,
                     [CommandType.OWNER], 'secrets')
