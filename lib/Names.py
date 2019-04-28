import json
import os

from lib.Command import register_command
from lib.Message import Message


NAMES_FILE = os.path.join('bot_state', 'names.json')


# Say hi to the user, and use the nickname they've chosen
@register_command(lambda m: m.content == '/hi')
async def hi(bot, message):
    """```
    Senpai says hi to you by name, if she knows your name. Use /callme to set your name.

    Usage:
    * /hi
    ```"""

    author_id = message.author.id

    if os.path.isfile(NAMES_FILE):
        with open(NAMES_FILE, 'r') as f:
            names = json.load(f)

        if author_id in names:
            return Message(message='Hi {0}.'.format(names[author_id]))
        else:
            return Message(message='Hi. I don\'t have a name for you, use /callme <name> to pick your name.')
    else:
        with open(NAMES_FILE, 'w') as f:
            f.write('{}')
        return Message(message='Hi. I don\'t have a name for you, use /callme <name> to pick your name.')


# Update names.txt with the new nickname
@register_command(lambda m: m.content.startswith('/callme'))
async def callme(bot, message):
    """```
    In the future, Senpai will call you whatever name you provide. Use /hi to check your name.

    /callme name
    ```"""

    author_id = message.author.id
    new_name = message.content[8:].strip()

    with open(NAMES_FILE, 'r') as f:
        names = json.load(f)

    names[author_id] = new_name

    with open(NAMES_FILE, 'w') as f:
        json.dump(names, f)

    return Message(message='Got it {0}!'.format(new_name))


def get_name(author_id):
    if os.path.isfile(NAMES_FILE):
        with open(NAMES_FILE, 'r') as f:
            names = json.load(f)

        if author_id in names:
            return names[author_id]
