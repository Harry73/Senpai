import os
import logging
from collections import OrderedDict

owner_help_text = """```Commands:
/secrets
/kraithan @<names>: message
/profile <image_url>
/name <new_name>
/sudoku
```"""

# Halp
regular_commands = OrderedDict()
regular_commands["senpai"] = """```/senpai <command>
Show information about the command specified.```"""

regular_commands["mtg"] = """```/mtg <card name>
Searches for a MTG card using the standard API```"""

regular_commands["card"] = """```/card <card name>
Provides link to search from magiccards.info```"""

regular_commands["roll"] = """```/roll NdM
Roll20-like dice rolling. Any roll command is limited to 1000 total dice. 
'/roll stats' will perform 4 rolls that can be used as stats for text-based game Kraithan.
'/roll' can be shortened to '/r'```"""

regular_commands["pun"] = """```/pun
Say a pun.```"""

regular_commands["chat"] = """```/chat <text>
Senpai will respond to the <text>```"""

regular_commands["cat"] = """```/cat
Links a picture to a random cat```"""

regular_commands["translate"] = """```/translate <text>
Use jisho.org to translate <text>```"""

regular_commands["spyfall"] = """```/spyfall @players
Starts a clone of the game Spyfall. Players will be PM'd their roles."""

regular_commands["hi"] = """```/hi
Senpai says hi to you.```"""

regular_commands["callme"] = """```/callme <name>
In the future, Senpai will call you <name>.```"""

#regular_commands["kraithan"] = """```/kraithan @<name1> @<name2>: <message>
#Temporarily transforms Senpai into Fyn and sends the <message> to the kraithan_game with @mention for the <names>.```"""


voice_commands = OrderedDict()
voice_commands["summon"] = """```/summon
Bring Senpai to your current voice channel```"""

voice_commands["play"] = """```Brings Senpai to your current voice channel if she's not already in it.
/play <youtube link>            -> Plays the linked song
/play <youtube search words>    -> Plays the first YT result
/play <soundcloud link>         -> Plays the linked song
/play                           -> Resumes paused music```"""

voice_commands["pause"] = """```/pause
Pauses the current song. Use /play to resume.```"""

voice_commands["queue"] = """```/queue
Lists the songs currently in the queue.```"""

voice_commands["np"] = """```/np
Prints the currently playing song.```"""

voice_commands["skip"] = """```/skip
Skips the currently playing song.```"""

voice_commands["stop"] = """```/stop
Stops playing any music and clear the current queue of songs.```"""

voice_commands["gtfo"] = """```/gtfo
Senpai will leave her current voice channel and clear the current queue of songs.```"""

logger = logging.getLogger("Senpai")

async def help(client, author, request):
	logger.debug("Help request: {0}".format(request))
	
	# Compile default help text
	regular_commands_list = ["/{0}".format(command) for command in list(regular_commands.keys())]
	voice_commands_list = ["/{0}".format(command) for command in list(voice_commands.keys())]
	
	help_text = "```Use /senpai <command> for more information\n\n"
	help_text += "General: \n" + ", ".join(regular_commands_list) + "\n\n"
	help_text += "Voice: \n" + ", ".join(voice_commands_list) + "\n\n"
	
	# Get list of available sound clips from directory
	clips = os.listdir("sounds/")
	clips = [clip[:-4] for clip in clips]
	
	# Add on instructions for each clip to the help text
	clips_commands = ["/{0}".format(clip) for clip in clips]
	clips_commands = sorted(clips_commands)
	
	help_text += "Sounds: \n" + ", ".join(clips_commands) + "```\n\n"

	if not request:
		await client.send_message(author, help_text)
	else:
		if request in regular_commands:
			await client.send_message(author, regular_commands[request])
		elif request in voice_commands:
			await client.send_message(author, voice_commands[request])
		elif request in clips:
			await client.send_message(author, "```/{0}\nPlays the {0} sound file```".format(request))
		else:
			await client.send_message(author, "No {0} command!".format(request))
			
	return {"message": "Sent you a DM."}

async def secrets():
	return {"message": owner_help_text}

