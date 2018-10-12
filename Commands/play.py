import discord
import asyncio
import logging
import youtube_dl
import datetime
import functools
import os
import shutil

from collections import deque
from youtube_dl.utils import ExtractorError, DownloadError, UnsupportedError
from discord import ClientException

###########
# GLOBALS #
###########
logger = logging.getLogger("bullinsbot.play")


def get_available_commands():
    return {"play": execute, "pause": pause, "resume": resume, "stop": stop, "volume": set_volume, "queue":queue_info, "repeat":set_repeat_mode, "skip":skip_track}


class song_entry:
    def __init__(self, message, player):
        self.requester = message.author
        self.message_channel = message.channel
        self.player = player


    def __str__(self):
        return "\"{}\" by {}, requested by {}".format(self.player.title, self.player.uploader, self.requester.display_name)


class song_cache:
    def __init__(self):
        self.data = {}


    def cache_song(self, url, song_data):
        self.data[url] = song_data
        return


    def song_in_cache(self, url):
        return url in self.data


    def get_info_from_cache(self, url):
        return self.data[url]


    def __len__(self):
        return len(self.data)


class music_class:
    def __init__(self, client):
        self.playback_queue = deque()
        self.status = "inactive"
        self.repeat_mode = "off"
        self.voice_channel = client.voice
        self.active_player = None
        self.cache = client.song_cache


    def __len__(self):
        return len(self.playback_queue)


    @asyncio.coroutine
    def custom_create_ytdl_player(self, url, *, ytdl_options=None, **kwargs):
        """This is a modified copy of the "create_ytdl_player" function from discord.py.
        The big difference here is that this version caches data pulled from youtube_dl, as it appears to be the biggest bottleneck on playback,
        especially when trying to play a given song more than song_cache during a given bot lifecycle. """

        use_avconv = kwargs.get('use_avconv', False)
        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'prefer_ffmpeg': not use_avconv
        }

        if ytdl_options is not None and isinstance(ytdl_options, dict):
            opts.update(ytdl_options)

        # check to see if the song requested is already in the player cache
        if not self.cache.song_in_cache(url):
            #logger.info("Creating YTDL")
            ydl = youtube_dl.YoutubeDL(opts)
            #logger.info("Creating YTDL function")
            func = functools.partial(ydl.extract_info, url, download=False)
            #logger.info("Running YTDL function")
            info = yield from self.voice_channel.loop.run_in_executor(None, func)
            if "entries" in info:
                info = info['entries'][0]

            logger.info("Adding song to cache.")
            self.cache.cache_song(url, info)
            logger.debug(self.cache.data.keys())
            #logger.info(self.cache.data[url])
            logger.debug(info.keys())
            #player = self.voice_channel.create_ffmpeg_player(info['_filename'], **kwargs)

        else:
            logger.info("Song already in cache.")
            info = self.cache.get_info_from_cache(url)
            ydl = None  #songs pulled from cache won't have access to the youtube_dl object, but we never use it, so it's not a huge deal; if you are expanding this code and want that access, add it to 'info' before caching in the above 'if' block.

        logger.info('playing URL {}'.format(url))
        download_url = info['url']
        player = self.voice_channel.create_ffmpeg_player(download_url, **kwargs)

        # set the dynamic attributes from the info extraction
        player.download_url = download_url
        player.url = url
        player.yt = ydl
        player.views = info.get('view_count')
        player.is_live = bool(info.get('is_live'))
        player.likes = info.get('like_count')
        player.dislikes = info.get('dislike_count')
        player.duration = info.get('duration')
        player.uploader = info.get('uploader')

        is_twitch = 'twitch' in url
        if is_twitch:
            # twitch has 'title' and 'description' sort of mixed up.
            player.title = info.get('description')
            player.description = None
        else:
            player.title = info.get('title')
            player.description = info.get('description')

        # upload date handling
        date = info.get('upload_date')
        if date:
            try:
                date = datetime.datetime.strptime(date, '%Y%M%d').date()
            except ValueError:
                date = None

        player.upload_date = date
        return player


    async def add_song(self, client, message, url, append_right):
        """Create a new song and add it to playback_queue."""

        new_song = song_entry(message, await self.custom_create_ytdl_player(url, ytdl_options={}, after=lambda: self.advance_queue(client, message)))
        if append_right:
            self.playback_queue.append(new_song)
        else:
            self.playback_queue.appendleft(new_song)
        if self.active_player == None:
            self.active_player = self.playback_queue[0].player
        await client.send_message(message.channel, "Queued {}".format(new_song))


    def advance_queue(self, client, message):
        """Advance the song queue, based on the music object's current repeat mode."""

        if not self.status == "inactive":
            logger.info("Advancing queue.")
            logger.debug("Playback_queue length = {}, repeat_mode = {}".format(len(self.playback_queue),self.repeat_mode))

            logger.info("Popping track from queue.")
            self.playback_queue.popleft()

            # there are additional songs in the queue; move to the next one
            if len(self.playback_queue) >= 1:

                # if repeat is not set; set queue to next player
                if self.repeat_mode == "off":
                    repeat_coroutine = None;

                    logger.info("Queueing up next track.")
                    self.active_player = self.playback_queue[0].player

                    next_song_message = client.send_message(message.channel, "Now playing: {}".format(self.playback_queue[0]))
                    logger.info("Now playing: {}".format(self.playback_queue[0]))

                    queue_coroutine = self.active_player.start()

                # else repeat is set to all; insert a duplicate of the current song into the queue
                elif self.repeat_mode == "all":
                    logger.info("Repeat set to all, loading new copy of current player")
                    repeat_coroutine = self.add_song(client, message, self.active_player.url, True)

                else:
                    logger.info("Repeat set to current, loading new copy of current player")
                    repeat_coroutine = self.add_song(client, message, self.active_player.url, False)

            # the queue only had one song in it
            else:
                # repeat mode is off, meaning updating the queue emtpies it. Clear the queue, and disconnect.
                if self.repeat_mode == "off":
                    repeat_coroutine = None;

                    next_song_message = client.send_message(message.channel, "Queue empty. Disconnecting from voice channel.")
                    logger.info("Queue empty. Disconnecting from voice channel.")

                    queue_coroutine = self.voice_channel.disconnect()

                # either repeat is set to "current" or "all;" since our queue is one song long, both behave the same
                else:
                    logger.info("Repeat set to either current or all, loading new copy of current player")
                    repeat_coroutine = self.add_song(client, message, self.active_player.url, True)

            # handle repeat coroutine for cases where repeat is not off
            if not repeat_coroutine == None:
                logger.debug("Assigning repeat_future")
                repeat_future = asyncio.run_coroutine_threadsafe(repeat_coroutine, client.loop)

                try:
                    logger.debug("Checking repeat_future")
                    repeat_future.result()

                    logger.info("Queueing up next track.")
                    self.active_player = self.playback_queue[0].player

                    next_song_message = client.send_message(message.channel, "Now playing: {}".format(self.playback_queue[0]))
                    logger.info("Now playing: {}".format(self.playback_queue[0]))

                    queue_coroutine = self.active_player.start()

                except Exception as e:
                    # an error occurred
                    logger.error("An exception of type {} has occurred".format(type(e).__name__))
                    logger.error(e)

            # send a message associated with the update to the queue.
            message_future = asyncio.run_coroutine_threadsafe(next_song_message, client.loop)

            try:
                message_future.result()
            except Exception as e:
                # an error occurred
                logger.error("An exception of type {} has occurred".format(type(e).__name__))
                logger.error(e)

            # run the assigned queue coroutine
            queue_future = asyncio.run_coroutine_threadsafe(queue_coroutine, client.loop)

            try:
                queue_future.result()
            except Exception as e:
                # an error occurred
                logger.error("An exception of type {} has occurred".format(type(e).__name__))
                logger.error(e)


    def set_status(self, new_status):
        self.status = new_status


