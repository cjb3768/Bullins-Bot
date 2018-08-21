import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.echo")

async def execute(client, message, args, _):
    """Copy user message after the echo statement"""
    logger.debug("Echoing message: %s", args)
    await client.send_message(message.channel, args)
