import json
import os
import random
import logging

from lib.Message import Message

LOGGER = logging.getLogger('Senpai')
game_players = None
SPYFALL_FILE = os.path.join('json', 'spyfall.json')

async def play_spyfall(author, mentions):
    global game_players
    bot_responses = []

    LOGGER.debug('Spyfall.play_spyfall: players %s %s', author, mentions)

    with open(SPYFALL_FILE, 'r') as f:
        roles = json.load(f)

    game_players = mentions
    if author not in mentions:
        game_players.append(author)

    # Pick a random location
    locations = list(roles.keys())
    location = random.choice(locations)

    # Assign a spy
    players = game_players
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


async def play_spyfall_again():
    LOGGER.debug('Spyfall.play_spyfall_again: request')
    if game_players:
        response = await play_spyfall(None, None)
        return response
    else:
        return Message(message='No previous game found')
