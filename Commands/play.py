import discord
import asyncio
import logging
import youtube_dl
import datetime
import functools

from collections import deque
from youtube_dl.utils import ExtractorError, DownloadError, UnsupportedError
from discord import ClientException

logger = logging.getLogger("bullinsbot.play")

def get_available_commands():
    return {"play": execute, "pause": pause, "resume": resume, "stop": stop, "volume": set_volume, "queue":queue_info, "repeat":set_repeat_mode}

class song_entry:
    def __init__(self, message, player):
        self.requester = message.author
        self.message_channel = message.channel
        self.player = player

    def __str__(self):
        return "\"{}\" by {}, requested by {}".format(self.player.title, self.player.uploader, self.requester.display_name)

class song_queue:
    def __init__(self, client):
        self.playback_queue = deque()
        self.play_status = "inactive"
        self.repeat_mode = "off"
        self.voice_channel = client.voice
        self.active_player = None

    def __len__(self):
        return len(self.playback_queue)

    @asyncio.coroutine
    def custom_create_ytdl_player(self, url, *, ytdl_options=None, **kwargs):
        # This is more or less a direct copy of the "create_ytdl_player" function from discord.py
        # However, this one allows for downloading with youtube_dl, and will instead load a stream player
        # if a song has already been downloaded.

        use_avconv = kwargs.get('use_avconv', False)
        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'prefer_ffmpeg': not use_avconv
        }

        if ytdl_options is not None and isinstance(ytdl_options, dict):
            opts.update(ytdl_options)

        logger.info("Creating YTDL")
        ydl = youtube_dl.YoutubeDL(opts)
        logger.info("Creating YTDL function")
        func = functools.partial(ydl.extract_info, url, download=False)
        logger.info("Running YTDL function")
        info = yield from self.voice_channel.loop.run_in_executor(None, func)
        if "entries" in info:
            info = info['entries'][0]

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

    async def add_song(self, client, message, url):
        """Create a new song and add it to playback_queue"""
        new_song = song_entry(message, await self.custom_create_ytdl_player(url, ytdl_options={"download-archive": "archive.txt"}, after=lambda: self.advance_queue(client, message)))
        self.playback_queue.append(new_song)
        if self.active_player == None:
            self.active_player = self.playback_queue[0].player
        await client.send_message(message.channel, "Queued {}".format(self.playback_queue[-1]))

    async def add_song_left(self, client, message, url):
        """Create a new song and add it to playback_queue"""
        new_song = song_entry(message, await self.custom_create_ytdl_player(url, ytdl_options={"download-archive": "archive.txt"}, after=lambda: self.advance_queue(client, message)))
        self.playback_queue.appendleft(new_song)
        if self.active_player == None:
            self.active_player = self.playback_queue[0].player
        await client.send_message(message.channel, "Queued {}".format(self.playback_queue[0]))

    def advance_queue(self, client, message):

        if not self.play_status == "stopped":
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
                    repeat_coroutine = self.add_song(client, message, self.active_player.url)

                else:
                    logger.info("Repeat set to current, loading new copy of current player")
                    repeat_coroutine = self.add_song_left(client, message, self.active_player.url)

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
                    repeat_coroutine = self.add_song(client, message, self.active_player.url)

            # handle repeat coroutine for cases where repeat is not off
            if repeat_coroutine is not None:
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


