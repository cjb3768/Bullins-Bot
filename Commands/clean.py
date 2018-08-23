import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.clean")

async def execute(client, message, command, **kwargs):
    """Deletes a number of past bot commands and replies from requested channel"""
    def bot_related(m):
        return m.content.startswith(client.invocation) or m.author == client.user

    deleted_messages = await client.purge_from(message.channel, limit=int(command[1]), check=bot_related)

    logger.info("Deleted %d bot-related messages from channel.", len(deleted_messages))
