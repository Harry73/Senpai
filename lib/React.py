from lib.Command import register_command


UNICODE_ALPHABET_START = ord('a')
UNICODE_REGIONAL_START = ord('\U0001F1E6')


@register_command(lambda m: m.content.startswith('/react'))
async def react(bot, message):
    """```
    Adds reactions to the previous message to match given text

    Usage:
    * /react <text>
    ```"""

    channel = message.channel
    reaction = message.content[7:].strip()

    # Remove spaces
    reaction = reaction.lower().replace(' ', '')

    first_seen = False
    async for message in bot.logs_from(channel, limit=2):
        # Skip the first message in the log, which will be the /react request
        if not first_seen:
            first_seen = True
            continue

        for char in reaction:
            unicode_ord = ord(char) - UNICODE_ALPHABET_START + UNICODE_REGIONAL_START
            await bot.add_reaction(message, chr(unicode_ord))
