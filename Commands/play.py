import discord
import asyncio
import logging

async def execute(client, message, args):
    """Play music from an online source back over a given voice channel
       Supported platforms will be added to this note as they are added

       Currently supported:

    """
    await client.send_message(message.author, "I'm playing music mommy/daddy!")
