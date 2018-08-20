import discord
import asyncio

def echo (client, message):
    """Copy user message after the echo statement"""
    print(message.channel)
    echoed_message = message.content[5:]
    print("Echoing message")
    return client.send_message(message.channel, "I heard you!")
