#!/usr/bin/python3
import discord
from discord.ext import commands
import KEYS
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
async def group_add(ctx, *, group: str):
    """
    Add a group!
    """
    db_helpers.add_name("groups", group)
    await ctx.message.add_reaction('\N{THUMBS UP SIGN}')



@bot.command()
async def group_join(ctx, *, group: str):
    """
    Join a given group.
    """
    if str(ctx.author) == "bam#5036" and group.upper() == "DOTA":
        await ctx.send(file=discord.File("images/ashley_dota/" + random.choice(os.listdir("images/ashley_dota/"))))
        return
    # TODO ideally we want to check if the group exists first, and ask the user to create it
    if db_helpers.get_group_id(group.upper()) == -1:
        await ctx.send("This group doesn't exist. Create it first!")
        return
    db_helpers.insert_userdata_pair(str(ctx.author), "groups", group)
    await ctx.send("Added {} to your groups, {}!".format(group, str(ctx.author)))


@bot.command()
async def group_list(ctx):
    """
    List your groups, and potentially delete them
    """
    group_list = db_helpers.get_user_data(str(ctx.author), "groups")
    if len(group_list) == 0:
        ctx.send("You have no areas assosciated with your username. Find one to add using \"?area_search\"")
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
            # if we timeout here, let's check if the user has already reacted before we get salty
            await ctx.send("None of your groups have been removed")
        else:
            try:
                index_area_selected = UNICODE_INTS.index(str(reaction_emoji))
                area_selected = group_list[index_area_selected][0]
                db_helpers.remove_userdata_pair(
                    str(ctx.author), "groups", area_selected)
                await ctx.send("Removed {} from your groups, {}!".format(area_selected, str(ctx.author)))
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
        msg = "No groups found! Add one with the \"?group_add\" command."
    await ctx.send(msg)


@bot.command()
async def schedule(ctx, *, group: str):
    """
    Returns when everyone in the group is available to join
    """
    # first, a  little easter egg
    if group.upper() == "UWU":
        await ctx.send(file=discord.File("images/uwu/" + random.choice(os.listdir("images/uwu/"))))
        return

    # check if the user and the group exist
    #
    # db_helpers.add_name("groups", group)
    # ctx.send("Added the group (if it didn't already exist).")
    hours_dict = helpers.schedule_group(group)
    result = helpers.stringify_can_join(hours_dict)
    if result == "[]":
        msg = "No {} today :(".format(group)
    else:
        msg = "You can schedule {} at these times today: \n".format(group)
        msg += result
    await ctx.send(msg)


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"An error occured: {str(error)}")

# @bot.command()
# async def roll(ctx, dice: str):
#     """Rolls a dice in NdN format.
#     TODO use this as a meme for predicting load shedding"""
#     try:
#         rolls, limit = map(int, dice.split('d'))
#     except Exception:
#         await ctx.send('Format has to be in NdN!')
#         return

#     result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
#     await ctx.send(result)


# @bot.command()
# async def joined(ctx, member: discord.Member):
#     """Says when a member joined."""
#     await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')


# @bot.group()
# async def cool(ctx):
#     """Says if a user is cool.

#     In reality this just checks if a subcommand is being invoked.
#     """
#     if ctx.invoked_subcommand is None:
#         await ctx.send(f'No, {ctx.subcommand_passed} is not cool')


# @cool.command(name='bot')
# async def _bot(ctx):
#     """Is the bot cool?"""
#     await ctx.send('Yes, the bot is cool.')


bot.run(KEYS.discord_bot_token)
