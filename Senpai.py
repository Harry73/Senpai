import os
import gc
import sys
import time
import json
import shutil
import asyncio
import logging
from subprocess import Popen, PIPE
from SenpaiBot import SenpaiBot

stop = False

# Set up logger
logger = logging.getLogger("Senpai")
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler(os.path.join(os.getcwd(), "Senpai.log"), mode="w")
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# Begin!
def main():
	global stop

	count = 1
	while True:
		bot = None

		# Delete old audio files
		if os.path.isdir("audio_cache"):
			shutil.rmtree("./audio_cache")

		try:
			logger.info("Loop #{0}".format(count))
			bot = SenpaiBot()
			bot.run()
		except Exception as e:
			logger.exception("Death: {0}".format(e))
		except SystemExit:
			break
		except:
			logger.error("Now I just have no idea what killed me.")
		finally:
			if not bot or not bot.init_ok:
				break

			asyncio.set_event_loop(asyncio.new_event_loop())
			count += 1
			time.sleep(30)

	# Clean up in the event of total failure
	gc.collect()
	logger.warning("I have committed sudoku.")

# Check python version for 3.5 or better
if __name__ == "__main__":
	if sys.version_info >= (3, 5):
		main()
	else:
		raise Exception("Run with python 3.5")
