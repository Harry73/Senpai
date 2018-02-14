import os
import json
import logging

from lib.Message import Message

LOGGER = logging.getLogger('Senpai')
NAMES_FILE = os.path.join('json', 'names.json')

# Say hi to the user, and use the nickname they've chosen
async def hi(author_id):
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
async def call_me(author_id, new_name):
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
