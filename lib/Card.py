import logging

from mtgsdk import Card

logger = logging.getLogger("Senpai")

# Find link to MTG card using magiccards.info queries
async def find_card(searchKey):
	logger.debug("MCI: Looking up '%s'", searchKey)
	
	try:
		searchKey = searchKey.replace(" ", "+")
		url = "http://magiccards.info/query?q={0}&v=card&s=cname"
		return {"message": url.format(searchKey)}
	except Exception as e:
		logger.exception("Error: {0}".format(e))

# Find link to MTG card using mtgsdk
async def mtg_find_card(searchKey):
	logger.debug("MTG: Looking up '%s'", searchKey)
	
	try:
		cards = Card.where(name=searchKey).all()
		if len(cards) == 0:
			return {"message": "Couldn't find a card with that name"}
		else:
			return {"message": cards[-1].image_url}

	except Exception as e:
		logger.exception("Error: {0}".format(e))