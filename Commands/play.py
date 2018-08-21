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

    #voice = await client.join_voice_channel(message.author)
    #player = client.

    await client.send_message(message.author, "I'm playing music mommy/daddy!")
