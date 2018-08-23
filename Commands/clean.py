import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.clean")

def get_available_commands():
    return {"clean": execute}

async def execute(client, message, instruction, **kwargs):
    """Deletes a number of past bot commands and replies from requested channel"""
    def bot_related(m):
        return m.content.startswith(client.invocation) or m.author == client.user

    deleted_messages = await client.purge_from(message.channel, limit=int(instruction[1]), check=bot_related)

    logger.info("Deleted %d bot-related messages from channel.", len(deleted_messages))
