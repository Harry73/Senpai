import os
import json
import logging

from lib.Message import Message

LOGGER = logging.getLogger("Senpai")

# Say hi to the user, and use the nickname they've chosen
async def hi(author_id):
	print("hi")
	if os.path.isfile("names.txt"):
		print("yes")
		with open("names.txt", "r") as f:
			names = json.load(f)

		if author_id in names:
			return Message(message="Hi {0}.".format(names[author_id]))
		else:
			return Message(message="Hi. I don't have a name for you, use /callme <name> to pick your name.")
	else:
		print("no")
		with open("names.txt", "w") as f:
			f.write("{}")
		return Message(message="Hi. I don't have a name for you, use /callme <name> to pick your name.")


# Update "names.txt" with the new nickname
async def callMe(author_id, new_name):
	with open("names.txt", "r") as f:
		names = json.load(f)

	names[author_id] = new_name

	with open("names.txt", "w") as f:
		json.dump(names, f)

	return Message(message="Got it {0}!".format(new_name))


def getName(author_id):
	if os.path.isfile("names.txt"):
		with open("names.txt", "r") as f:
			names = json.load(f)

		if author_id in names:
			return names[author_id]
