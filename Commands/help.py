import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.help")

async def execute(client, message, args, modules):
    """Enumerate commands, or explain the functionality of specific command."""

    if args:
        logger.debug("User looking for spicific info about command %s.", args)

        try:
            await client.send_message(message.author, "*{}*: {}".format(args, modules[args].execute.__doc__))
        except KeyError:
            logger.warning("Unknown command '%s'!", args)
            #FIXME: Notify the user of the error.

    else:
        logger.debug("User looking for general help.")

        # Build a sting of a list of modules.
        module_list = '*\n*'.join(modules)

        # Build a string to display.
        helptext = "I support the following commands:\n*{}*\nTry `{}help [command]` for more information.".format(module_list, client.invocation)

        # Send a direct message to the user with requested information.
        await client.send_message(message.author, helptext)
