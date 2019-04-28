import json
import os
import random

from lib.Command import register_command
from lib.Message import Message

GAME_PLAYERS = None
SPYFALL_FILE = os.path.join('json', 'spyfall.json')


@register_command(lambda m: m.content.startswith('/spyfall'))
async def spyfall(bot, message):
    """```
    Starts a clone of the game Spyfall with the message author and mentioned users as players.
    Players will be PM'd their roles.

    Usage:
    * /spyfall @player1 <@player2> <@player3> ...
    ```"""

    return await play_spyfall(message.author, message.mentions)


@register_command(lambda m: m.content == '/spyfall_again')
async def spyfall_again():
    """```
    Starts a new game with the same players as a previous game, if one exists.
    Players will be PM'd their roles.

    Usage:
    * /spyfall_again
    ```"""

    if GAME_PLAYERS:
        response = await play_spyfall(None, None)
        return response
    else:
        return Message(message='No previous game found')


async def play_spyfall(author, mentions):
    global GAME_PLAYERS
    bot_responses = []

    with open(SPYFALL_FILE, 'r') as f:
        roles = json.load(f)

    GAME_PLAYERS = mentions
    if author not in mentions:
        GAME_PLAYERS.append(author)

    # Pick a random location
    locations = list(roles.keys())
    location = random.choice(locations)

    # Assign a spy
    players = GAME_PLAYERS
    spy = random.choice(players)
    players.remove(spy)
    bot_responses.append(Message(
        message='You are the spy!\nPotential Locations: \n\t{0}'.format('\n\t'.join(sorted(locations))),
        channel=spy,
        cleanup_original=False,
        cleanup_self=False
    ))

    # Assign roles to other players
    for player in players:
        role = random.choice(roles)
        bot_responses.append(Message(
            message='You are not the spy.\nLocation: {0}\nYour Role: {1}'.format(location, role),
            channel=player,
            cleanup_original=False,
            cleanup_self=False
        ))
        roles.remove(role)

    bot_responses.append(Message(message='Game started'))

    return bot_responses
