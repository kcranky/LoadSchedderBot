from discord.ext import commands
import db_helpers
import helpers


class Timezone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def timezone(self, ctx):
        if ctx.invoked_subcommand is None:
            # TODO print help instead
            await ctx.send("No command selected")

    @timezone.command()
    async def set(self, ctx, *, timezone_str: str):
        if timezone_str is not None and helpers.is_timezone(timezone_str):
            # we can now add the timezone for the user
            db_helpers.set_user_timezone(str(ctx.author.id), timezone_str)
            await ctx.message.add_reaction('\N{THUMBS UP SIGN}')
        else:
            await ctx.send("Please enter a valid pytz timezone: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568")

    @timezone.command()
    async def get(self, ctx):
        result = db_helpers.get_user_timezone(str(ctx.author.id))
        if result is not None:
            msg = f"Your timezone is currently {result}."
        else:
            msg = "Your timezone is not set. You're currently using the default timezone."
        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Timezone(bot))
