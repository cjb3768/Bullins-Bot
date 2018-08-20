import discord
import asyncio

async def execute(client, message, args):
    """Send user a private message with a list of all supported functions"""
    await client.send_message(message.author, "This is a help message")