async def execute(client, message, instruction, **kwargs):
    """Stream audio from an online source over a given voice channel.
       Currently supported websites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
    """

    #Attempt to connect to voice channel
    try:
        await connect_to_voice_channel(client, message)
        if not hasattr(client, 'song_cache'):
            client.song_cache = song_cache()

        client.music = music_class(client)

    except ClientException:
        logger.warning("Client is already in a voice channel.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)


    #Attempt to load and play a video
    try:
        #Check to see if the music class has a player running already
        if client.music.active_player == None:
            #there isn't an active player; add a song and start playing.
            logger.info("No active player was found. Adding song.")
            await client.music.add_song(client, message, instruction[1], True)
            logger.info("Queue currently contains {} songs.".format(len(client.music)))
            logger.info("Playing song.")

            client.music.active_player.start()
            client.music.set_status("playing")

        else:
            #there is an active player
            logger.warning("Existing player found. Adding song to queue.")
            if client.music.status in ["playing","paused"]:
                #a song is currently playing or paused; add track to back of queue_info
                await client.music.add_song(client, message, instruction[1], True)
                logger.info("Queue currently contains {} songs.".format(len(client.music)))

            else:
                #this is a sanity check to make sure I'm updating the status flag right; if this calls, we have a problem
                logger.error("You shouldn't be seeing this.")

    #TODO: make a function to handle shutdown on errors in a more uniform way
    except AttributeError as e:
        logger.error("User not connected to voice channel.")
        logger.error(e)
        await client.send_message(message.channel, "Error: Requester isn't in a voice channel.")

    except DownloadError:
        logger.error("Unable to download video")
        await client.send_message(message.channel, "Error: Invalid link.")
        logger.error(e)
        await client.voice.disconnect()

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        await client.send_message(message.channel, "An unknown error has occurred.")
        logger.error(e)
        await client.voice.disconnect()


async def connect_to_voice_channel(client, message):
    #find voice channel author is in
    logger.debug(message.server.channels)

    for channel in message.server.channels:
        if message.author in channel.voice_members:
            logger.info("{} is in voice channel {}. Joining.".format(message.author.display_name, channel.name))
            client.voice = await client.join_voice_channel(channel)


async def queue_info(client, message, instruction, **kwargs):
    """Reports a list of information about the songs currently in the playback queue."""
    message_string = "The current playback queue contains the following {} song(s):".format(len(client.music.playback_queue))
    logger.info(message_string)
    await client.send_message(message.channel, message_string)
    for song in client.music.playback_queue:
        logger.info(song)
        await client.send_message(message.channel, song)


async def pause(client, message, instruction, **kwargs):
    """Pause stream playback."""

    try:
        if client.music.status == "playing":
            logger.info("Pausing playback")
            client.music.active_player.pause()
            client.music.set_status("paused")
            await client.send_message(message.channel, "Stream paused.")
        else:
            await client.send_message(message.channel, "Nothing is playing right now.")

    except AttributeError:
        logger.error("No stream player to pause.")
        await client.send_message(message.channel, "Error: No stream to pause.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        await client.send_message(message.channel, "An unknown error has occured")


async def resume(client, message, instruction, **kwargs):
    """Resume stream playback."""

    try:
        if client.music.status == "paused":
            logger.info("Resuming playback")
            client.music.set_status("playing")
            client.music.active_player.resume()
            await client.send_message(message.channel, "Stream resumed.")

        else:
            await client.send_message(message.channel, "Playback isn't currently paused.")

    except AttributeError:
        logger.error("No stream player to resume.")
        await client.send_message(message.channel, "Error: No stream to resume.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        await client.send_message(message.channel, "An unknown error has occured")


async def stop(client, message, instruction, **kwargs):
    """Stops stream playback."""
    try:
        logger.info("Stopping playback")
        client.music.set_status("inactive")
        client.music.active_player.stop()

        await client.send_message(message.channel, "Stream stopped.")
        await client.voice.disconnect()

    except AttributeError:
        logger.error("No stream player to stop.")
        await client.send_message(message.channel, "Error: No stream to stop.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        await client.send_message(message.channel, "An unknown error has occured")


def limit_volume(volume_level):
    if volume_level > 1:
        return 1
    elif volume_level < 0:
        return 0
    else:
        return volume_level


async def adjust_volume(client, message, instruction):
    #handle differences in input between "volume +/- x" and "volume +x/-x"
    if len(instruction) == 2:
        volume_adjustment = int(instruction[1][1:])/100
    else:
        volume_adjustment = int(instruction[2])/100

    logger.info("attempting to adjust volume by %s", volume_adjustment)

    if instruction[1].startswith('+'):
        client.music.active_player.volume = limit_volume(client.music.active_player.volume + volume_adjustment)
    else:
        client.music.active_player.volume = limit_volume(client.music.active_player.volume - volume_adjustment)

    logger.info("Volume adjusted to {:.0%}.".format(client.music.active_player.volume))
    await client.send_message(message.channel, "Volume adjusted to {:.0%}.".format(client.music.active_player.volume))


async def set_volume(client, message, instruction, **kwargs):
    """Reports or allows for manual setting or adjustment of the volume of the active stream.
       Available options:
       <no option> - returns the current volume level of the active stream.
       "+/- x" - raises or lowers the volume by x percent. Values of x that would push the volume above 100% or below 0% round out to those values.
       "x" - sets the stream volume to an exact percentage. Volume percentages above 100% or below 0% round to those values."""

    try:
        if len(instruction) == 1:
            logger.info("current volume: %s", client.music.active_player.volume)
            await client.send_message(message.channel, "Song is currently playing at {:.0%}.".format(client.music.active_player.volume))

        elif instruction[1][0] in ['+','-']:
            await adjust_volume(client, message, instruction)

        else:
            volume_adjustment = int(instruction[1])/100
            logger.info("attempting to manually set volume")
            client.music.active_player.volume = limit_volume(volume_adjustment)
            logger.info("Set volume to {:.0%}.".format(client.music.active_player.volume))
            await client.send_message(message.channel, "Set volume to {:.0%}.".format(client.music.active_player.volume))

    except ValueError:
        logger.error("Attempted to adjust volume by something other than a number")
        await client.send_message(message.channel, "Error: Invalid volume change")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        await client.send_message(message.channel, "An unknown error has occurred.")
        await client.voice.disconnect()


async def set_repeat_mode(client, message, instruction, **kwargs):
    """Sets the repeat mode for the playback queue.
       Available options:
       "all" - set repeat to loop entire queue
       "current" - set repeat to loop current song only
       "off" - turn off repeat
       nothing - report repeat mode"""

    try:
        if len(instruction) == 1:
            message_string = "Repeat mode: {}".format(client.music.repeat_mode)
            logger.info(message_string)
            await client.send_message(message.channel, message_string)

        elif instruction[1] in ["all", "current", "off"]:
            client.music.repeat_mode = instruction[1]
            message_string = "Setting repeat mode to \"{}\".".format(instruction[1])
            logger.info(message_string)
            await client.send_message(message.channel, message_string)

        else:
            logger.error("Invalid repeat mode.")
            await client.send_message(message.channel, "Invalid repeat mode setting. Please choose between \"all\", \"current\", or \"off\".")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)


async def skip_track(client, message, instruction, **kwargs):
    """Skips the current track in the song queue.
       Note: Skip will not proceed through the queue if repeat mode is set to 'current.'"""
    if message.author == client.music.playback_queue[0].requester:
        message_string = "Song skip requested by song requestor. Playing next song."
    else:
        message_string = "Song skip requested. Playing next song."
    logger.info(message_string)
    await client.send_message(message.channel, message_string)
    client.music.active_player.stop()
