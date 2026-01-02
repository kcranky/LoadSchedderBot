from discord.ext import commands
import db_helpers
import helpers
import configparser
import asyncio

config = configparser.ConfigParser()
config.read("config.ini")

class Timezone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def timezone(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @timezone.command()
    async def set(self, ctx, *, timezone_str: str):
        """
        Set a timezone for your user.
        Must be in pytz format: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
        """
        if timezone_str is not None and helpers.is_timezone(timezone_str):
            # we can now add the timezone for the user
            db_helpers.set_user_timezone(str(ctx.author.id), timezone_str)
            await ctx.message.add_reaction('\N{THUMBS UP SIGN}')
        else:
            await ctx.send("Please enter a valid pytz timezone: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568")

    @timezone.command()
    async def get(self, ctx):
        result = db_helpers.get_user_timezone(str(ctx.author.id))
        if result is None:
            msg = f"Your timezone is not set. You're currently using the default timezone of {config["Timezone"]["default"]}."
            await ctx.send(msg)
            return
        else:
            msg = f"Your timezone is currently {result}. \n React with {helpers.CROSS} to fall back to the default timezone of {config["Timezone"]["default"]}."

        message_sent = await ctx.send(msg)
        await message_sent.add_reaction(helpers.CROSS)

        def check(reaction, user):
            return (
                user == ctx.author
                and reaction.message.id == message_sent.id
                and str(reaction.emoji) == helpers.CROSS
            )

        try:
            await self.bot.wait_for(
                "reaction_add",
                timeout=helpers.TIMEOUT / 2,
                check=check,
            )
        except asyncio.TimeoutError:
            return
        else:
            db_helpers.remove_user_timezone(str(ctx.author.id))

            await ctx.send(
                f"Your timezone has been removed, {ctx.author.mention}. "
                f"You are now using the default timezone of {config['Timezone']['default']}."
            )

            await message_sent.delete()


async def setup(bot):
    await bot.add_cog(Timezone(bot))
