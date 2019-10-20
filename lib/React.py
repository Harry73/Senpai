from lib.Command import register_command


UNICODE_NUMBER_START = ord('0')
UNICODE_NUMBER_END = ord('9')
UNICODE_ALPHABET_START = ord('a')
UNICODE_ALPHABET_END = ord('z')
UNICODE_REGIONAL_A = ord('\U0001F1E6')
UNICODE_REGIONAL_ZERO = ord('\U000020E3')

numbers = [
    '\N{DIGIT ZERO}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT SIX}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT SEVEN}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT EIGHT}\N{COMBINING ENCLOSING KEYCAP}',
    '\N{DIGIT NINE}\N{COMBINING ENCLOSING KEYCAP}',
]


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
    async for message in channel.history(limit=2):
        # Skip the first message in the log, which will be the /react request
        if not first_seen:
            first_seen = True
            continue

        sent = []
        for char in reaction:
            if char in sent:
                continue

            if UNICODE_NUMBER_START <= ord(char) <= UNICODE_NUMBER_END:
                sent.append(char)
                await message.add_reaction(numbers[ord(char) - UNICODE_NUMBER_START])

            elif UNICODE_ALPHABET_START <= ord(char) <= UNICODE_ALPHABET_END:
                sent.append(char)
                unicode_ord = ord(char) - UNICODE_ALPHABET_START + UNICODE_REGIONAL_A
                await message.add_reaction(chr(unicode_ord))
