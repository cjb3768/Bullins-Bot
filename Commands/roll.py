import discord
import asyncio
from random import *

def roll_die(num_sides):
    """Roll a single die of num_sides sides"""
    return randint(1, int(num_sides))

async def execute(client, message, args):
    """Roll a number of dice for the user, with modifiers, and return the result"""
    roll_result = roll_die(args)
    await client.send_message(message.author, "{} rolled a {}".format(message.author, roll_result))
