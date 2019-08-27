import discord
import asyncio
import logging

###########
# GLOBALS #
###########
logger = logging.getLogger("bullinsbot.help")


def get_available_commands():
    return {"help": execute}


def filter_commands_by_permissions(client, command_list):
    filtered_commands = dict()
    # check to see if the bot is allowed to run a command
    if '*' in client.current_bot_permissions['bot-functions']:
        # all commands allowed
        logger.debug("All commands permitted. Returning full command list.")
        filtered_commands = command_list

    else:
        for command in command_list.keys():
            if command in client.current_bot_permissions['bot-functions']:
                #command is allowed
                logger.debug("Current permissions allow for command '{}'.".format(command))
                filtered_commands[command] = command_list[command]

    return filtered_commands


async def execute(client, message, instruction, **kwargs):
    """Enumerate commands, or explain the functionality of specific command."""

    #commands = kwargs['commands']
    commands = filter_commands_by_permissions(client, kwargs['commands'])
    logger.info(commands.keys())

    if len(instruction) > 2:
        logger.warning("Unknown command '%s'!", instruction[1:])

        await message.channel.send("Warning: Too many arguments. Try again with the format `{} help [command].`".format(client.invocation))

    elif len(instruction) == 2:
        logger.debug("User looking for specific info about command %s.", instruction[1])

        try:
            await message.channel.send("*{}*: {}".format(instruction[1], commands[instruction[1]].__doc__))
        except KeyError:
            logger.warning("Unknown or restricted command '%s'!", instruction[1])
            #FIXME: Notify the user of the error.
            await message.channel.send("Error: The command you entered is either invalid or its access is restricted to you.\nContact your channel's Bullins-Bot administrator for more information.")

    else:
        logger.debug("User looking for general help.")

        # Build a string of a list of commands.
        command_list = '*\n*'.join(commands)

        # Build a string to display.
        helptext = "Your current permissions give you access to the following commands:\n*{}*\nTry `{}help [command]` for more information on a given command.".format(command_list, client.invocation)

        # Send a direct message to the user with requested information. CURRENTLY DUMPS TO TEXT CHANNEL.
        await message.channel.send(helptext)
