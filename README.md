# Bullins-Bot
A simple Discord bot for streaming music as audio over voice channels, and other various tasks. Uses Python 3.6.3, the [discord.py](https://github.com/Rapptz/discord.py) library, and the [youtube-dl](https://github.com/rg3/youtube-dl/) library.

### Command Format

Commands are prefaced by the invocation `b!`, for example:

* `b! help`
* `b! echo Hello, World!`

### Command List

* `help ['command']` - Request available commands, or info on specific command if given.
* `echo 'phrase'` - Repeats 'phrase' in current chat.
* `roll 'dice'` - Randomly rolls dice with support for chained rolls of n-sided dice and modifiers.
* `play 'url'` - Plays audio from a given url source in the voice chat you are currently in. Supports queueing of audio sources from a number of different websites, including YouTube, Soundcloud, Twitch.tv, and others. See help text for command for full list.
* `pause` - Pauses stream player if one is active.
* `resume` - Resume stream player if one is active.
* `stop` - Stop streaming audio if a stream player is active.
* `volume [' ', '+/- x', 'x']` - Report stream player volume, adjust the current volume level by x %, or set the current volume level to x %. Volume levels are capped at 0% and 100%.
* `queue` - Report a list of all the songs in the current stream playback queue, with their names, the name of the source uploader, and the name of the user who requested the song to the bot.
* `repeat [' ', 'all/current/off']` - Report the current repeat mode for the current stream playback queue, or set it to repeat either all songs in the queue, the current song, or no songs.
* `skip` - Skips the current song in the stream playback queue.
* `clean ['number']` - Scans 'number' messages from the current channel and deletes any bot requests and bot replies.


### Installation

Note: this section is still under revision.

Before running this application, you will need a Discord bot authorization token to authenticate and login with the bot. You can get that token by creating an application at [the Discord applications developer portal.](https://discordapp.com/developers/applications/) Once you have that token, you will need to add it as an environment variable on your OS with the name "DISCORD_TOKEN".

You will also need to get the discord.py module with voice features enabled, the youtube-dl library, and either ffmpeg or avconv. Installation instructions for discord.py and youtube-dl may be found at their respective github repositories, linked at the top of this readme; ffmpeg can be found [here.](https://www.ffmpeg.org)


