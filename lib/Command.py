from enum import Enum

from lib import IDs


class CommandType(Enum):
    GENERAL = 1
    VOICE = 2
    CLIP = 3
    OWNER = 4


COMMAND_CONDITIONS = {}
HELP_TEXT = {command_type: {} for command_type in CommandType}


# All registered functions must take two arguments, the Discord bot and the message.
# All registered functions are expected to have a docstring, which is used as the command's help text.
# Registered functions may return a Message, or a list of Messages, that Senpai should send in response.
# "condition" is a lambda that takes a Discord message and returns True if the decorated function should be run.
def register_command(condition, command_type=CommandType.GENERAL, override_name=None, override_help=None):

    # Check if a message is from the owner and check the original condition
    def owner_condition(message):
        return message.author.id == IDs.OWNER_ID and condition(message)

    def wrapper(function):
        command_condition = owner_condition if is_owner_only(command_type) else condition
        COMMAND_CONDITIONS[function] = command_condition

        help_key = override_name or function.__name__
        help_text = override_help or function.__doc__
        help_text = '\n'.join([line.strip() for line in help_text.strip().splitlines()])
        help_dictionary = HELP_TEXT[command_type]
        help_dictionary[help_key] = help_text

        return function

    return wrapper


# Check if a command should only be run by the owner
def is_owner_only(command_type):
    return command_type == CommandType.OWNER


def get_command_conditions():
    return COMMAND_CONDITIONS
