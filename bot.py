import discord
import asyncio
import logging
import pkgutil
import Commands

logger = logging.getLogger("bullinsbot")
client = discord.Client()
invocation = "b! "
modules = {}

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-------')

    #TODO: I Think the Introduction mught go here

@client.event
async def on_message(message):
    if message.content.startswith(invocation):
        try:
            _, command, args = message.content.split(' ', 2)
        except ValueError:
            _, command, args = message.content.split(' ', 1), ''

        logger.info("Given command '%s' with args '%s'", command, args)

        try:
            await modules[command].execute(client, message, args, modules)
        except KeyError:
            logger.error("Unrecognized command: %s", command)
            #respond that the command is unrecognized and suggest checking 'help'

def main():
    logging.basicConfig(level=logging.INFO)

    prefix = Commands.__name__ + "."
    for importer, mod_name, ispkg in pkgutil.iter_modules(Commands.__path__, prefix):
        sub_mod_name = mod_name.split(".", 1)[-1]
        modules[sub_mod_name] = importer.find_module(mod_name).load_module(mod_name)

    logger.info("Found %s command modules.", len(modules))

    #read in token info from bot_token.txt
    token_file = open("bot_token.txt","r")
    bot_login_token = token_file.read()

    client.run(bot_login_token)

if __name__ == "__main__":
    main()
