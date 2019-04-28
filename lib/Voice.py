import asyncio
import functools
import logging
import os
import random
import shutil
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import discord
import youtube_dl

from lib.Command import CommandType, register_command
from lib.Message import Message

LOG = logging.getLogger('Senpai')

# Lots of options used by Downloader class
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
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

# Load the magical opus
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')


# Encapsulates a YoutubeDL object and makes it nicer
class Downloader:

    def __init__(self, download_folder=None):
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.unsafe_ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.safe_ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.safe_ytdl.params['ignoreerrors'] = True
        self.download_folder = download_folder

        if download_folder:
            otmpl = self.unsafe_ytdl.params['outtmpl']
            self.unsafe_ytdl.params['outtmpl'] = os.path.join(download_folder, otmpl)

            otmpl = self.safe_ytdl.params['outtmpl']
            self.safe_ytdl.params['outtmpl'] = os.path.join(download_folder, otmpl)

    @property
    def ytdl(self):
        return self.safe_ytdl

    async def extract_info(self, loop, *args, on_error=None, retry_on_error=False, **kwargs):
        """
            Runs ytdl.extract_info within the threadpool. Returns a future that will fire when it's done.
            If `on_error` is passed and an exception is raised, the exception will be caught and passed to
            on_error as an argument.
        """
        if callable(on_error):
            try:
                return await loop.run_in_executor(
                    self.thread_pool,
                    functools.partial(self.unsafe_ytdl.extract_info, *args, **kwargs)
                )

            except Exception as e:

                # (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError)
                if asyncio.iscoroutinefunction(on_error):
                    asyncio.ensure_future(on_error(e), loop=loop)

                elif asyncio.iscoroutine(on_error):
                    asyncio.ensure_future(on_error, loop=loop)

                else:
                    loop.call_soon_threadsafe(on_error, e)

                if retry_on_error:
                    return await self.safe_extract_info(loop, *args, **kwargs)
        else:
            return await loop.run_in_executor(
                self.thread_pool,
                functools.partial(self.unsafe_ytdl.extract_info, *args, **kwargs)
            )

    async def safe_extract_info(self, loop, *args, **kwargs):
        return await loop.run_in_executor(
            self.thread_pool,
            functools.partial(self.safe_ytdl.extract_info, *args, **kwargs)
        )


# Encapsulates a player for a song or mp3
class VoiceEntry:

    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        if hasattr(self.player, 'url'):
            fmt = '{0.url}'
            return fmt.format(self.player)
        else:
            return 'something I do not recognize?'


