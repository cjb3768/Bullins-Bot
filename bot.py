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

        if message.content == "shutdown":
            await client.logout()
            logger.info("Logged out successfully.")

        else:
            # Tokenize the message contents
            command = message.content.split(' ')

            logger.info("Given command '{}' with args '{}'".format(command[0], command[1:]))

            try:
                # Attempt to execute the given command.
                await modules[command[0]].execute(client, message, command, modules=modules)
            except KeyError:
                logger.error("Unrecognized command: %s", command)
                #FIXME: Respond that the command is unrecognized and suggest checking 'help'
            except Exception as e:
                logger.error(e)


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
