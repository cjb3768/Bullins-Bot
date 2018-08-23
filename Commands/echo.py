import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.echo")

async def execute(client, message, command, **kwargs):
    """Copy user message after the echo statement"""
    logger.debug("Echoing message: %s", ' '.join(command[1:]))
    await client.send_message(message.channel, ' '.join(command[1:]))
