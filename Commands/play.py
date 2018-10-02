import discord
import asyncio
import logging
from collections import deque
from youtube_dl.utils import ExtractorError, DownloadError, UnsupportedError
from discord import ClientException

logger = logging.getLogger("bullinsbot.play")

logger.info("Attempting to load opus")
discord.opus.load_opus
logger.info("Opus loaded")

def get_available_commands():
    return {"play": execute, "pause": pause, "resume": resume, "stop": stop, "volume": set_volume, "queue":queue_info, "repeat":set_repeat_mode}

async def execute(client, message, instruction, **kwargs):
    """Stream from an online source back over a given voice channel
       Supported platforms will be added to this note as they are added

       Currently supported formats can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
    """
    #this is a video request; connect to channel if not already connected, load stream, and play

    #Attempt to connect to voice channel
    try:
        await connect_to_voice_channel(client, message)

    except ClientException:
        logger.warning("Client is already in a voice channel.")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)

    #attempt to load and play a video
    try:
        #check to see if client has a playback queue; if not, create one
        if not hasattr(client,"playback_queue"):
            client.playback_queue = deque()
            # default repeat mode to off
            client.repeat_mode = "off"

        #check to see if client already has a player
        if hasattr(client,"player"):
            #check to make sure client isn't playing
            logger.warning("Client already has a player.")
            if not client.player.is_playing():
                logger.warning("Replacing existing player.")
                await load_youtube_video(client, message, instruction[1])
                logger.info("Queue currently contains {} songs.".format(len(client.playback_queue)))
                await start_stream(client)
            #client is playing; log an error
            else:
                logger.warning("Existing player active.");
                await load_youtube_video(client, message, instruction[1])
                logger.info("Queue currently contains {} songs.".format(len(client.playback_queue)))

        else:
            await load_youtube_video(client, message, instruction[1])
            logger.info("Queue currently contains {} songs.".format(len(client.playback_queue)))
            await start_stream(client)

    except AttributeError as e:
        logger.error("User not connected to voice channel.")
        logger.error(e)
        await client.send_message(message.channel, "Error: Requestor isn't in a voice channel.")

    except DownloadError:
        logger.error("Unable to download video")
        await client.send_message(message.channel, "Error: Invalid link.")
        await client.voice.disconnect()

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        await client.send_message(message.channel, "An unknown error has occurred.")
        await client.voice.disconnect()

async def connect_to_voice_channel(client, message):
    #find voice channel author is in
    logger.info(message.server.channels)

    for channel in message.server.channels:
        if message.author in channel.voice_members:
            logger.info("{} is in voice channel {}. Joining.".format(message.author.display_name, channel.name))
            client.voice = await client.join_voice_channel(channel)

async def load_youtube_video(client, message, url):
    """Create a youtube download player to stream audio from a youtube video.
       Loaded player is added to playback queue, and if there is not an active player, the new player is set as the client's active player."""
    client.playback_queue.append(await client.voice.create_ytdl_player(url, after=lambda: advance_queue(client, message))) #TODO: get the after function working
    #if the video just loaded into the queue is the only video in the queue, set its player as the active player
    if (len(client.playback_queue) == 1):
        client.player = client.playback_queue[0]
    await client.send_message(message.channel, "Queued \"{}\" by {}, as requested by {}".format(client.playback_queue[-1].title, client.playback_queue[-1].uploader, message.author.display_name))

async def start_stream(client):
    client.player.start()

async def queue_info(client, message, instruction, **kwargs):
    """Reports a list of information about the songs currently in the playback queue."""
    #TODO- check to make sure there is a queue to look through
    await client.send_message(message.channel, "The current playback queue contains the following {} songs:".format(len(client.playback_queue)))
    for song in client.playback_queue:
        await client.send_message(message.channel, "\"{}\" by {}".format(song.title, song.uploader))

