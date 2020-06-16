from .silph import Silph


def setup(bot):
    bot.add_cog(Silph(bot))
