import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.clean")

async def execute(client, message, args, _):
    """Deletes all past bot commands and replies from requested channel"""
