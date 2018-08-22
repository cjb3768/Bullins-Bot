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
modules = {}

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

        # Seperate the command from any additional arguments.
        try:
            command, args = message.content.split(' ', 1)
        except ValueError:
            command, args = message.content, ''

        logger.info("Given command '%s' with args '%s'", command, args)

        try:
            # Attempt to execute the given command.
            await modules[command].execute(client, message, args, modules)
        except KeyError:
            logger.error("Unrecognized command: %s", command)
            #FIXME: Respond that the command is unrecognized and suggest checking 'help'


def main():
    # Set logging to output all messages INFO level or higher.
    logging.basicConfig(level=logging.INFO)

    # Import all modules from the Commands package and categorize them.
    prefix = Commands.__name__ + "."
    for importer, mod_name, ispkg in pkgutil.iter_modules(Commands.__path__, prefix):
        sub_mod_name = mod_name.split(".", 1)[-1]
        modules[sub_mod_name] = importer.find_module(mod_name).load_module(mod_name)

    logger.info("Found %s command modules.", len(modules))

    # Read in token info from bot_token.txt
    token_file = open("bot_token.txt","r")
    bot_login_token = token_file.read()

    # Start the client and give it our token.
    client.run(bot_login_token)


if __name__ == "__main__":
    main()
