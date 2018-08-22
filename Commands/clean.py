import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.clean")

def is_bot_response(client, message):
    return message.author == client.user

def is_bot_request(client, message):
    return message.content.startswith(client.invocation)

async def execute(client, message, args, _):
    """Deletes all past bot commands and replies from requested channel"""
    async for log in client.logs_from(message.channel):
        if is_bot_request(client, log) or is_bot_response(client, log):
            await client.delete_message(log)
