import discord
from discord.ext import commands
import db_helpers
import helpers
import asyncio
import loadshedding_helpers

class Area(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def area(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("No command selected")

    @area.command()
    async def list(self, ctx):
        """
        List your areas, and potentially delete them
        """
        area_list = db_helpers.get_user_data(str(ctx.author.id), "areas")
        if len(area_list) == 0:
            await ctx.send("You have no areas assosciated with your username. Find one to add using \"?area_search\"")
            return
        else:
            message = "Here are your areas! Remove one by reacting with it's number.\n"
            for i in range(min(9, len(area_list))):
                message += helpers.UNICODE_INTS[i] + " " + area_list[i][0] + "\n"
            message_sent = await ctx.send(message)

            for i in range(min(9, len(area_list))):
                await message_sent.add_reaction(helpers.UNICODE_INTS[i])

            def check(reaction, user):
                if user == ctx.author:
                    return str(reaction.emoji)

            try:
                reaction_emoji, user = await self.bot.wait_for('reaction_add', timeout=helpers.TIMEOUT/2, check=check)
            except asyncio.TimeoutError:
                # if we timeout here, let's check if the user has already reacted before we get salty
                # await ctx.send("None of your areas have been removed")
                return
            else:
                try:
                    index_area_selected = helpers.UNICODE_INTS.index(str(reaction_emoji))
                    area_selected = area_list[index_area_selected][0]
                    db_helpers.remove_userdata_pair(
                        str(ctx.author.id), "areas", area_selected)
                    await ctx.send("Removed {} from your areas, {}!".format(area_selected, str(ctx.author)))
                except ValueError:
                    # User reacted with a bad emoji
                    return

    @area.command()
    async def search(self, ctx, *, area: str):
        """
        Search for an area. If it's found, you can add it to your areas.
        Adding an area to your profile also adds you to the implicit group "all"
        """
        # TODO: Could we make this neater?
        areas = loadshedding_helpers.find_area(area.upper().replace(" ", "+"))
        area_list = areas["areas"]
        if len(area_list) != 0:
            message = "I found the following areas! React with yours to add it to your profile.\n"
            for i in range(min(9, len(area_list))):
                area = area_list[i]
                message += helpers.UNICODE_INTS[i] + " " + area["name"] + " - " + area["region"] + "\n"
        else:
            message = "I found no areas matching {}, sorry!".format(area)
            await ctx.send(message)
            return

        message_sent = await ctx.send(message)
        # we've sent the message, now add the reactions
        if len(area_list) != 0:
            for i in range(min(9, len(area_list))):
                await message_sent.add_reaction(helpers.UNICODE_INTS[i])

        def check(reaction, user):
            if user == ctx.author:
                return str(reaction.emoji)

        try:
            reaction_emoji, user = await self.bot.wait_for('reaction_add', timeout=helpers.TIMEOUT, check=check)
        except asyncio.TimeoutError:
            # if we timeout here, let's check if the user has already reacted before we get salty
            cache_msg = discord.utils.get(self.bot.cached_messages, id=message_sent.id)
            for reaction in cache_msg.reactions:
                if reaction.count > 1:
                    try:
                        index_area_selected = helpers.UNICODE_INTS.index(str(reaction_emoji))
                        area_selected = area_list[index_area_selected]
                        db_helpers.insert_userdata_pair(
                            str(ctx.author.id), "areas", area_selected["id"])
                        await ctx.send("Added {} to your areas, {}!".format(area_selected["name"], str(ctx.author)))
                        return
                    except ValueError:
                        # something went horribly wrong
                        return
            await ctx.send("Timed out.")

        else:
            try:
                index_area_selected = helpers.UNICODE_INTS.index(str(reaction_emoji))
                area_selected = area_list[index_area_selected]
                db_helpers.insert_userdata_pair(
                    str(ctx.author.id), "areas", area_selected["id"])
                await ctx.send("Added {} to your areas, {}!".format(area_selected["name"], str(ctx.author)))
            except ValueError:
                # User reacted with a bad emoji
                return


async def setup(bot):
    await bot.add_cog(Area(bot))