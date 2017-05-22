import os
import logging
from subprocess import call

from lib import Dice
from lib import Card
from lib import Profile
from lib import Voice
from lib import Pun
from lib import Chat
from lib import Cat
from lib import Help
from lib import Translate
from lib import Names

logger = logging.getLogger("Senpai")

ownerID = "97877725519302656"

# Method to detect any commands and deal with them
async def handle_message(client, message):
	# Get list of available sound clips from directory
	clips = os.listdir("sounds/")
	clips = [clip[:-4] for clip in clips]

	# Call appropriate method to handle command
	if message.content == "/senpai":
		response = await Help.help(client, message.author, message.content[8:].strip())
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

	elif message.content == "/pun":
		response = await Pun.pun()
		return response

	elif message.content.startswith("/chat"):
		response = await Chat.chat(message.author.id, message.content[6:].strip())
		return response

	elif message.content == "/cat":
		response = await Cat.cat()
		return response

	elif message.content.startswith("/translate"):
		response = await Translate.translate(message.content[11:].strip())
		return response

	elif message.content == "/hi":
		response = await Names.hi(message.author.id)
		return response

	elif message.content.startswith("/callme"):
		response = await Names.callme(message.author.id, message.content[8:].strip())
		return response

	elif message.content.startswith("/spyfall again"):
		response = await client.spyfall_game.play_again()
		return response

	elif message.content.startswith("/spyfall"):
		response = await client.spyfall_game.play(message.author, message.mentions)
		return response

	# Voice commands
	elif message.content == "/summon":
		response = await client.music_player.summon(message)
		return response

	elif message.content == "/gtfo":
		response = await client.music_player.gtfo(message)
		return response

	elif message.content.startswith("/play"):
		response = await client.music_player.play(message, message.content[6:].strip())
		return response

	elif message.content == "/pause":
		response = await client.music_player.pause(message)
		return response

	elif message.content == "/queue":
		response = await client.music_player.queue(message)
		return response

	elif message.content == "/np":
		response = await client.music_player.np(message)
		return response

	elif message.content == "/skip":
		response = await client.music_player.skip(message)
		return response

	elif message.content == "/stop":
		response = await client.music_player.stop(message)
		return response

	elif message.content == "/sounds":
		return {"message": "\n".join(sorted(["/" + clip for clip in clips]))}
		
	elif message.content == "/count":
		return {"message": str(len(clips)) + " sound clips"}
		
	elif message.content[1:] in clips:
		response = await client.music_player.play_mp3(message, message.content[1:].strip())
		return response

	# Owner commands
	if message.author.id == ownerID:
		if message.content.startswith("/secrets"):
			response = await Help.secrets()
			return response

		elif message.content.startswith("/profile"):
			await Profile.edit_avatar(client, image_url=message.content[8:].strip())

		elif message.content.startswith("/name"):
			await Profile.edit_username(client, new_username=message.content[5:].strip())

		# Stops the "forever" or "pm2" process that is used to run the bot, thus killing the bot on comman
		elif message.content.startswith("/sudoku"):
			await client.logout()
			call(["forever", "stop", "0"])
			call(["pm2", "stop", "Senpai"])
			
		elif message.content.startswith("/restart"):
			call(["pm2", "restart", "Senpai"])
