# LoadSchedder

LoadSchedder is a Discord bot written in Python designed to collate loadshedding schedules of multiple users. It makes use of Discord.py and the [sepush API](https://documenter.getpostman.com/view/1296288/UzQuNk3E).

I'm not currently hosting this for the public, and I don't currently have intentions to. You're welcome to self-host it (basic instructions below) but note that support may be limited. To get a sepush API token, you can visit [this site](https://eskomsepush.gumroad.com/l/api).

If you do end up using this, or have ideas on how to improve it, please let me know.

## Bot commands and How-to
The following thread is out of date, but shows the concept: [Twiter thread](https://twitter.com/CrankyPandaMan/status/1579506558869741569).

The premise is fairly simple:
- Each user has one or more areas which dictates their loadschedding schedule.
- Each user can join multiple groups.
- There are commands to schedule a group activity, which considers when users within that group are loadshedding.
- Users not located in the default timezone can set a pytz timezone, and the bot will interpret their schedule as being in their own timezone and adjust accordingly.

All commands can be found and explained by running "?help"

## How to self-host
First, you need to ensure the python packages found in requirements.txt are installed.
You also need to ensure you have the FreeSerif font installed (so that that the graph can display unicode character "\U00002713").

Once that's all done, modify config.ini to contain:
- your Discord bot token
- your sepush API token
- the default timezone if not located in South Africa

The Discord bot needs the following intents:
- reactions
- members
- messages intents
- guild_scheduled_events

Personally I'm hosting this bot using systemd, and as a consequence of that I have also version controlled a loadsheddingbot.service file. This will likely work for you, though you will need to change the "WorkingDirectory" and "ExecStart" variables accordingly.

## Acknowledgements
Thanks to [BrydonLeonard](https://github.com/BrydonLeonard) for doing the inital work on scheduling Discord-native events.