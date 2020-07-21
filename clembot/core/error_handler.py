from discord.ext.commands import Cog

from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds


class InvalidInputError(Exception):
    pass


class ErrorHandler(Cog):

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        Logger.error(f"{error.__type__} : {error}")
        return await Embeds.error(ctx.channel, f'{error}')


def setup(bot):
    bot.add_cog(ErrorHandler(bot))




