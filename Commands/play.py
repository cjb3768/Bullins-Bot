import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.play")

async def execute(client, message, args, _):
    """Play music from an online source back over a given voice channel
       Supported platforms will be added to this note as they are added

       Currently supported:

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

    player = await voice.create_ytdl_player(args, after=voice.disconnect)
    await client.send_message(message.channel, "Playing \"{}\" by {}, as requested by {}".format(player.title, player.uploader, message.author.display_name))
    #player.start()

    #await client.send_message(message.author, "I'm playing music mommy/daddy!")
