import json
import logging
import aiohttp

logger = logging.getLogger("Senpai")

async def translate(text):
	logger.debug("Translate something")

	url = "http://jisho.org/api/v1/search/words?"
	
	try:
		if text:
			url += "keyword={0}".format(text.replace(" ", "+"))
			js = None
			
			# Fetch json from url
			async with aiohttp.get(url) as r:
				if r.status == 200:
					js = await r.json()
				else:
					logger.error("Can't translate. Status: {0}".format(r.status))
			
			# Get translations from resulting data structure
			if js:
				data = js["data"]
				if data:
					japanese = data[0]["japanese"][0]
					english = data[0]["senses"][0]["english_definitions"]
					
					output = ""
					if "word" in japanese:
						output += "Japanese: {0}\n".format(japanese["word"])
					if "reading" in japanese:
						output += "Reading: {0}\n".format(japanese["reading"])
					if english:
						output += "English: {0}".format(", ".join(english))
					return {"message": output}
				else:
					return {"message": "No translations found"}
		else:
			return {"message": "Well give me something to translate!"}
	except Exception as e:
		logger.exception(e)
	