import discord
import asyncio
import logging

###########
# GLOBALS #
###########
logger = logging.getLogger("bullinsbot.help")


def get_available_commands():
    return {"help": execute}


async def execute(client, message, instruction, **kwargs):
    """Enumerate commands, or explain the functionality of specific command."""

    commands = kwargs['commands']

    if len(instruction) > 2:
        logger.warning("Unknown command '%s'!", instruction[1:])

        await client.send_message(message.author, "Warning: Too many arguments.\n*help*: {}".format(commands['help'].__doc__))

    elif len(instruction) == 2:
        logger.debug("User looking for specific info about command %s.", instruction[1])

        try:
            await client.send_message(message.author, "*{}*: {}".format(instruction[1], commands[instruction[1]].__doc__))
        except KeyError:
            logger.warning("Unknown command '%s'!", instruction[1])
            #FIXME: Notify the user of the error.

    else:
        logger.debug("User looking for general help.")

        # Build a string of a list of commands.
        command_list = '*\n*'.join(commands)

        # Build a string to display.
        helptext = "I support the following commands:\n*{}*\nTry `{}help [command]` for more information.".format(command_list, client.invocation)

        # Send a direct message to the user with requested information.
        await client.send_message(message.author, helptext)
