import discord
import asyncio
import logging
import pkgutil
import Commands

###########
# GLOBALS #
###########
logger = logging.getLogger("bullinsbot")
client = discord.Client()
commands = {}

client.invocation = "b! "


@client.event
async def on_ready():
    logger.info("Logged in as '%s', ID: %s", client.user.name, client.user.id)

    #TODO: I Think an introduction might go here.


@client.event
async def on_message(message):
    # Check if incoming message is intended for this bot.
    if message.content.startswith(client.invocation):
        # Consume the invocation.
        message.content = message.content[len(client.invocation):]

        if message.content == "shutdown":
            await client.logout()
            logger.info("Logged out successfully.")

        else:
            # Tokenize the message contents
            instructions = message.content.split(' ')

            logger.info("Given instruction '{}' with args '{}'".format(instructions[0], instructions[1:]))

            try:
                # Attempt to execute the given instruction.
                await commands[instructions[0]](client, message, instructions, commands=commands)

            except KeyError:
                logger.error("Unrecognized instruction: %s", instructions[0])
                #FIXME: Respond that the instruction is unrecognized and suggest checking 'help'

            except Exception as e:
                logger.error(e)


def main():
    # Set logging to output all messages INFO level or higher.
    logging.basicConfig(level=logging.INFO)

    # Import all commands from the Commands package and categorize them.
    prefix = Commands.__name__ + "."
    for importer, mod_name, ispkg in pkgutil.iter_modules(Commands.__path__, prefix):
        module = importer.find_module(mod_name).load_module(mod_name)
        commands.update(module.get_available_commands())

    logger.info("Found %s commands.", len(commands))

    # Read in token info from bot_token.txt
    token_file = open("bot_token.txt","r")
    bot_login_token = token_file.read()

    # Start the client and give it our token.
    client.run(bot_login_token)


if __name__ == "__main__":
    main()
