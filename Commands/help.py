import discord
import asyncio

async def execute(client, message, args, modules):
    """Send user a private message with a list of all supported functions or the key functionality of a given command"""

    if args == "":
        await client.send_message(message.author, "List of commands")

    else:
        try:
            await client.send_message(message.author, "'{}': {}".format(args, modules[args].execute.__doc__))
        except KeyError:
            print("Unknown module '{}'!".format(args))
