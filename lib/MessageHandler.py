import os
import re
import random
import logging
from subprocess import call

from lib.Message import Message
from lib import Dice
from lib import Hentai
from lib import Card
from lib import Profile
from lib import Pun
from lib import Cat
from lib import Help
from lib import Translate
from lib import Names
from lib import Spyfall

LOGGER = logging.getLogger("Senpai")

ownerID = "97877725519302656"
senpai = "199228964651270144"

# MTG regex
MTG_REGEX = re.compile("\[(?P<card>.*?)\]")

# Method to detect any commands and deal with them
async def handleMessage(client, original_message):
	bot_response = None

	if original_message.author.id == senpai:
		return

	# Owner commands
	if original_message.author.id == ownerID:
		print("owner")
		if original_message.content.startswith("/secrets"):
			bot_response = await Help.secrets(original_message)

		elif original_message.content.startswith("/profile"):
			await Profile.editAvatar(client, image_url=original_message.content[8:].strip())

		elif original_message.content.startswith("/name"):
			await Profile.editUsername(client, new_username=original_message.content[5:].strip())

		# Stops the "forever" or "pm2" process that is used to run the bot, thus killing the bot on comman
		elif original_message.content.startswith("/sudoku"):
			await client.logout()
			call(["pm2", "stop", "Senpai"])

		elif original_message.content.startswith("/restart"):
			await client.logout()
			call(["pm2", "restart", "Senpai"])

	print("other")
	# Search for regex matches
	matches_mtg = re.findall(MTG_REGEX, original_message.content)

	# Call appropriate method to handle command
	if original_message.content.startswith("/senpai"):
		bot_response = await Help.getHelp(original_message, original_message.content[8:].strip())

	elif original_message.content.startswith("/mtg"):
		bot_response = await Card.mtgFindCards(original_message.channel.id, [original_message.content[5:].strip()])

	elif matches_mtg:
		bot_response = await Card.mtgFindCards(original_message.channel.id, matches_mtg)

	elif original_message.content.startswith("/card"):
		bot_response = await Card.findCard(original_message.channel.id, original_message.content[6:].strip())

	elif original_message.content.startswith("/roll"):
		bot_response = await Dice.parseRoll(original_message.content[6:].strip())

	elif original_message.content.startswith("/r "):
		bot_response = await Dice.parseRoll(original_message.content[3:].strip())

	elif original_message.content == "/pun":
		bot_response = await Pun.pun()

	elif original_message.content == "/cat":
		bot_response = await Cat.cat()

	elif original_message.content.startswith("/translate"):
		bot_response = await Translate.translate(original_message.content[11:].strip())

	elif original_message.content == "/hi":
		print("run hi")
		bot_response = await Names.hi(original_message.author.id)

	elif original_message.content.startswith("/callme"):
		bot_response = await Names.callMe(original_message.author.id, original_message.content[8:].strip())

	elif original_message.content == "/spyfall again":
		bot_response = await Spyfall.playSpyfallAgain()

	elif original_message.content.startswith("/spyfall"):
		bot_response = await Spyfall.playSpyfall(original_message.author, original_message.mentions)

	# Voice commands
	elif original_message.content == "/summon":
		bot_response = await client.music_player.summon(original_message)

	elif original_message.content == "/gtfo":
		bot_response = await client.music_player.gtfo(original_message)

	elif original_message.content.startswith("/play"):
		bot_response = await client.music_player.play(original_message, original_message.content[6:].strip())

	elif original_message.content == "/pause":
		bot_response = await client.music_player.pause(original_message)

	elif original_message.content == "/queue":
		bot_response = await client.music_player.queue(original_message)

	elif original_message.content == "/np":
		bot_response = await client.music_player.np(original_message)

	elif original_message.content == "/skip":
		bot_response = await client.music_player.skip(original_message)

	elif original_message.content == "/stop":
		bot_response = await client.music_player.stop(original_message)

	elif original_message.content == "/shuffle":
		random.shuffle(clips)
		for clip in clips:
			bot_response = await client.music_player.play_mp3(original_message, clip)

	# Commands that require the list of sound clips
	elif original_message.content.startswith("/"):
		# Get list of available sound clips from directory
		clips = os.listdir("sounds/")
		clips = [clip[:-4] for clip in clips if os.path.isfile(os.path.join("sounds/", clip))]

		if original_message.content == "/sounds":
			bot_message = "\n".join(sorted(["/" + clip for clip in clips]))
			bot_response = Message(original_message=bot_message)

		elif original_message.content == "/count":
			bot_message = str(len(clips)) + " sound clips"
			bot_response = Message(message=bot_message)

		elif original_message.content[1:] in clips:
			bot_message = await client.music_player.play_mp3(original_message, original_message.content[1:].strip())

	if isinstance(bot_response, list):
		return bot_response
	elif bot_response:
		return [bot_response]
	else:
		return None