# Contains the music queues of VoiceEntry's and manages the player
class VoiceState:

    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.songs_queue = deque()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        if self.is_playing():
            self.player.stop()

    def toggle_next(self, last_song_filename):
        # Remove last song played
        if last_song_filename:
            if os.path.isfile(last_song_filename):
                os.remove(last_song_filename)

        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            self.songs_queue.popleft()
            LOG.debug('now playing %s', str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()


# Voice related command helpers
def _get_voice_state(bot, server):
    state = bot.voice_states.get(server.id)
    if state is None:
        state = VoiceState(bot)
        bot.voice_states[server.id] = state

    return state


def __unload(bot):
    for state in bot.voice_states.values():
        try:
            state.audio_player.cancel()
            if state.voice:
                bot.loop.create_task(state.voice.disconnect())
        finally:
            pass


# Plays a clip song. If something is playing, the request will be queued
# Also automatically searches YouTube for the song
async def _play_mp3(bot, message, clip: str):
    # Requester must be in a voice channel to use '/<sound>' command
    if message.author.voice_channel is None:
        return Message(message='You are not in a voice channel.')

    state = _get_voice_state(bot, message.server)

    if state.voice is None:
        response = await summon(bot, message)
        if response:
            return response

    try:
        player = state.voice.create_ffmpeg_player(
            'sounds/{0}.mp3'.format(clip),
            after=lambda: state.toggle_next(None)
        )
        player.url = 'Sound clip - {0}'.format(clip)
        player.title = 'Sound clip - {0}'.format(clip)
    except Exception as e:
        LOG.exception(e)
    else:
        player.volume = 0.6
        entry = VoiceEntry(message, player)
        await state.songs.put(entry)
        state.songs_queue.append(entry)


# Resumes the currently playing song, internal method
async def _resume(bot, message):
    state = _get_voice_state(bot, message.server)
    if state.is_playing():
        player = state.player
        player.resume()


# Voice related commands

# Summons the bot to join the voice channel the message author is in
@register_command(lambda m: m.content == '/summon', command_type=CommandType.VOICE)
async def summon(bot, message):
    """```
    Bring Senpai to your current voice channel.

    Usage:
    * /summon
    ```"""

    summoned_channel = message.author.voice_channel
    if summoned_channel is None:
        return Message(message='You are not in a voice channel')

    state = _get_voice_state(bot, message.server)
    if state.voice is None:
        state.voice = await bot.join_voice_channel(summoned_channel)
    else:
        await state.voice.move_to(summoned_channel)


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
    if message.author.voice_channel is None:
        return Message(message='You are not in a voice channel.')

    song_and_count = message.content[6:].strip()

    if not song_and_count:
        await _resume(bot, message)
        return {}

    state = _get_voice_state(bot, message.server)

    # Bring Senpai to the voice channel if she's not already in it
    if state.voice is None or str(message.author.voice_channel) != str(state.voice.channel):
        response = await summon(message)
        if response:
            return response

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

    for i in range(count):
        try:
            # Check info
            info = await bot.downloader.extract_info(bot.loop, song, download=False)

            if not info:
                LOG.warning('failed to extract info for %s', song)
                return Message(message='Failed to extract info from the video')
            else:
                if 'entries' in info:
                    info = info['entries'][0]

                song_url = info['webpage_url']
                LOG.debug('song url %s', song_url)

                result = await bot.downloader.safe_extract_info(bot.loop, song_url, download=True)
                if not result:
                    raise Exception('Death, and idk why')

                # Get filename and then create player for the file
                filename = bot.downloader.ytdl.prepare_filename(result)
                player = state.voice.create_ffmpeg_player(
                    filename,
                    before_options='-nostdin',
                    options='-vn -b:a 128k',
                    after=lambda: state.toggle_next(filename)
                )
                player.url = song
                player.title = result['title']
        except Exception as e:
            LOG.exception(e)
        else:
            player.volume = 0.6
            entry = VoiceEntry(message, player)
            await state.songs.put(entry)
            state.songs_queue.append(entry)


# Pauses the currently playing song
@register_command(lambda m: m.content == '/pause', command_type=CommandType.VOICE)
async def pause(bot, message):
    """```
    Pauses the current song. Use /play to resume.

    Usage:
    * /pause
    ```"""

    state = _get_voice_state(bot, message.server)
    if state.is_playing():
        player = state.player
        player.pause()


# Return a list of song titles in the queue
@register_command(lambda m: m.content == '/queue', command_type=CommandType.VOICE)
async def queue(bot, message):
    """```
    Lists the songs currently in the queue.

    Usage:
    * /queue
    ```"""

    state = _get_voice_state(bot, message.server)

    if state.songs_queue:
        song_list = []
        for song in state.songs_queue:
            if hasattr(song.player, 'title'):
                song_list.append(song.player.title)

        response = 'Songs currently in the queue:\n'
        response += '\n'.join(song_list)
    else:
        response = 'No songs queued'

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

    state = _get_voice_state(bot, message.server)

    if state.current:
        return Message(message='Now playing: {0}'.format(state.current.player.title))
    else:
        return Message(message='Not playing any music right now...')


@register_command(lambda m: m.content == '/skip', command_type=CommandType.VOICE)
async def skip(bot, message):
    """```
    Skip the currently playing song.

    Usage:
    * /skip
    ```"""

    state = _get_voice_state(bot, message.server)
    if not state.is_playing():
        return Message(message='Not playing any music right now...')

    state.skip()


# Stops the song and clears the queue
@register_command(lambda m: m.content == '/stop', command_type=CommandType.VOICE)
async def stop(bot, message):
    """```
    Stop playing any music and clear the current queue of songs.

    Usage:
    * /stop
    ```"""

    server = message.server
    state = _get_voice_state(bot, server)

    if state.is_playing():
        player = state.player
        player.stop()
        state.songs = asyncio.Queue()
        state.songs_queue = deque()


# Stops the song, clears the queue, and leaves the channel
@register_command(lambda m: m.content == '/gtfo', command_type=CommandType.VOICE)
async def gtfo(bot, message):
    """```
    Remove Senpai from her current voice channel and clear the current queue of songs.

    Usage:
    * /gtfo
    ```"""

    server = message.server
    state = _get_voice_state(bot, server)

    if state.is_playing():
        player = state.player
        player.stop()

    try:
        state.audio_player.cancel()
        del bot.voice_states[server.id]
        await state.voice.disconnect()

        # Delete old audio files
        if os.path.isdir('audio_cache'):
            shutil.rmtree('./audio_cache')
    finally:
        pass


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