async def pause(client, message, instruction, **kwargs):
    """Pause stream playback"""

    try:
        if client.player.is_playing():
            logger.info("Pausing playback")
            client.player.pause()
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
        if client.player.is_playing():
            await client.send_message(message.channel, "Playback isn't currently paused.")
        else:
            logger.info("Resuming playback")
            client.player.resume()
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
        client.player.stop()
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
        client.player.volume = limit_volume(client.player.volume + volume_adjustment)
    else:
        client.player.volume = limit_volume(client.player.volume - volume_adjustment)

    logger.info("Volume adjusted to {:.0%}.".format(client.player.volume))
    await client.send_message(message.channel, "Volume adjusted to {:.0%}.".format(client.player.volume))

async def set_volume(client, message, instruction, **kwargs):
    """Reports or allows for manual setting or adjustment of the volume of the active stream."""

    try:
        if len(instruction) == 1:
            logger.info("current volume: %s", client.player.volume)
            await client.send_message(message.channel, "Song is currently playing at {:.0%}.".format(client.player.volume))

        elif instruction[1][0] in ['+','-']:
            await adjust_volume(client, message, instruction)

        else:
            volume_adjustment = int(instruction[1])/100
            logger.info("attempting to manually set volume")
            client.player.volume = limit_volume(volume_adjustment)
            logger.info("Set volume to {:.0%}.".format(client.player.volume))
            await client.send_message(message.channel, "Set volume to {:.0%}.".format(client.player.volume))

    except ValueError:
        logger.error("Attempted to adjust volume by something other than a number")
        await client.send_message(message.channel, "Error: Invalid volume change")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        await client.send_message(message.channel, "An unknown error has occurred.")
        await client.voice.disconnect()


def advance_queue(client, message):
    # there are additional songs in the queue; move to the next one
    if (len(client.playback_queue) > 1):
        # if repeat is not set, pop old song out of the queue and prep next one
        if client.repeat_mode == "off":
            client.playback_queue.popleft()
            client.player = client.playback_queue[0]

        # else if repeat is set to all, rotate queue to the left once
        elif client.repeat_mode == "all":
            client.playback_queue.rotate(-1)
            client.player = client.playback_queue[0]

        # else repeat is set to current; do nothing (we can just play the song again)
        else:
            pass

        next_song_message = client.send_message(message.channel, "Now playing: \"{}\" by {}".format(client.player.title, client.player.uploader))
        logger.info("Now playing: \"{}\" by {}".format(client.player.title, client.player.uploader))

        queue_coroutine = start_stream(client)

    # the queue only had one song in it
    else:
        # repeat mode is off, meaning updating the queue emtpies it. Clear the queue, and disconnect.
        if client.repeat_mode == "off":
            next_song_message = client.send_message(message.channel, "Queue empty. Disconnecting from voice channel.")
            logger.info("Queue empty. Disconnecting from voice channel.")

            client.playback_queue.clear()
            queue_coroutine = client.voice.disconnect()

        # either repeat is set to "current" or "all;" since our queue is one song long, both behave the same
        else:
            next_song_message = client.send_message(message.channel, "Now playing: \"{}\" by {}".format(client.player.title, client.player.uploader))
            logger.info("Now playing: \"{}\" by {}".format(client.player.title, client.player.uploader))

            queue_coroutine = start_stream(client)

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


async def set_repeat_mode(client, message, instruction, **kwargs):
    """Sets the repeat mode for the playback queue.
       Available options:
       "all" - set repeat to loop entire queue
       "current" - set repeat to loop current song only
       "off" - turn off repeat
       nothing - report repeat mode"""

    try:
        if len(instruction) == 1:
            logger.info("Repeat mode: {}".format(client.repeat_mode))
            await client.send_message(message.channel, "Repeat mode: {}".format(client.repeat_mode))

        elif instruction[1] in ["all", "current", "off"]:
            client.repeat_mode = instruction[1]
            logger.info("Setting repeat mode to \"{}\".".format(instruction[1]))
            await client.send_message(message.channel, "Setting repeat mode to \"{}\".".format(instruction[1]))

        else:
            logger.error("Invalid repeat mode.")
            await client.send_message(message.channel, "Invalid repeat mode setting. Please choose between \"all\", \"current\", or \"off\".")

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
