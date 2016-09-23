import os
import logging
from subprocess import call

from lib import Dice
from lib import Card
from lib import Profile
from lib import Voice
from lib import Pun
from lib import Clever
from lib import Cat
from lib import Help
from lib import Translate

logger = logging.getLogger("Senpai")

ownerID = "97877725519302656"

# IDs of other bot accounts
other_bots = [
	"152617487630991360",
	"121398650738835458"
]

# Method to detect any commands and deal with them
async def handle_message(client, message):
	# Prevent another bot from calling commands
	if message.author.id in other_bots or "bot" in message.author.name:
		if message.content.startswith("/"):
			logger.debug("Request by another bot, ignoring")
	else:
		# Get list of available sound clips from directory
		clips = os.listdir("sounds/")
		clips = [clip[:-4] for clip in clips]

		# Call appropriate method to handle command
		if message.content.startswith("/senpai"):
			response = await Help.help(message.content[8:].strip())
			return response

		elif message.content.startswith("/mtg"):
			response = await Card.mtg_find_card(message.content[5:].strip())
			return response

		elif message.content.startswith("/card"):
			response = await Card.find_card(message.content[6:].strip())
			return response

		elif message.content.startswith("/roll"):
			response = await Dice.parse_roll(message.content[6:].strip())
			return response

		elif message.content.startswith("/r "):
			response = await Dice.parse_roll(message.content[3:].strip())
			return response

		elif message.content.startswith("/pun"):
			response = await Pun.pun()
			return response

		elif message.content.startswith("/chat"):
			response = await Clever.chat(message.content[6:].strip())
			return response
			
		elif message.content.startswith("/cat"):
			response = await Cat.cat()
			return response

		elif message.content.startswith("/translate"):
			response = await Translate.translate(message.content[11:].strip())
			return response

		# Voice commands
		elif message.content.startswith("/summon"):
			response = await client.music_player.summon(message)
			return response

		elif message.content.startswith("/gtfo"):
			response = await client.music_player.gtfo(message)
			return response

		elif message.content.startswith("/play"):
			response = await client.music_player.play(message, message.content[6:].strip())
			return response

		elif message.content.startswith("/pause"):
			response = await client.music_player.pause(message)
			return response

		elif message.content.startswith("/queue"):
			response = await client.music_player.queue(message)
			return response

		elif message.content.startswith("/np"):
			response = await client.music_player.np(message)
			return response

		elif message.content.startswith("/skip"):
			response = await client.music_player.skip(message)
			return response

		elif message.content.startswith("/stop"):
			response = await client.music_player.stop(message)
			return response

		elif message.content[1:] in clips:
			response = await client.music_player.play_mp3(message, message.content[1:].strip())
			return response

	# Owner commands
	if message.author.id == ownerID:
		if message.content.startswith("/secrets"):
			response = await Help.secrets()
			return response

		elif message.content.startswith("/test"):
			return "Hi %s" % message.author.name.split("#")[0]

		elif message.content.startswith("/profile"):
			await Profile.edit_profile(client, image_url=message.content[8:].strip())

		elif message.content.startswith("/daily"):
			await Hentai.post()
			
		# Stops the "forever" process that is used to run the bot, thus killing the bot on comman
		elif message.content.startswith("/sudoku"):
			await client.logout()
			call(["forever", "stop", "0"])
