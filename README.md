![logo](logo.png)

# Raceroom Commander
Created by Koen van Hove - koenvh.nl

Raceroom Commander is a small script that adds support for chat commands in Raceroom.
It can also set custom rules regarding minimum rating/reputation with whitelist.

## Commands:
- /kick NAME - Kicks a player from the server
- /ban NAME - Bans a player from the server
- /penalty NAME TYPE - Penalise a player, either slowdown, drivethrough, stopandgo, or disqualify
- /slowdown NAME DURATION - Give a slowdown penalty to a player for DURATION seconds
- /drivethrough NAME - Give a drive-through penalty to a player
- /stopandgo NAME - Give a stop-and-go penalty to a player
- /disqualify NAME - Black flag a player
- /next - Continue to the next session
- /restart - Restart the current session
- /help - Show the available commands

## How it works:
Edit the `server.json` file. Add your own ID to the `admin_ids` list. 
You can find your ID in the dedicated server web page, under current users next to your name.
The users in this list have access to the commands above. 
If they are in the game, and they type one of the commands, then Raceroom Commander will pick that up.
If you set a `minimum_rating` and/or `minimum_reputation`, then the server will kick players that 
attempt to join the server with an insufficient rating/reputation. Set this to -1 to disable.
The IDs in the `whitelist_ids` list will never be kicked due to insufficient rating/reputation.

## How to download:
Go to https://gitlab.com/Koenvh/raceroom-commander/-/releases, download the latest `server.zip`,
extract the files to a folder of your choosing, set the settings in `server.json` to match whatever 
you want to do with Raceroom Commander, start the Raceroom Dedicated Server and run `server.exe`. 
Please note that the Raceroom Dedicated Server must be running when starting `server.exe`, and settings
will only be applied after restarting `server.exe`.

**Consider donating if you find Raceroom Commander useful:**  
[![Donate](https://www.paypalobjects.com/en_US/GB/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XN358TP8M3J26&source=url)