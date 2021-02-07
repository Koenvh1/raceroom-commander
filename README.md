![logo](logo.png)

# Raceroom Commander
Created by Koen van Hove - koenvh.nl

Raceroom Commander is a small program that runs alongside your dedicated server, and adds support for 
chat commands in Raceroom. It can also set custom rules regarding minimum rating/reputation with 
whitelist, and penalty rules for incidents.

## Commands:
- /kick NAME - Kicks a player from the server
- /ban NAME - Bans a player from the server
- /penalty NAME TYPE - Penalise a player, either slowdown, drivethrough, stopandgo, or disqualify
- /slowdown (or /sd) NAME DURATION - Give a slowdown penalty to a player for DURATION seconds
- /drivethrough (or /dt) NAME - Give a drive-through penalty to a player
- /stopandgo (or /sg) NAME DURATION - Give a stop-and-go penalty to a player for DURATION seconds
- /disqualify (or /dq) NAME - Black flag a player
- /next - Continue to the next session
- /restart - Restart the current session

## How it works:
The easiest way to see how everything works is to look at the example configuration in the `rrcommander.json5` file.

Edit the `rrcommander.json5` file. Add your own ID to the `admin_ids` list. 
You can find your ID in the dedicated server web page, under current users next to your name.
The users in this list have access to the commands above. 
If they are in the game, and they type one of the commands, then Raceroom Commander will pick that up.

If you set a `minimum_rating` and/or `minimum_reputation`, then the server will kick players that 
attempt to join the server with an insufficient rating/reputation. Set this to -1 to disable.
The IDs in the `whitelist_ids` list will never be kicked due to insufficient rating/reputation.

In `incidents`, you can set some incident rules. Once a player reaches one of the specified amounts of incident points, 
they will get a penalty. The type of penalty is specified in `penalty` 
(namely `slowdown`, `drivethrough`, or `stopandgo`) and `duration` (in case of stop-and-go or slowdown). 
You can specify in `types` which types of incidents should be counted towards this point total, and how much. 
The possible types are:

| Type | Description                                        |
|------|----------------------------------------------------|
| 0    | Car to car collision                               |
| 1    | Collision with a track object                      |
| 2    | Going the wrong way                                |
| 3    | Going off track                                    |
| 4    | Staying stationary on the track                    |
| 5    | Losing control of the vehicle                      |
| 6    | Invalid Lap                                        |
| 7    | Not serving a penalty                              |
| 8    | Disconnecting / Giving up before the end of a race |

In intervals you can set at how many incident points this penalty should be applied. 

You can also exclude certain sessions from certain rules. 
For example, if you have one race that last 20 minutes, and another race that lasts 40 minutes,
you might want to differentiate the rules. The sessions are as follows:

| Code | Name            |
|------|-----------------|
| 0    | Practice        |
| 256  | Qualify         |
| 513  | Warmup (Race)   |
| 514  | Warmup (Race 2) |
| 515  | Warmup (Race 3) |
| 768  | Race            |
| 769  | Race 1          |
| 770  | Race 2          |
| 771  | Race 3          |

For example, the following rule applies a four second slowdown penalty to players getting five, eight or fifteen 
incident points. The types have been omitted for clarity:
```json
{
  "penalty": "slowdown", 
  "duration": 4, 
  "intervals": [5, 8, 15], 
  "types": { ... },
  "exclude_sessions": [770]
}
```
You can have multiple rules, and they can overlap. For example, if a stop-and-go and drive-through rule both contain 10 
as interval, then a player will get both a drive-through and stop-and-go penalty.

Currently, banning players in the dedicated server does not prevent them from joining until you restart the server. 
If you use `/ban`, then they will be added to the ban list, and they will be unable to join as long as RRC is running.

You do not need to use all functionality, and you can disable functionality you do not use.

## How to download:
Go to https://gitlab.com/Koenvh/raceroom-commander/-/releases, download the latest `rrcommander.zip`,
extract the files to a folder of your choosing, set the settings in `rrcommander.json5` to match whatever 
you want to do with Raceroom Commander, start the Raceroom Dedicated Server and run `rrcommander.exe`. 
The servers are in the same order as they are in the dedicated server control panel, 
ergo server 1 is the top server, server 2 the one below that etc.
You will need to have a config for each server.
Please note that the Raceroom Dedicated Server must be running when starting `rrcommander.exe`, and setting changes
will only be applied after restarting `rrcommander.exe`.

## Building the exe yourself:
The executable is created using pyinstaller, specifically using:
```
pyinstaller --icon logo.ico --onefile rrcommander.py
```

**Consider donating if you find Raceroom Commander useful:**  
[![Donate](https://www.paypalobjects.com/en_US/GB/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=XN358TP8M3J26&source=url)