import os
import discord
import asyncio
import logging
import pkgutil
import configparser
import Commands

###########
# GLOBALS #
###########
logger = logging.getLogger("bullinsbot")
client = discord.Client()
commands = {}

client.invocation = "b! "


def get_highest_priority_role():
    # find the highest priority role in the user permissions and return it
    highest_priority_role = client.permission_config['Default']

    for role in client.permission_config.sections():
        if client.permission_config[role]['role-priority'] > highest_priority_role['role-priority']:
            highest_priority_role = client.permission_config[role]

    return highest_priority_role


def set_bot_permissions(message):
    """check each role a user has to see if they have any that match the configuration file,
       then assign those permissions to the user for later use"""

    # first, clear any old bot permissions
    try:
        # Remove current bot permissions to prevent accidental overlap after a call from an admin
        delattr(client, "current_bot_permissions")
    except AttributeError:
        # We had no prior bot permissions.
        pass

    # next, check to see if user has either general administrator priveleges,
    # or if the user has any of the roles specified in the client config
    for role in message.author.roles:
        # check for generic administrator priveleges in the given role
        if role.permissions.administrator:
            # set permissions to highest priority permission configuration in client config
            logger.debug("Role {} has general administrative privileges. Assigning highest level bot permissions.".format(role.name))
            client.current_bot_permissions = get_highest_priority_role();
            # return; we can't do better than this.
            return

        # check for specified roles
        if role.name in client.permission_config.sections():
            # the user has a role specified in the permissions configuration
            # assuming the user has permissions set already, if the priority of this role is higher than the one the user already has, update their permissions
            try:
                if client.permission_config[role.name]['role-priority'] > client.current_bot_permissions['role-priority']:
                    logger.debug("Role {} has greater permissions than previously allowed. Applying new permissions.".format(role.name))
                    client.current_bot_permissions = client.permission_config[role.name]

            # otherwise, the user has no permissions set, assign them the permissions from this role
            except AttributeError:
                logger.debug("No bot permissions set. Applying permissions for {}.".format(role.name))
                client.current_bot_permissions = client.permission_config[role.name]

    # if at this point, the user still has no permissions set, then assign them the default permission category
    if not hasattr(client, "current_bot_permissions") or client.current_bot_permissions is None:
        logger.debug("No bot permissions set. Applying default permissions.")
        client.current_bot_permissions = client.permission_config['Default']


def check_command_permissions(client, command):
    # check to see if the bot is allowed to run a command
    if '*' in client.current_bot_permissions['bot-functions']:
        # all commands allowed
        logger.info("Current permissions allow all commands.")
        return True
    elif command in client.current_bot_permissions['bot-functions']:
        #command is allowed
        logger.debug("Current permissions allow for command '{}'.".format(command))
        return True
    else:
        logger.debug("Current permissions do no allow for command '{}'.".format(command))
        return False


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

        # Set current bot permissions based on the client call
        set_bot_permissions(message)
        logger.debug("Bot currently operating with the following permissions:")
        for key in client.current_bot_permissions:
            logger.debug("{} : {}".format(key, client.current_bot_permissions[key]))

        # Tokenize the message contents
        instructions = message.content.split(' ')

        logger.info("Given instruction '{}' with args '{}'".format(instructions[0], instructions[1:]))

        #check to see if command is allowed given current permission levels
        if check_command_permissions(client, instructions[0]):
            # permission levels allow for current command
            if instructions[0] == "shutdown":
                await client.logout()
                logger.info("Logged out successfully.")

            else:
                try:
                    # Attempt to execute the given instruction.
                    await commands[instructions[0]](client, message, instructions, commands=commands)

                except KeyError:
                    logger.error("Unrecognized instruction: %s", instructions[0])
                    #FIXME: Respond that the instruction is unrecognized and suggest checking 'help'

                except Exception as e:
                    logger.error(e)
        else:
            # permission levels do not allow for current command
            logger.error("User does not have permission to use requested command.")
            await client.send_message(message.channel, "Either that command is invalid or you do not have permission to use it. Talk to your administrator for more info.")


def main():
    try:
    # Set logging to output all messages INFO level or higher.
        logging.basicConfig(level=logging.INFO)

        # Import all commands from the Commands package and categorize them.
        prefix = Commands.__name__ + "."
        for importer, mod_name, ispkg in pkgutil.iter_modules(Commands.__path__, prefix):
            module = importer.find_module(mod_name).load_module(mod_name)
            commands.update(module.get_available_commands())

        logger.info("Found %s commands.", len(commands))

        # Read in permissions configuration file
        client.permission_config = configparser.ConfigParser()
        client.permission_config.read('permissions.ini')

        logger.info("Permission configurations found for roles: {}".format(client.permission_config.sections()))

        # Start the client and give it our token.
        client.run(os.environ["DISCORD_TOKEN"])

    except Exception as e:
        logger.error("An exception of type {} has occurred".format(type(e).__name__))
        logger.error(e)
        return


if __name__ == "__main__":
    main()
