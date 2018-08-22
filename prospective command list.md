# Wishlist

0. bot.py
    * `quit`
        * shuts down bullinsbot
1. Help module
    * `help`
    * `help "command"`
2. Echo module
    * `echo "message"`
3. Roll module
    * `roll "die"`
4. Play module
    * `play "link"`
        * Loads a link and plays stream if not currently running, adds to queue if running
    * `play "search term"`
        * Searches for stream with "search term"
        * Offers top n results (say, n=4)
        * Listens for user response
        * Loads stream and plays if not running, adds to queue if running
    * `pause`
        * pause current playback
    * `resume`
        * resume current playback
    * `stop`
        * stop current playback and empty queue
    * `next`
        * could also be `skip`
    * `repeat`
        * reports repeat status
    * `repeat on`
    * `repeat off`
    * `queue`
        * report contents of queue
    * `add "link"`
        * checks to see if link valid when adding to queue
    * `volume "x"`
        * sets video volume to x
5. Clean module
    * `clean`
        * cleans text channel of bot messages and commands
