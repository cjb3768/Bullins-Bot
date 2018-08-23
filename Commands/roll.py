import discord
import asyncio
import logging
from random import *

logger = logging.getLogger("bullinsbot.roll")

def eval_dice(dice_string):
    """Takes in a string of dice rolls and modifiers, splits on operators, and calls sub functions to handle calculation"""
    dice_totals = (0,"")

    #logger.info("Dice string is {}".format(dice_string))
    #check to make sure an addition isn't taking place
    if dice_string.find('+') != -1:
        left, right = dice_string.split("+",1)
        #logger.info("Adding {} and {}".format(left,right))
        return add_dice(left,right)

    #check to make sure a subtraction isn't taking replace
    elif dice_string.find('-') != -1:
        left, right = dice_string.split("-")
        #logger.info("Subtracting {} and {}".format(left, right))
        return sub_dice(left,right)

    #check to make sure dice_string actually contains a die
    elif dice_string.find('d') != -1:
        return roll_dice(dice_string)

    #dice_string is just a modifier; return it
    else:
        return roll_mod(dice_string)

def add_dice(left_dice, right_dice):
    """Add two dice roll values or modifiers together"""
    left_result = eval_dice(left_dice)
    right_result = eval_dice(right_dice)

    dice_sum = left_result[0] + right_result[0]
    result_string = left_result[1] + " + " + right_result[1]
    return (dice_sum, result_string)

def sub_dice(left_dice, right_dice):
    """Subtract a dice roll value or modifier from another"""
    left_result = eval_dice(left_dice)
    right_result = eval_dice(right_dice)

    dice_diff = left_result[0] - right_result[0]
    result_string = left_result[1] + " - " + right_result[1]
    return (dice_diff, result_string)

def roll_dice(dice_string):
    """Roll a sequence of die and add them up; also reports all roll results"""
    dice_sum = 0
    result_string = ""
    quantity, size = dice_string.split('d',1)
    for i in range(0,int(quantity)):
        roll_result = roll_die(size)
        dice_sum += roll_result
        result_string = str(roll_result)
        #logger.info("Rolled a {}".format(result_string))
        return (dice_sum, result_string)
    return (dice_sum, result_string)

def roll_die(num_sides):
    """Roll a single die of num_sides sides"""
    return randint(1, int(num_sides))

def roll_mod(dice_string):
    """Return a dice roll modifier"""
    return (int(dice_string),dice_string)

async def execute(client, message, command, **kwargs):
    """Roll a number of dice for the user, with modifiers, and return both the roll total and a string of individual roll results
       Supports rolls of the format 'xdy +/- m', where x is the number of rolls, y is the number of sides on the die, and m is a positive integer modifier to your roll
       Rolls and modifiers can be chained in any order. Do not use parentheses or negative numbers."""
    #roll_result = sum_dice(args)
    roll_result = eval_dice(''.join(command[1:]))
    logger.info("{} rolled a total of {} ({})".format(message.author, roll_result[0], roll_result[1]))
    await client.send_message(message.channel, "{}, you rolled a total of {} ({})".format(message.author.display_name, roll_result[0], roll_result[1]))
