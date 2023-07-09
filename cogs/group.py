import discord
from discord.ext import commands
import db_helpers
import helpers
import asyncio
import loadshedding_helpers

class Group(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("No command selected")

    @group.command()
    async def join(self, ctx, *, group: str):
        """
        Join a given group. Creates the group if it does not exist.
        Groups must be a single word/string.
        You are added to a group "all" by having an area assosciated with your username.
        """
        if group.count(" ") > 0:
            await ctx.send("Group names can't have spaces!")
            return
        if db_helpers.get_group_id(group.upper()) == -1:
            db_helpers.add_name("groups", group)
        db_helpers.insert_userdata_pair(str(ctx.author.id), "groups", group)
        await ctx.send("Added {} to your groups, {}!".format(group, str(ctx.author)))

    @group.command()
    async def list(self, ctx):
        """
        List your groups, and potentially delete them.
        You cannot remove yourself from the "all" group.
        """
        group_list = db_helpers.get_user_data(str(ctx.author.id), "groups")
        if len(group_list) == 0:
            ctx.send("You have no groups assosciated with your username. Create or join one!")
            return
        else:
            message = "Here are your groups! Remove one by reacting with it's number.\n"
            for i in range(min(9, len(group_list))):
                message += helpers.UNICODE_INTS[i] + " " + group_list[i][0] + "\n"
            message_sent = await ctx.send(message)

            for i in range(min(9, len(group_list))):
                await message_sent.add_reaction(helpers.UNICODE_INTS[i])

            def check(reaction, user):
                if user == ctx.author:
                    return str(reaction.emoji)

            try:
                reaction_emoji, user = await self.bot.wait_for('reaction_add', timeout=helpers.TIMEOUT/2, check=check)
            except asyncio.TimeoutError:
                # await ctx.send("None of your groups have been removed")
                # If nothing happens, then nothing happens. We don't need to tell the user that nothing happens
                pass
            else:
                try:
                    index_group_selected = helpers.UNICODE_INTS.index(str(reaction_emoji))
                    group_selected = group_list[index_group_selected][0]
                    group_id = db_helpers.get_group_id(group_selected)
                    db_helpers.remove_userdata_pair(str(ctx.author.id), "groups", group_selected)
                    msg = "Removed {} from your groups, {}!".format(group_selected, str(ctx.author))
                    # see if there are any more members in the group. If not, delete the group
                    if db_helpers.get_group_members(group_id) == -1:
                        db_helpers.remove_group(group_id)
                        msg += "\nYou were also the last member, so I removed the group, too."
                    await ctx.send(msg)
                except ValueError:
                    # User reacted with a bad emoji
                    return

    @group.command()
    async def list_all(self, ctx):
        """
        Returns all groups currently available
        """
        msg = ""
        groups = db_helpers.get_groups()
        if len(groups) > 0:
            for i, g in enumerate(groups):
                msg += "{}: {}\n".format(i + 1, g[0])
        else:
            msg = "No groups found! Add one with the \"?group create <group_name>\" command."
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Group(bot))