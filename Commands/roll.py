import discord
import asyncio
from random import *

def roll_die(num_sides):
    """Roll a single die of num_sides sides"""
    return randint(1, num_sides)

print(roll_die(20))
