from discord.ext.commands import Cog

from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds


class ErrorHandler(Cog):

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        Logger.error(error)
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
