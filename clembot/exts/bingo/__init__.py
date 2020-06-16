from .bingo_cog import BingoCog


def setup(bot):
    bot.add_cog(BingoCog(bot))
