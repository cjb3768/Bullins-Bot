import discord
import asyncio
from random import *

def roll_die(num_sides):
    """Roll a single die of num_sides sides"""
    return randint(1, int(num_sides))

def sum_dice(dice_string):
    """Roll a sequence of die and add them up; also reports all roll results"""
    dice_sum = 0
    result_string = ""
    die_list = dice_string.replace(" ","").split("+")
    for dice in die_list:
        quantity, size = dice.split('d',1)
        for i in range(0,int(quantity)):
            roll_result = roll_die(size)
            dice_sum += roll_result
            if result_string == "":
                result_string = str(roll_result)
            else:
                result_string = result_string + " + " + str(roll_result)
            print(result_string)
    return [dice_sum, result_string]

async def execute(client, message, args):
    """Roll a number of dice for the user, without modifiers, and return the result"""
    roll_result = sum_dice(args)
    await client.send_message(message.author, "{} rolled a total of {} ({})".format(message.author, roll_result[0], roll_result[1]))
