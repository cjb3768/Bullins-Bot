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
    #TODO: check to see what kind of link is in args, if there even is one

    #find voice channel author is in
    logger.info(message.server.channels)

    for channel in message.server.channels:
        if message.author in channel.voice_members:
            logger.info("{} is in voice channel {}".format(message.author.display_name, channel.name))
            voice = await client.join_voice_channel(channel)
            #voice.disconnect()

    #TODO: make sure voice actually is connected to a valid channel

    client.player = await voice.create_ytdl_player(args, after=voice.disconnect)
    await client.send_message(message.channel, "Playing \"{}\" by {}, as requested by {}".format(player.title, player.uploader, message.author.display_name))
    client.player.start()

async def pause(client):
    """Pause stream playback"""
    #TODO: Make sure video exists and is playing
    if client.player.is_playing():
        await client.player.pause()
        await client.send_message(message.channel, "Stream paused."))
    else:
        await client.send_message(message.channel, "Nothing is playing right now."))

async def resume(client):
    """Resume stream playback"""
    #TODO: Make sure video exists and is paused
    if not client.player.is_playing():
        await client.player.resume()
        await client.send_message(message.channel, "Stream resumed."))
    else:
        await client.send_message(message.channel, "Playback isn't currently paused."))
