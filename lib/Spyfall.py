import math
import json
import random
import logging
import itertools

logger = logging.getLogger("Senpai")

class Spyfall:
	def __init__(self, client):
		self.client = client
		self.game_players = []
		with open("spyfall.json", "r") as f:
			self.roles = json.load(f)

	async def play(self, author, mentions):
		self.game_players = mentions
		if author not in mentions:
			self.game_players.append(author)
		
		# Pick a random location
		locations = list(self.roles.keys())
		location = random.choice(locations)

		# Assign a spy
		players = self.game_players
		spy = random.choice(players)
		players.remove(spy)
		await self.client.send_message(spy, "You are the spy!\nPotential Locations: \n\t{0}".format("\n\t".join(sorted(locations))))

		# Assign roles to other players
		for player in players:
			role = random.choice(roles)
			await self.client.send_message(player, "You are not the spy.\nLocation: {0}\nYour Role: {1}".format(location, role))
			roles.remove(role)
			
		return {"message": "Game started"}

	async def play_again(self):
		if self.game_players:
			response = await self.play(None, None)
			return response
		else:
			return {"message": "No previous game found"}
			