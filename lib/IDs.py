# Holds channel and user IDs
import os
from threading import Lock


OWNER_ID = 199228964651270144
SENPAI_ID = 411731781629247488

CARD_CHANNELS = [
    255524987245428736,
    491118672711122949,
]

NAMES_TO_CHANNELS = {
    'dnd':         167436887139549185,
    'singularity': 349211261541810176,
    'hyperlanes':  481594516399456267,
    'zenith':      349211211742838784,
    'test':        456969532423274508,
}

NAMES_TO_USERS = {
    'ian':    199228964651270144,
    'steve':  100462788190683136,
    'adam':   97886370554445824,
    'matt':   98257366826360832,
    'ahasan': 97878099194040320,
    'ravi':   97876869939998720,
    'nevil':  140472675838459904,
    'jason':  117438004661846023,
    'dan':    97925454748479488,
    'sanjay': 117062160093282313,
}

# Miscellaneous variables for event handling, because I need some shared place to put them to break cycles
EVENTS_FILE = os.path.join('json', 'events.json')
FILE_LOCK = Lock()
ABSOLUTE_TIME_FORMAT = '%Y-%m-%d %H:%M'
