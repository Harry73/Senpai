import os
import shutil
import logging
import discord
import asyncio
import functools
import youtube_dl
from concurrent.futures import ThreadPoolExecutor
from collections import deque

from lib.Message import Message
from lib import IDs

LOGGER = logging.getLogger('Senpai')

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
            LOGGER.debug('Voice.audio_player_task: now playing %s', str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()


# Class for voice related commands
class Music:

    def __init__(self, bot):
        self.bot = bot
        self.downloader = None
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            finally:
                pass

    # Summons the bot to join the voice channel the message author is in
    async def summon(self, message):
        summoned_channel = message.author.voice_channel
        if summoned_channel is None:
            return Message(message='You are not in a voice channel')

        # Keep Senpai out of the DnD voice channel
        if summoned_channel in IDs.BLACKLISTED_VOICE_CHANNELS:
            return Message(message='DnD voice channel is blacklisted')

        LOGGER.debug('Voice.summon: joining %s', summoned_channel)
        state = self.get_voice_state(message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

    # Plays a song. If something is playing, the request will be queued
    # Also automatically searches YouTube for the song
    async def play(self, message, song: str):
        # Requester must be in a voice channel to use '/play' command
        if message.author.voice_channel is None:
            return Message(message='You are not in a voice channel.')

        LOGGER.debug('Voice.play: play %s', song)

        if not song:
            await self._resume(message)
            return {}

        state = self.get_voice_state(message.server)

        if state.voice is None or str(message.author.voice_channel) != str(state.voice.channel):
            response = await self.summon(message)
            if response:
                return response

        try:
            if not self.downloader:
                self.downloader = Downloader(download_folder='audio_cache')

            # Check info
            info = await self.downloader.extract_info(self.bot.loop, song, download=False)

            if not info:
                LOGGER.warning('Voice.play: failed to extract info')
                return Message(message='Failed to extract info from the video')
            else:
                if 'entries' in info:
                    info = info['entries'][0]

                song_url = info['webpage_url']
                LOGGER.debug('Voice.play: song url %s', song_url)

                result = await self.downloader.safe_extract_info(self.bot.loop, song_url, download=True)
                if not result:
                    raise Exception('Death, and idk why')

                # Get filename and then create player for the file
                filename = self.downloader.ytdl.prepare_filename(result)
                player = state.voice.create_ffmpeg_player(
                    filename,
                    before_options='-nostdin',
                    options='-vn -b:a 128k',
                    after=lambda: state.toggle_next(filename)
                )
                player.url = song
                player.title = result['title']
        except Exception as e:
            LOGGER.exception(e)
        else:
            player.volume = 0.6
            entry = VoiceEntry(message, player)
            await state.songs.put(entry)
            state.songs_queue.append(entry)

    # Plays a clip song. If something is playing, the request will be queued
    # Also automatically searches YouTube for the song
    async def play_mp3(self, message, clip: str):
        # Requester must be in a voice channel to use '/<sound>' command
        if message.author.voice_channel is None:
            return Message(message='You are not in a voice channel.')

        LOGGER.debug('Voice.play_mp3: play mp3 %s', clip)

        state = self.get_voice_state(message.server)

        if state.voice is None:
            response = await self.summon(message)
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
            LOGGER.exception(e)
        else:
            player.volume = 0.6
            entry = VoiceEntry(message, player)
            await state.songs.put(entry)
            state.songs_queue.append(entry)

    # Pauses the currently playing song
    async def pause(self, message):
        state = self.get_voice_state(message.server)
        if state.is_playing():
            player = state.player
            player.pause()
            LOGGER.debug('Voice.pause: paused music')

    # Resumes the currently playing song, internal method
    async def _resume(self, message):
        state = self.get_voice_state(message.server)
        if state.is_playing():
            player = state.player
            player.resume()
            LOGGER.debug('Voice._resume: resumed music')

    # Return a list of song titles in the queue
    async def queue(self, message):
        LOGGER.debug('Voice.queue: request')

        state = self.get_voice_state(message.server)

        if state.songs_queue:
            song_list = []
            for song in state.songs_queue:
                if hasattr(song.player, 'title'):
                    song_list.append(song.player.title)

            response = 'Songs currently in the queue:\n'
            response += '\n'.join(song_list)
        else:
            response = 'No songs queued'

        LOGGER.debug('Voice.queue: response, %s', response)
        return Message(message=response)

    # Return the currently playing song
    async def np(self, message):
        LOGGER.debug('Voice.np: request')

        state = self.get_voice_state(message.server)

        if state.current:
            LOGGER.debug('Voice.np: response, %s', state.current.player.title)
            return Message(message='Now playing: {0}'.format(state.current.player.title))
        else:
            LOGGER.debug('Voice.np: not playing')
            return Message(message='Not playing any music right now...')

    # Skip a song
    async def skip(self, message):
        LOGGER.debug('Voice.skip: request')

        state = self.get_voice_state(message.server)
        if not state.is_playing():
            LOGGER.debug('Voice.skip: not playing')
            return Message(message='Not playing any music right now...')

        state.skip()

    # Stops the song and clears the queue
    async def stop(self, message):
        LOGGER.debug('Voice.stop: request')

        server = message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()
            state.songs = asyncio.Queue()
            state.songs_queue = deque()

    # Stops the song, clears the queue, and leaves the channel
    async def gtfo(self, message):
        server = message.server
        state = self.get_voice_state(server)

        LOGGER.debug('Voice.gtfo: leaving voice channel')
        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()

            # Delete old audio files
            if os.path.isdir('audio_cache'):
                shutil.rmtree('./audio_cache')
        finally:
            pass
