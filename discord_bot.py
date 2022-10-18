#!/usr/bin/python3
import discord
from discord.ext import commands
import configparser
import asyncio

import loadshedding_helpers
import db_helpers
import helpers
import os, random  # uwu

"""
discord_bot

TODO: Look at command groups rather than the underscores as I have them now
TODO: Need a command to completely remove groups from the db
"""

description = '''A bot to help you schedule games.

For help, type ?help'''

TIMEOUT = 60.0
UNICODE_INTS = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(num) for num in range(0, 10)]


intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?',description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    db_helpers.create_db()


@bot.command()
async def area_search(ctx, *, area: str):
    """
        Search for an area. If it's found, you can add it to your areas.
    """
    # TODO: Could we make this neater?
    areas = loadshedding_helpers.find_area(area.upper().replace(" ", "+"))
    area_list = areas["areas"]
    if len(area_list) != 0:
        message = "I found the following areas! React with yours to add it to your profile.\n"
        for i in range(min(9, len(area_list))):
            area = area_list[i]
            message += UNICODE_INTS[i] + " " + area["name"] + " - " + area["region"] + "\n"
    else:
        message = "I found no areas matching {}, sorry!".format(area)
        await ctx.send(message)
        return

    message_sent = await ctx.send(message)
    # we've sent the message, now add the reactions
    if len(area_list) != 0:
        for i in range(min(9, len(area_list))):
            await message_sent.add_reaction(UNICODE_INTS[i])

    def check(reaction, user):
        if user == ctx.author:
            return str(reaction.emoji)

    try:
        reaction_emoji, user = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
    except asyncio.TimeoutError:
        # if we timeout here, let's check if the user has already reacted before we get salty
        cache_msg = discord.utils.get(bot.cached_messages, id=message_sent.id)
        for reaction in cache_msg.reactions:
            if reaction.count > 1:
                try:
                    index_area_selected = UNICODE_INTS.index(str(reaction_emoji))
                    area_selected = area_list[index_area_selected]
                    db_helpers.insert_userdata_pair(
                        str(ctx.author), "areas", area_selected["id"])
                    await ctx.send("Added {} to your areas, {}!".format(area_selected["name"], str(ctx.author)))
                    return
                except ValueError:
                    # something went horribly wrong
                    return
        await ctx.send("Fine then, ignore me >:(")
    else:
        try:
            index_area_selected = UNICODE_INTS.index(str(reaction_emoji))
            area_selected = area_list[index_area_selected]
            db_helpers.insert_userdata_pair(
                str(ctx.author), "areas", area_selected["id"])
            await ctx.send("Added {} to your areas, {}!".format(area_selected["name"], str(ctx.author)))
        except ValueError:
            # User reacted with a bad emoji
            await ctx.send("Can't follow instructions, eh? You'll have to ask me again.")


@bot.command()
async def area_list(ctx):
    """
    List your areas, and potentially delete them
    """
    area_list = db_helpers.get_user_data(str(ctx.author), "areas")
    if len(area_list) == 0:
        ctx.send("You have no areas assosciated with your username. Find one to add using \"?area_search\"")
        return
    else:
        message = "Here are your areas! Remove one by reacting with it's number.\n"
        for i in range(min(9, len(area_list))):
            message += UNICODE_INTS[i] + " " + area_list[i][0] + "\n"
        message_sent = await ctx.send(message)

        for i in range(min(9, len(area_list))):
            await message_sent.add_reaction(UNICODE_INTS[i])

        def check(reaction, user):
            if user == ctx.author:
                return str(reaction.emoji)

        try:
            reaction_emoji, user = await bot.wait_for('reaction_add', timeout=TIMEOUT/2, check=check)
        except asyncio.TimeoutError:
            # if we timeout here, let's check if the user has already reacted before we get salty
            await ctx.send("None of your areas have been removed")
        else:
            try:
                index_area_selected = UNICODE_INTS.index(str(reaction_emoji))
                area_selected = area_list[index_area_selected][0]
                db_helpers.remove_userdata_pair(
                    str(ctx.author), "areas", area_selected)
                await ctx.send("Removed {} from your areas, {}!".format(area_selected, str(ctx.author)))
            except ValueError:
                # User reacted with a bad emoji
                await ctx.send("Can't follow instructions, eh? You'll have to ask me again.")


