![logo](logo.png)

# Raceroom Commander
Created by Koen van Hove - koenvh.nl

Raceroom Commander is a small program that runs alongside your dedicated server, and adds support for 
chat commands in Raceroom. It can also set custom rules regarding minimum rating/reputation with 
whitelist, and drive-through penalty rules for incidents.

## Commands:
- /kick NAME - Kicks a player from the server
- /ban NAME - Bans a player from the server
- /penalty NAME TYPE - Penalise a player, either slowdown, drivethrough, stopandgo, or disqualify
- /slowdown NAME DURATION - Give a slowdown penalty to a player for DURATION seconds
- /drivethrough NAME - Give a drive-through penalty to a player
- /stopandgo NAME DURATION - Give a stop-and-go penalty to a player for DURATION seconds
- /disqualify NAME - Black flag a player
- /next - Continue to the next session
- /restart - Restart the current session
- /help - Show the available commands

## How it works:
Edit the `rrcommander.json` file. Add your own ID to the `admin_ids` list. 
You can find your ID in the dedicated server web page, under current users next to your name.
The users in this list have access to the commands above. 
If they are in the game, and they type one of the commands, then Raceroom Commander will pick that up.

If you set a `minimum_rating` and/or `minimum_reputation`, then the server will kick players that 
attempt to join the server with an insufficient rating/reputation. Set this to -1 to disable.
The IDs in the `whitelist_ids` list will never be kicked due to insufficient rating/reputation.

If you set the `incident_intervals`, then once a player reaches one of the specified amounts of incident points, 
they will get a drive-through penalty. You can specify in `incident_types` which types of incidents should be 
counted towards this point total. The possible types are:
- Type 0 = Car to car collision
- Type 1 = Collision with a track object
- Type 2 = Going the wrong way
- Type 3 = Going off track
- Type 4 = Staying stationary on the track
- Type 5 = Losing control of the vehicle
- Type 6 = Not serving a penalty
- Type 7 = Disconnecting / Giving up before the end of a race
- Type 8 = Missing the race start

So if you do not care about people going off track, then you can remove 3 from the `incident_types`. 

## How to download:
Go to https://gitlab.com/Koenvh/raceroom-commander/-/releases, download the latest `rrcommander.zip`,
extract the files to a folder of your choosing, set the settings in `rrcommander.json` to match whatever 
you want to do with Raceroom Commander, start the Raceroom Dedicated Server and run `rrcommander.exe`. 
Please note that the Raceroom Dedicated Server must be running when starting `rrcommander.exe`, and settings
will only be applied after restarting `rrcommander.exe`.

**Consider donating if you find Raceroom Commander useful:**  
[![Donate](https://www.paypalobjects.com/en_US/GB/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XN358TP8M3J26&source=url)