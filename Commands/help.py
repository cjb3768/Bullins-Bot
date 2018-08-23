import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.help")

async def execute(client, message, command, **kwargs):
    """Enumerate commands, or explain the functionality of specific command."""

    modules = kwargs['modules']

    if len(command) > 2:
        logger.warning("Unknown command '%s'!", command[1:])

        await client.send_message(message.author, "Warning: Too many arguments.\n*help*: {}".format(modules['help'].execute.__doc__))

    elif len(command) == 2:
        logger.debug("User looking for specific info about command %s.", command[1])

        try:
            await client.send_message(message.author, "*{}*: {}".format(command[1], modules[command[1]].execute.__doc__))
        except KeyError:
            logger.warning("Unknown command '%s'!", command[1])
            #FIXME: Notify the user of the error.

    else:
        logger.debug("User looking for general help.")

        # Build a sting of a list of modules.
        module_list = '*\n*'.join(modules)

        # Build a string to display.
        helptext = "I support the following commands:\n*{}*\nTry `{}help [command]` for more information.".format(module_list, client.invocation)

        # Send a direct message to the user with requested information.
        await client.send_message(message.author, helptext)
