import discord
import asyncio
import logging
from Commands import echo, help, play, roll

logging.basicConfig(level=logging.INFO)

#this next function could be used later to spread the bot; can be moved later
def generate_oauth_url(client_id, permissions):
    """Generate the bot's OAuth2 URL to add it to a server from a given client_id and set of permissions"""
    return "https://discordapp.com/api/oauth2/authorize?client_id={}&permissions={}&scope=bot".format(client_id, permissions)

#read in token info from bot_token.txt
token_file = open("bot_token.txt","r")
bot_login_token = token_file.read()

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-------')

@client.event
async def on_message(message):
    if message.author != client.user:
        #print("INCOMING MESSAGE!")

        try:
            command, args = message.content.split(' ', 1)
        except ValueError:
            #print("Value Error Caught")
            command, args = message.content, ''

        print("Executing command '{}' with args '{}'".format(command, args))

        if command == '!test':
            counter = 0
            tmp = await client.send_message(message.channel, 'Calculate messages...')
            async for log in client.logs_from(message.channel, limit=100):
                if log.author == message.author:
                    counter += 1

            await client.edit_message(tmp, 'You have {} messages.'.format(counter))
        elif command == '!sleep':
            await asyncio.sleep(5)
            await client.send_message(message.channel, 'Done sleeping')

        #support echo function
        elif command == '!echo':
            await echo.execute(client, message, args)

        elif command == '!help':
            await help.execute(client, message, args)

        elif command == "!play":
            await play.execute(client, message, args)

        elif command == "!roll":
            await roll.execute(client, message, args)
        #print("Finished!")

client.run(bot_login_token)