@bot.command()
async def group_join(ctx, *, group: str):
    """
    Join a given group. Creates the group if it does not exist.
    """
    if str(ctx.author) == "bam#5036" and group.upper() == "DOTA":
        await ctx.send(file=discord.File("images/ashley_dota/" + random.choice(os.listdir("images/ashley_dota/"))))
        return
    if db_helpers.get_group_id(group.upper()) == -1:
        db_helpers.add_name("groups", group)
    db_helpers.insert_userdata_pair(str(ctx.author), "groups", group)
    await ctx.send("Added {} to your groups, {}!".format(group, str(ctx.author)))


@bot.command()
async def group_list(ctx):
    """
    List your groups, and potentially delete them
    """
    group_list = db_helpers.get_user_data(str(ctx.author), "groups")
    if len(group_list) == 0:
        ctx.send("You have no groups assosciated with your username. Create or join one!")
        return
    else:
        message = "Here are your groups! Remove one by reacting with it's number.\n"
        for i in range(min(9, len(group_list))):
            message += UNICODE_INTS[i] + " " + group_list[i][0] + "\n"
        message_sent = await ctx.send(message)

        for i in range(min(9, len(group_list))):
            await message_sent.add_reaction(UNICODE_INTS[i])

        def check(reaction, user):
            if user == ctx.author:
                return str(reaction.emoji)

        try:
            reaction_emoji, user = await bot.wait_for('reaction_add', timeout=TIMEOUT/2, check=check)
        except asyncio.TimeoutError:
            # await ctx.send("None of your groups have been removed")
            # If nothing happens, then nothing happens. We don't need to tell the user that nothing happens
            pass
        else:
            try:
                index_group_selected = UNICODE_INTS.index(str(reaction_emoji))
                group_selected = group_list[index_group_selected][0]
                group_id = db_helpers.get_group_id(group_selected)
                print(group_selected, group_id)
                db_helpers.remove_userdata_pair(str(ctx.author), "groups", group_selected)
                msg = "Removed {} from your groups, {}!".format(group_selected, str(ctx.author))
                # see if there are any more members in the group. If not, delete the group
                if db_helpers.get_group_members(group_id) == -1:
                    db_helpers.remove_group(group_id)
                    msg += "\nYou were also the last member, so I removed the group, too."
                await ctx.send(msg)
            except ValueError:
                # User reacted with a bad emoji
                await ctx.send("Can't follow instructions, eh? You'll have to ask me again.")


@bot.command()
async def group_list_all(ctx):
    """
    Returns all groups currently available
    """
    msg = ""
    groups = db_helpers.get_groups()
    if len(groups) > 0:
        for i, g in enumerate(groups):
            msg += "{}: {}\n".format(i + 1, g[0])
    else:
        msg = "No groups found! Add one with the \"?group_create\" command."
    await ctx.send(msg)


@bot.command()
async def schedule(ctx, group: str, time=None):
    """
    Returns when everyone in the group is available to join.
    If you provide a time in the format HH:MM, you can ask everyone to join you at that time.
    """
    group = group.replace(" ", "")
    # first, a  little easter egg
    if group.upper() == "UWU":
        await ctx.send(file=discord.File("images/uwu/" + random.choice(os.listdir("images/uwu/"))))
        return

    # check if the user and the group exist
    if db_helpers.get_id("groups", group) == -1:
        await ctx.send("I couldn't find a group by that name!")
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
        # Hey
        # get all users in the group:
        uids = db_helpers.get_group_members(db_helpers.get_group_id(group))
        members = [db_helpers.get_name("users", i) for i in uids]
        msg = "Hey there "

        for member in members:
            name = member[:member.rfind("#")]
            discriminator = member[member.rfind("#")+1:]
            user = discord.utils.get(ctx.guild.members, name = name, discriminator = discriminator)
            if user is not None and user is not ctx.author:
                msg += f"{user.mention}, "
        msg = msg[:-2] + ". {} would like to schedule {} for {} today! RSVP below.".format(ctx.message.author.mention, group, time)

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
    Returns an image with a breakdown of each member's available times
    """
    # first, let's check if the group exists
    if db_helpers.get_group_id(group) != -1:
        # get the graph
        image = helpers.generate_graph(group)
        await ctx.send(file=discord.File(image))
    else:
        await ctx.send("Group does not exist.")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"An error occured: {str(error)}")


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")
    bot.run(config["Tokens"]["discord_bot"])
