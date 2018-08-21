import discord
import asyncio
from random import *

def roll_die(num_sides):
    """Roll a single die of num_sides sides"""
    return randint(1, int(num_sides))

def sum_dice(dice_string):
    """Roll a sequence of die and add them up"""
    dice_sum = 0
    print(dice_string)
    die_list = dice_string.replace(" ","").split("+")
    print(die_list)
    for dice in die_list:
        quantity, size = dice.split('d',1)
        for i in range(0,int(quantity)):
            dice_sum += roll_die(size)
            print(dice_sum)
    return dice_sum

async def execute(client, message, args):
    """Roll a number of dice for the user, with modifiers, and return the result"""
    roll_result = sum_dice(args)
    await client.send_message(message.author, "{} rolled a total of {}".format(message.author, roll_result))
