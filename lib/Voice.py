import asyncio
import ctypes
import discord
import functools
import logging
import os
import random
import shutil
import uuid
import youtube_dlc

from collections import deque

from lib.Command import CommandType, register_command
from lib.Message import Message


LOG = logging.getLogger('Senpai')
AUDIO_CACHE_DIR = 'audio_cache'

YTDL_FORMAT_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': os.path.join(AUDIO_CACHE_DIR, '%(extractor)s-%(id)s-%(title)s.%(ext)s'),
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'options': '-vn'
}

# Load the magical opus
if not discord.opus.is_loaded():
    lib = ctypes.util.find_library('opus')
    discord.opus.load_opus(lib)

YT_DL = youtube_dlc.YoutubeDL(YTDL_FORMAT_OPTIONS)


# Encapsulates a YoutubeDL object and makes it nicer
class YtdlSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, file_to_clean_up=None, url=None, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        # Set information for clean up
        self.file_to_clean_up = file_to_clean_up

        # Set information for now-playing command
        self.title = data.get('title')
        self.url_link = data.get('webpage_url', url)

    def cleanup(self):
        super().cleanup()
        if os.path.isfile(self.file_to_clean_up):
            os.remove(self.file_to_clean_up)

    @classmethod
    async def download(cls, url, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: YT_DL.extract_info(url, download=True))

        # take first item from a playlist
        if 'entries' in data:
            data = data['entries'][0]

        return data, YT_DL.prepare_filename(data)


def _get_client(bot, guild):
    return discord.utils.get(bot.voice_clients, guild=guild)


def _play_next(voice_client, exception):
    if exception:
        LOG.error('Player error', exc_info=exception)

    if not hasattr(voice_client, 'song_queue'):
        LOG.info('Voice client has no song queue')
        return

    if not voice_client.song_queue:
        LOG.info('No more queued songs to play')
        return

    source = voice_client.song_queue.popleft()
    LOG.info('Playing next: %s' % source.title)
    voice_client.play(source, after=functools.partial(_play_next, voice_client))


def _play_or_queue(voice_client, source):
    if not hasattr(voice_client, 'song_queue'):
        voice_client.song_queue = deque()

    if voice_client.is_playing():
        voice_client.song_queue.append(source)
    else:
        LOG.info('Playing: %s' % source.title)
        voice_client.play(source, after=functools.partial(_play_next, voice_client))


# Plays a clip song. If something is playing, the request will be queued
# Also automatically searches YouTube for the song
async def _play_mp3(bot, message, clip: str):
    # Requester must be in a voice channel to use '/<sound>' command
    if message.author.voice.channel is None:
        return Message(message='You are not in a voice channel.')

    voice_client = _get_client(bot, message.guild)

    if voice_client is None:
        response = await summon(bot, message)
        if response:
            return response
        else:
            voice_client = _get_client(bot, message.guild)

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio('sounds/{0}.mp3'.format(clip)))
    # add information for now-playing command
    source.title = 'Sound clip - {0}'.format(clip)
    source.url_link = None
    _play_or_queue(voice_client, source)


# Resumes the currently playing song, internal method
async def _resume(bot, message):
    voice_client = _get_client(bot, message.guild)
    if voice_client:
        voice_client.resume()


def uniquify(file_path):
    return os.path.join(os.path.dirname(file_path), '%s-%s' % (uuid.uuid4(), os.path.basename(file_path)))


# Voice related commands

# Summons the bot to join the voice channel the message author is in
@register_command(lambda m: m.content == '/summon', command_type=CommandType.VOICE)
async def summon(bot, message):
    """```
    Bring Senpai to your current voice channel.

    Usage:
    * /summon
    ```"""

    if message.author.voice is None or message.author.voice.channel is None:
        return Message(message='You are not in a voice channel')

    summoned_voice_channel = message.author.voice.channel
    voice_client = _get_client(bot, message.guild)

    if voice_client is None:
        await summoned_voice_channel.connect()
    elif voice_client.channel != summoned_voice_channel:
        await voice_client.move_to(summoned_voice_channel)


# Plays a song. If something is playing, the request will be queued
# Also automatically searches YouTube for the song
@register_command(lambda m: m.content.startswith('/play'), command_type=CommandType.VOICE)
async def play(bot, message):
    """```
    Download and play a youtube video or soundcloud song. This command will bring Senpai to your current
    voice channel if she is not already in it.

    Usages:
    * /play youtube_link <count>           -> Play the linked song <count> number of times
    * /play youtube_search_words <count>   -> Play the first YT result <count> number of times
    * /play soundcloud_link <count>        -> Play the linked song <count> number of times
    * /play                                -> Resume paused music
    ```"""

    # Requester must be in a voice channel to use '/play' command
    if message.author.voice is None or message.author.voice.channel is None:
        return Message(message='You are not in a voice channel')

    song_and_count = message.content[6:].strip()

    if not song_and_count:
        await _resume(bot, message)
        return {}

    voice_client = _get_client(bot, message.guild)

    # Bring Senpai to the voice channel if she's not already in it
    if voice_client is None or message.author.voice.channel != voice_client.channel:
        response = await summon(bot, message)
        if response:
            return response
        else:
            voice_client = _get_client(bot, message.guild)

    # See if a number of times to play ths song is specified
    pieces = song_and_count.split()
    count = 1
    song = song_and_count
    if len(pieces) > 1:
        try:
            count = int(pieces[-1])
            song = ' '.join(pieces[0:-1])
        except ValueError:
            pass

    if count < 1:
        count = 1
    elif count > 25:
        count = 25

    data, original_file = await YtdlSource.download(song, loop=bot.loop)
    file_names = []

    def clone_file(method):
        unique_file_name = uniquify(original_file)
        method(original_file, unique_file_name)
        file_names.append(unique_file_name)

    # Make "count - 1" copies of the file and then move the original file to one with a unique name.
    for i in range(count - 1):
        clone_file(shutil.copy)
    clone_file(shutil.move)

    # Play each file separately. This process is to cope with a song being played multiple times in a row nicely.
    for file_name in file_names:
        source = YtdlSource(discord.FFmpegPCMAudio(file_name, **FFMPEG_OPTIONS), data=data,
                            file_to_clean_up=file_name, url=song)
        source.url = song
        _play_or_queue(voice_client, source)


