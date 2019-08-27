import discord
import asyncio
import logging

###########
# GLOBALS #
###########
logger = logging.getLogger("bullinsbot.echo")


def get_available_commands():
    return {"echo": execute}


async def execute(client, message, instruction, **kwargs):
    """Copy user message after the echo statement"""
    logger.debug("Echoing message: %s", ' '.join(instruction[1:]))
    await message.channel.send(' '.join(instruction[1:]))
