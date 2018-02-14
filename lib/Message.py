import logging

LOGGER = logging.getLogger('Senpai')


class Message:

    def __init__(self, message=None, channel=None, cleanup_original=True, cleanup_self=True):
        self.message = message
        self.channel = channel
        self.cleanup_original = cleanup_original
        self.cleanup_self = cleanup_self

    def set_channel(self, new_channel):
        if not self.channel:
            self.channel = new_channel

    def __str__(self):
        return str(self.message) + ' || ' + str(self.channel)
        
    def __repr__(self):
        return self.__str__()