# Pauses the currently playing song
@register_command(lambda m: m.content == '/pause', command_type=CommandType.VOICE)
async def pause(bot, message):
    """```
    Pauses the current song. Use /play to resume.

    Usage:
    * /pause
    ```"""

    voice_client = _get_client(bot, message.guild)
    if voice_client.is_playing():
        voice_client.pause()


# Return a list of song titles in the queue
@register_command(lambda m: m.content == '/queue', command_type=CommandType.VOICE)
async def queue(bot, message):
    """```
    Lists the songs currently in the queue.

    Usage:
    * /queue
    ```"""

    voice_client = _get_client(bot, message.guild)

    response = 'No songs queued'
    if voice_client and hasattr(voice_client, 'song_queue') and voice_client.song_queue:
        song_list = [song.title for song in voice_client.song_queue]
        response = 'Songs currently in the queue:\n'
        response += '\n'.join(song_list)

    return Message(message=response)


# Return the currently playing song
@register_command(lambda m: m.content in ['/np', '/nowplaying'], command_type=CommandType.VOICE)
async def np(bot, message):
    """```
    Print the currently playing song.

    Usages:
    * /np
    * /nowplaying
    * /playing
    ```"""

    voice_client = _get_client(bot, message.guild)

    if voice_client is None or not voice_client.is_playing():
        return Message(message='Not playing any music right now')

    return Message(message='Now playing: {0}\n{1}'.format(voice_client.source.title, voice_client.source.url_link))


@register_command(lambda m: m.content == '/skip', command_type=CommandType.VOICE)
async def skip(bot, message):
    """```
    Skip the currently playing song.

    Usage:
    * /skip
    ```"""

    voice_client = _get_client(bot, message.guild)
    if voice_client is None or not voice_client.is_playing():
        return Message(message='Not playing any music right now')

    voice_client.stop()
    _play_next(voice_client, None)


# Stops the song and clears the queue
@register_command(lambda m: m.content == '/stop', command_type=CommandType.VOICE)
async def stop(bot, message):
    """```
    Stop playing any music and clear the current queue of songs.

    Usage:
    * /stop
    ```"""

    voice_client = _get_client(bot, message.guild)

    if voice_client:
        if hasattr(voice_client, 'song_queue'):
            voice_client.song_queue = deque()
        voice_client.stop()


# Stops the song, clears the queue, and leaves the channel
@register_command(lambda m: m.content == '/gtfo', command_type=CommandType.VOICE)
async def gtfo(bot, message):
    """```
    Remove Senpai from her current voice channel and clear the current queue of songs.

    Usage:
    * /gtfo
    ```"""

    await stop(bot, message)

    voice_client = message.guild.voice_client
    await voice_client.disconnect()

    # Delete old audio files
    if os.path.isdir('audio_cache'):
        shutil.rmtree('./audio_cache')


# Commands that require the list of sound clips
def generate_sound_clip_commands():
    # Get list of available sound clips from directory
    clips = os.listdir('sounds/')
    clips = [clip[:-4] for clip in clips if os.path.isfile(os.path.join('sounds/', clip))]

    @register_command(lambda m: m.content == '/sounds', command_type=CommandType.VOICE)
    async def sounds(bot, message):
        """```
        PM a list of commands for sound clips that Senpai can play.

        Usage:
        * /sounds
        ```"""

        bot_message = '\n'.join(sorted(['/' + clip for clip in clips]))
        bot_response = Message(message=bot_message, channel=message.author,
                               cleanup_self=False, cleanup_original=False)
        if 'Direct Message' not in str(message.channel):
            bot_response = [bot_response, Message(message='Sent you a DM.')]

        return bot_response

    @register_command(lambda m: m.content == '/count', command_type=CommandType.VOICE)
    async def count(bot, message):
        """```
        Give the number of available sound clips.

        Usage:
        * /count
        ```"""
        return Message(message=str(len(clips)) + ' sound clips')

    @register_command(lambda m: m.content == '/shuffle', command_type=CommandType.VOICE)
    async def shuffle(bot, message):
        """```
        Plays all the sounds clips in a random order. Please play nice.

        Usage:
        * /shuffle
        ```"""

        bot_response = None
        random.shuffle(clips)
        for clip in clips:
            bot_response = await bot.music_player.play_mp3(message, clip)

        return bot_response

    def make_clip_function(clip):
        help_text = """```
        Plays the "{0}" sound clip.
        
        Usage:
        * /{0}
        ```""".format(clip)

        @register_command(lambda m: m.content[1:] == clip, command_type=CommandType.CLIP,
                          override_name=clip, override_help=help_text)
        async def play_clip(bot, message):
            bot_message = await _play_mp3(bot, message, message.content[1:].strip())
            return Message(message=bot_message) if bot_message else None

        return play_clip

    for clip in clips:
        make_clip_function(clip)


generate_sound_clip_commands()
