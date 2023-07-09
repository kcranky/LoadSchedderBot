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

description = '''A bot to help you schedule games.

For help, type ?help'''

intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True
intents.members = True

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
    if time is None or helpers.isTimeFormat(time) == False:
        hours_dict = helpers.schedule_group(group)
        result = helpers.stringify_can_join(hours_dict)
        if result == "[]":
            msg = "No {} today :(".format(group)
        else:
            msg = "You can schedule {} at these times today: \n".format(group)
            msg += result

    if helpers.isTimeFormat(time):
        uids = db_helpers.get_group_members(db_helpers.get_group_id(group))
        members = [db_helpers.get_name("users", i) for i in uids]
        if len(members) == 0:
            member_list = ", ".join(f"<@{member}>" for member in members)
            msg = "Hey there {}!".format(member_list)
        else:
            if str(ctx.author.id) in members:
                    members.remove(str(ctx.author.id))
            msg = "Hey there!"
        msg = msg + "{} would like to schedule {} for {} today! RSVP below.".format(ctx.message.author.mention, group, time)

        message_sent = await ctx.send(msg)
        await message_sent.add_reaction('\N{THUMBS UP SIGN}')
        await message_sent.add_reaction('\N{THUMBS DOWN SIGN}')
        return
    elif time != None:
        msg = "I couldn't understand your time format, but y" + msg[1:]

    await ctx.send(msg)

@bot.command()
async def timetable(ctx, *, group: str):
    """
    Returns an image with a breakdown of each member's available times.
    You can use group "all" to see everyone's availability.
    """
    # Because we store userIDs in the DB, we also need now to pass through a translation for users, from UID -> nick
    uid2nick = {}

    async with ctx.typing():
        uids = db_helpers.get_group_members(db_helpers.get_group_id(group))
        for id in uids:
            user = await bot.fetch_user(db_helpers.get_name("users", id))
            uid2nick[user.id] = user.name

        if group.upper() == "ALL":
            image = helpers.generate_graph("ALL", uid2nick)
        elif db_helpers.get_group_id(group) != -1:
            # get the graph
            image = helpers.generate_graph(group, uid2nick)
        else:
            await ctx.send("Group does not exist.")
            return

        await ctx.send(file=discord.File(image))

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"An error occured: {str(error)}")


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")
    bot.run(config["Tokens"]["discord_bot"])
