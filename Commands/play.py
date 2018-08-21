import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.play")

async def execute(client, message, args, _):
    """Stream from an online source back over a given voice channel
       Supported platforms will be added to this note as they are added

       Currently supported:
       Youtube videos
    """

    #TODO: make sure voice actually is connected to a valid channel

    if args.startswith("http"):
        #this is a video request; connect to channel if not already connected, load stream, and play
        #TODO: Check to see if client connected to a voice channel already
        await connect_to_voice_channel(client, message)
        #TODO: check to see what kind of link is in args; right now assuming youtube
        await load_youtube_video(client, message, args)
        await start_stream(client)

    elif args.startswith("pause"):
        await pause(client)

    elif args.startswith("resume"):
        await resume(client)


async def connect_to_voice_channel(client,message):
    #find voice channel author is in
    logger.info(message.server.channels)

    for channel in message.server.channels:
        if message.author in channel.voice_members:
            logger.info("{} is in voice channel {}. Joining.".format(message.author.display_name, channel.name))
            client.voice = await client.join_voice_channel(channel)
    #TODO: Handle when the user isn't connected to a channel

async def load_youtube_video(client,message,args):
    """Create a youtube download player to stream audio from a youtube video"""
    client.player = await client.voice.create_ytdl_player(args, after=client.voice.disconnect) #TODO: get the after function working
    await client.send_message(message.channel, "Loaded \"{}\" by {}, as requested by {}".format(client.player.title, client.player.uploader, message.author.display_name))

async def start_stream(client):
    #TODO: Make sure player exists and video loaded
    client.player.start()

async def pause(client):
    """Pause stream playback"""
    #TODO: Make sure player exists
    if client.player.is_playing():
        await client.player.pause()
        await client.send_message(message.channel, "Stream paused.")
    else:
        await client.send_message(message.channel, "Nothing is playing right now.")

async def resume(client):
    """Resume stream playback"""
    #TODO: Make sure player exists
    if client.player.is_playing():
        await client.send_message(message.channel, "Playback isn't currently paused.")
    else:
        await client.player.resume()
        await client.send_message(message.channel, "Stream resumed.")
