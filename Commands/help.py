import discord
import asyncio
import logging

logger = logging.getLogger("bullinsbot.help")

async def execute(client, message, args, modules):
    """Send user a private message with a list of all supported functions or the key functionality of a given command"""

    if args:
        logger.debug("looking for spicific info about command %s.", args)

        try:
            await client.send_message(message.author, "'{}': {}".format(args, modules[args].execute.__doc__))
        except KeyError:
            logger.warning("Unknown command '%s'!", args)

    else:
        logger.debug("looking for general help.")

        module_list = "\n"
        for command in modules:
            module_list += command + "\n"

        helptext = "Supports the following commands:{}Type `!help [command]` for more information.".format(module_list)

        await client.send_message(message.author, helptext)
