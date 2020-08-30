from .pokebattler_cog import PokeBattlerCog


def setup(bot):
    bot.add_cog(PokeBattlerCog(bot))
