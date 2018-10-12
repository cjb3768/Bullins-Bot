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
* `play 'url'` - Plays audio from a given url source in the voice chat you are currently in. Supports queueing of audio sources from a number of different websites (full list [here](https://rg3.github.io/youtube-dl/supportedsites.html)).
* `pause` - Pauses stream player if one is active.
* `resume` - Resume stream player if one is active.
* `stop` - Stop streaming audio if a stream player is active.
* `volume [' ', '+/- x', 'x']` - Report stream player volume, adjust the current volume level by x %, or set the current volume level to x %. Volume levels are capped at 0% and 100%.
* `queue` - Report a list of all the songs in the current stream playback queue, with their names, the name of the source uploader, and the name of the user who requested the song to the bot.
* `repeat [' ', 'all/current/off']` - Report the current repeat mode for the current stream playback queue, or set it to repeat either all songs in the queue, the current song, or no songs.
* `skip` - Skips the current song in the stream playback queue.
* `clean ['number']` - Scans 'number' messages from the current channel and deletes any bot requests and bot replies.
