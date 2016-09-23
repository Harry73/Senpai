import sys
import os
import gc
import time
import json
import discord
import asyncio
import logging
from threading import Thread
from subprocess import Popen, PIPE

from lib import MessageHandler
from lib import Voice

sys.setrecursionlimit(5000)

logger = logging.getLogger("Senpai")

sources = [
	"hentai",
	"ecchi",
	"sukebei",
	"pantsu"
]

class SenpaiBot(discord.Client):
	def __init__(self):
		# Get discord creds
		with open("Config.json", "r") as f:
			self.config = json.load(f)

		self.init_ok = False
		self.music_player = Voice.Music(self)
		super().__init__()

	# Startup task
	async def on_ready(self):
		logger.info("Logged in as:")
		logger.info(self.user.name)
		logger.info(self.user.id)
		logger.info("--------------")
		self.init_ok = True

	# Look for discord messages and ask MessageHandler to deal with any
	async def on_message(self, message):
		response = await MessageHandler.handle_message(self, message)

		# If a command created a response, send response here
		if response:
			await self.wait_until_ready()
			try:
				await self.send_message(message.channel, response)
			except discord.errors.HTTPException as e:
				logger.exception(e)

	async def logout(self):
		return await super().logout()

	def run(self):
		try:
			self.loop.run_until_complete(self.start(self.config["discord"]["email"], self.config["discord"]["pass"]))
		finally:
			self._cleanup()

		self.loop.close()

	def _cleanup(self):
		try:
			self.loop.run_until_complete(self.logout())
		except: # Can be ignored
			pass

		pending = asyncio.Task.all_tasks()
		gathered = asyncio.gather(*pending)

		try:
			gathered.cancel()
			self.loop.run_until_complete(gathered)
			gathered.exception()
		except: # Can be ignored
			pass
