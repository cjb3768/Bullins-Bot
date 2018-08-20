import discord
import asyncio

async def execute(client, message, args):
    """Copy user message after the echo statement"""
    #print("Echoing message")
    await client.send_message(message.channel, args)