async def execute(client, message, instruction, **kwargs):
    """Stream from an online source back over a given voice channel
       Supported platforms will be added to this note as they are added

       Currently supported formats can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
    """
    #this is a video request; connect to channel if not already connected, load stream, and play

    #Attempt to connect to voice channel
    try:
        await connect_to_voice_channel(client, message)
        client.song_queue = song_queue(client)

    except ClientException:
        logger.warning("Client is already in a voice channel.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)

    #attempt to load and play a video
    try:
        #check to see if client already has a player
        if client.song_queue.active_player is not None:
            #check to make sure client isn't playing TODO: Get working when stream is paused (stream isn't playing, but has started before, leading to errors)
            logger.warning("Client already has a player.")
            if not client.song_queue.active_player.is_playing():
                logger.warning("Replacing existing player.")
                await client.song_queue.add_song(client, message, instruction[1])
                logger.info("Queue currently contains {} songs.".format(len(client.song_queue)))
                client.song_queue.active_player.start()
            #client is playing; log an error
            else:
                logger.warning("Existing player active.");
                await client.song_queue.add_song(client, message, instruction[1])
                logger.info("Queue currently contains {} songs.".format(len(client.song_queue)))

        else:
            await client.song_queue.add_song(client, message, instruction[1])
            logger.info("Queue currently contains {} songs.".format(len(client.song_queue)))
            #await start_stream(client)
            client.song_queue.active_player.start()

    except AttributeError as e:
        logger.error("User not connected to voice channel.")
        logger.error(e)
        await client.send_message(message.channel, "Error: Requestor isn't in a voice channel.")

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
    logger.info(message.server.channels)

    for channel in message.server.channels:
        if message.author in channel.voice_members:
            logger.info("{} is in voice channel {}. Joining.".format(message.author.display_name, channel.name))
            client.voice = await client.join_voice_channel(channel)

async def queue_info(client, message, instruction, **kwargs):
    """Reports a list of information about the songs currently in the playback queue."""
    await client.send_message(message.channel, "The current playback queue contains the following {} songs:".format(len(client.playback_queue)))
    for song in client.playback_queue:
        await client.send_message(message.channel, "\"{}\" by {}".format(song.title, song.uploader))

async def pause(client, message, instruction, **kwargs):
    """Pause stream playback"""

    try:
        if client.song_queue.active_player.is_playing():
            logger.info("Pausing playback")
            client.song_queue.active_player.pause()
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
    """Resume stream playback"""
    try:
        if client.song_queue.active_player.is_playing():
            await client.send_message(message.channel, "Playback isn't currently paused.")
        else:
            logger.info("Resuming playback")
            client.song_queue.active_player.resume()
            await client.send_message(message.channel, "Stream resumed.")

    except AttributeError:
        logger.error("No stream player to resume.")
        await client.send_message(message.channel, "Error: No stream to resume.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        await client.send_message(message.channel, "An unknown error has occured")

async def stop(client, message, instruction, **kwargs):
    """Stops stream playback"""
    try:
        logger.info("Stopping playback")
        client.song_queue.play_status = "stopped"
        client.song_queue.active_player.stop()
        await client.send_message(message.channel, "Stream stopped.")
        client.song_queue.playback_queue.clear()
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
        client.song_queue.active_player.volume = limit_volume(client.song_queue.active_player.volume + volume_adjustment)
    else:
        client.song_queue.active_player.volume = limit_volume(client.song_queue.active_player.volume - volume_adjustment)

    logger.info("Volume adjusted to {:.0%}.".format(client.song_queue.active_player.volume))
    await client.send_message(message.channel, "Volume adjusted to {:.0%}.".format(client.song_queue.active_player.volume))

async def set_volume(client, message, instruction, **kwargs):
    """Reports or allows for manual setting or adjustment of the volume of the active stream."""

    try:
        if len(instruction) == 1:
            logger.info("current volume: %s", client.song_queue.active_player.volume)
            await client.send_message(message.channel, "Song is currently playing at {:.0%}.".format(client.song_queue.active_player.volume))

        elif instruction[1][0] in ['+','-']:
            await adjust_volume(client, message, instruction)

        else:
            volume_adjustment = int(instruction[1])/100
            logger.info("attempting to manually set volume")
            client.song_queue.active_player.volume = limit_volume(volume_adjustment)
            logger.info("Set volume to {:.0%}.".format(client.song_queue.active_player.volume))
            await client.send_message(message.channel, "Set volume to {:.0%}.".format(client.song_queue.active_player.volume))

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
            message_string = "Repeat mode: {}".format(client.song_queue.repeat_mode)
            logger.info(message_string)
            await client.send_message(message.channel, message_string)

        elif instruction[1] in ["all", "current", "off"]:
            client.song_queue.repeat_mode = instruction[1]
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
