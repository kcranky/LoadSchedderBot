#!/usr/bin/python3
import discord
from discord.ext import commands
import configparser
import asyncio

import loadshedding_helpers
import db_helpers
import helpers

"""
discord_bot

TODO: Look at command groups rather than the underscores as I have them now
TODO: Need a command to completely remove groups from the db
"""

config = configparser.ConfigParser()
config.read("config.ini")

description = '''A bot to help you schedule games.

For help, type ?help'''

intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True
intents.members = True
intents.guild_scheduled_events = True

help_command = commands.DefaultHelpCommand(no_category = 'Commands', show_parameter_descriptions=False)
bot = commands.Bot(command_prefix='?',description=description, intents=intents, help_command = help_command)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    for cog_file in helpers.COGS_DIR.glob("*.py"):
            if cog_file != "__init.py__":
                await bot.load_extension(f"cogs.{cog_file.name[:-3]}")
    db_helpers.create_db()

@bot.command()
async def schedule(ctx, group: str, time=None):
    """
    Returns when everyone in the group is available to join.
    If you provide a time in the format HH:MM, you can ask everyone to join you at that time.
    You can schedule group "all" to see when everyone is available.
    """
    group = group.replace(" ", "")
    # check if the user and the group exist
    if db_helpers.get_id("groups", group) == -1:
        msg = "I couldn't find a group with that name!\n"
        msg += "Groups need to be a single word/string. If your group has multiple words, recreate it as a single word group."
        await ctx.send(msg)
        return

    # If there's just one parameter
    if time is None or helpers.is_time_format(time) == False:
        hours_dict = helpers.schedule_group(group)
        result = helpers.stringify_can_join(hours_dict)
        if result == "[]":
            msg = "No {} today :(".format(group)
        else:
            msg = "You can schedule {} at these times today: \n".format(group)
            msg += result

    if helpers.is_time_format(time):
        uids = db_helpers.get_group_members(db_helpers.get_group_id(group))
        members = [db_helpers.get_name("users", i) for i in uids]
        if len(members) == 0:
            msg_intro = "Hey there!"
        else:
            if str(ctx.author.id) in members:
                    members.remove(str(ctx.author.id))
            member_list = ", ".join(f"<@{member}>" for member in members)
            msg_intro = f"Hey there {member_list}!"

        guild = bot.get_guild(int(config["Server"]["server_id"]))

        # Would be nice to stash this, but the call volume should be low enough for now
        channel = await bot.fetch_channel(int(config["Server"]["scheduling_vc_id"]))

        event: discord.ScheduledEvent = await guild.create_scheduled_event(
            name=f"{group}",
            channel=channel,
            start_time=helpers.to_tz_aware_datetime(time),
            privacy_level=discord.PrivacyLevel.guild_only,
            entity_type=discord.EntityType.voice
        )

        try:
            invite: discord.Invite = await channel.create_invite(temporary=True)
            invite_link = f"{invite}?event={event.id}"
        except:
            invite_link = ("The bot failed to create an invite link. You'll need to open the event manually to mark "
                           "yourself interested")

        msg = f"{msg_intro} {ctx.message.author.mention} would like to schedule {group} for {time} today!\n{invite_link}"

        await ctx.send(msg)

        return
    elif time != None:
        msg = "I couldn't understand your time format, but y" + msg[1:]

    await ctx.send(msg)

@bot.command()
async def timetable(ctx, *, group: str ="ALL"):
    """
    Returns an image with a breakdown of each member's available times.
    You can use group "all" to see everyone's availability.
    """
    # Because we store userIDs in the DB, we also need now to pass through a translation for users, from UID -> nick
    uid2nick = {}

    async with ctx.typing():
        if group.upper() == "ALL" or None:
            uids = db_helpers.get_all_members()
            for id in uids:
                user = await bot.fetch_user(db_helpers.get_name("users", id))
                uid2nick[user.id] = user.name
            image = helpers.generate_graph("ALL", uid2nick)
        elif db_helpers.get_group_id(group) != -1:
            uids = db_helpers.get_group_members(db_helpers.get_group_id(group.upper()))
            for id in uids:
                user = await bot.fetch_user(db_helpers.get_name("users", id))
                uid2nick[user.id] = user.name
            # get the graph
            image = helpers.generate_graph(group.upper(), uid2nick)
        else:
            await ctx.send("Group does not exist.")
            return

        await ctx.send(file=discord.File(image))

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"An error occured: {error}")

if __name__ == "__main__":
    bot.run(config["Tokens"]["discord_bot"], root_logger=True)
