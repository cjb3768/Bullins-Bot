import discord
import asyncio
import logging
import pkgutil
import Commands

logger = logging.getLogger("bullinsbot")
client = discord.Client()
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
    #TODO: Instead of checking if the author is not itself, check to see if they are of a 'bot-controller' roll in Discord
    if message.author != client.user:
        try:
            command, args = message.content.split(' ', 1)
        except ValueError:
            command, args = message.content, ''

        logger.info("Given command '%s' with args '%s'", command, args)

        try:
            await modules[command].execute(client, message, args, modules)
        except KeyError:
            logger.warning("Unrecognized command: %s", command)
            #respond that the command is unrecognized and suggest checking 'help'

def main():
    logging.basicConfig(level=logging.INFO)

    prefix = Commands.__name__ + "."
    for importer, mod_name, ispkg in pkgutil.iter_modules(Commands.__path__, prefix):
        sub_mod_name = "!" + mod_name.split(".", 1)[-1]
        modules[sub_mod_name] = importer.find_module(mod_name).load_module(mod_name)

    logger.info("Found %s command modules.", len(modules))

    #read in token info from bot_token.txt
    token_file = open("bot_token.txt","r")
    bot_login_token = token_file.read()

    client.run(bot_login_token)

if __name__ == "__main__":
    main()
