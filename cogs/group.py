import discord
from discord.ext import commands
import db_helpers
import helpers
import asyncio
import loadshedding_helpers
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

class Group(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @group.command()
    async def join(self, ctx, *, group: str):
        """
        Join a given group. Creates the group if it does not exist.
        Groups must be a single word/string.
        You are added to a group "all" by having an area assosciated with your username.
        """
        if any(char in group for char in config["GroupRules"]["unallowed_chars"]):
            await ctx.send(f"Group names cannot have the following characters: {config["GroupRules"]["unallowed_chars"]}")
            return
        if len(group) > int(config["GroupRules"]["max_length"]):
            await ctx.send(f"Group names must be shorter than {config["GroupRules"]["max_length"]} characters.")
            return
        if db_helpers.get_group_id(group.upper()) == -1:
            db_helpers.add_name("groups", group)
        db_helpers.insert_userdata_pair(str(ctx.author.id), "groups", group)
        await ctx.message.add_reaction('\N{THUMBS UP SIGN}')

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
        max_groups = min(len(group_list), len(helpers.LETTER_EMOJIS))
        message = "Here are your groups! Remove one by reacting with its letter.\n"

        for i in range(max_groups):
            message += f"{helpers.LETTER_EMOJIS[i]} {group_list[i][0]}\n"

        message_sent = await ctx.send(message)

        # Add reactions
        for i in range(max_groups):
            await message_sent.add_reaction(helpers.LETTER_EMOJIS[i])

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in helpers.LETTER_EMOJIS[:max_groups]

        try:
            reaction_emoji, user = await self.bot.wait_for(
                'reaction_add', timeout=helpers.TIMEOUT / 2, check=check
            )
        except asyncio.TimeoutError:
            pass  # User did not select anything
        else:
            index_group_selected = helpers.LETTER_EMOJIS.index(str(reaction_emoji))
            group_selected = group_list[index_group_selected][0]
            group_id = db_helpers.get_group_id(group_selected)
            db_helpers.remove_userdata_pair(
                str(ctx.author.id), "groups", group_selected)

            msg = f"Removed {group_selected} from your groups, {ctx.author}!"
            # Remove group if no more members
            if db_helpers.get_group_members(group_id) == -1:
                db_helpers.remove_group(group_id)
                msg += "\nYou were also the last member, so I removed the group, too."

            await ctx.send(msg)

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