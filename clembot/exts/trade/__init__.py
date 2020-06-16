from .trademanager import TradeManager


def setup(bot):
    bot.add_cog(TradeManager(bot))


