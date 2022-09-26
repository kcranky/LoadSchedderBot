#!/usr/bin/python3

from operator import indexOf
import discord
from discord.ext import commands
import random
import KEYS
import asyncio

import loadshedding_helpers
import db_helpers
import helpers

description = '''A bot to help you schedule games.

For help, type ?help'''

TIMEOUT = 10.0
UNICODE_INTS = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(num) for num in range(0, 10)]


intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='?',
                   description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # TODO: Create DB here if it doesn't exist


@bot.command()
async def area_search(ctx, *, area: str):
    """
        Search for an area. If it's found, you can add it to your areas.
    """
    areas = loadshedding_helpers.find_area(area.upper().replace(" ", "+"))
    area_list = areas["areas"]
    if len(area_list) != 0:
        message = "I found the following areas! React with yours to add it to your profile.\n"
        for i in range(min(9, len(area_list))):
            message += UNICODE_INTS[i] + area_list[i]["name"] + " - " + area_list[i]["region"] + "\n"
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
        # FIXME : Check if the emoji is one of the desired ones?
        try:
            index_area_selected = UNICODE_INTS.index(str(reaction_emoji))
            area_selected = area_list[index_area_selected]
            db_helpers.insert_userdata_pair(
                str(ctx.author), "areas", area_selected["id"])
            await ctx.send("Added {} to your areas, {}!".format(area_selected["name"], str(ctx.author)))
        except ValueError:
            # User reacted with a bad emoji
            await ctx.send("Can't follow instructions, eh? I'll let you try again.")


@bot.command()
async def group_list(ctx):
    """
    Returns the groups you're a part of
    """
    msg = ""
    groups = db_helpers.get_user_data(str(ctx.author), "groups")
    if len(groups) > 0:
        for i, g in enumerate(groups):
            msg += "{}: {}\n".format(i + 1, g[0])
    else:
        msg = "You're not a part of any groups!"
    await ctx.send(msg)


@bot.command()
async def group_remove(ctx, *, group: str):
    """
    Remove a group
    """
    msg = ""
    groups = db_helpers.remove_user_data(str(ctx.author), "groups", group)
    await ctx.message.add_reaction('\N{THUMBS UP SIGN}')


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
    # check if the user and the group exist
    #
    # db_helpers.add_name("groups", group)
    # ctx.send("Added the group (if it didn't already exist).")
    db_helpers.insert_userdata_pair(str(ctx.author), "groups", group)
    await ctx.send("Added {} to your groups, {}!".format(group, str(ctx.author)))

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
async def group_schedule(ctx, *, group: str):
    """
    Returns when everyone in the group is available to join
    """
    # check if the user and the group exist
    #
    # db_helpers.add_name("groups", group)
    # ctx.send("Added the group (if it didn't already exist).")
    result = helpers.schedule_group(group)
    msg = "You can schedule {} at these times today: \n".format(group)
    msg += helpers.stringify_can_join(result)
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
