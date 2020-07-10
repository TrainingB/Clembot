from functools import wraps

import discord
from discord.ext.commands import Cog

from clembot.config.constants import Icons
from clembot.core.context import Context
from clembot.core.logs import Logger
from clembot.utilities.timezone import timehandler as TH
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.snowflake import CUIDGenerator


class InvalidInputError(Exception):
    pass


error_header = ["Alright, something happened.",
                "Hmmm, that didn't go as planned.",
                "Wow, That was unexpected.",
                "Are you sure this worked before?",
                "Enough, I need a break.",
                "Surprise, surprise!",
                "You broke me!"
                ]
error_message = ["I would love to say \"Hey, It's not you, its me!\" but that wouldn't change anything.",
    'You can try again or get on of the admins involved.',
    "Someone will spot the problem in due time.",
    "Don't read too much into this message and ask for help!",
    "You can try again but probably it wouldn't work unless someone takes a look at it.",
    "What else do you expect from a free bot!"
]



def wrap_error(func):
    """
    Decorator to handle logging of exception and sending an error message to the user.
    Need ctx object to send an error message to user. if ctx is not the second argument, specify which argument is ctx.
    """
    @wraps(func)
    async def decorator(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as error:
            import traceback
            ref_id = f"E-{CUIDGenerator.cuid(int(TH.current_epoch()))}"
            Logger.error(f"{ref_id} - {traceback.format_exc()}")

            ctx = next(filter(lambda arg: isinstance(arg, Context), args))

            if ctx:
                ctx.bot.loop.create_task(ctx.send(embed=Embeds.make_embed(
                    header_icon=Icons.bot_error, msg_color=discord.Color.dark_red(),
                    header=error_header[int(str(TH.current_epoch()).split(".")[-1]) % len(error_header)],
                    content=f'{error_message[int(str(TH.current_epoch()).split(".")[-1]) % len(error_message)]}\n\n||**Command:** `{ctx.message.content}`\n**Error:** `{error}`\n**Where:** `{func.__name__}()`||',
                    footer=f"Reference Id: {ref_id}")))
            return None

    return decorator



class ErrorHandler(Cog):

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        Logger.error(f"{error.__type__} : {error}")
        return await Embeds.error(ctx.channel, f'{error}')






    #
    #
    #
    # async def on_command_error(self, ctx, error):
    #
    #     if isinstance(error, discord.ext.commands.CheckFailure):
    #         return await Utilities.error(ctx.channel, f"{ctx.author.mention}, it seems like you don't have access to run this command.")
    #     elif isinstance(error, discord.ext.commands.CommandInvokeError):
    #         return await Utilities.error(ctx.channel, f'{error.original}')
    #



def setup(bot):
    bot.add_cog(ErrorHandler(bot))




