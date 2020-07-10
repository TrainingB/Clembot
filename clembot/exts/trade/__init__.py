from .poke_form_cog import PokemonFormCog
from .trademanager import TradeManager


def setup(bot):
    bot.add_cog(PokemonFormCog(bot))
    bot.add_cog(TradeManager(bot))



