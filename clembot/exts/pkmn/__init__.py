from .pokemon_cog import PokemonCog


def setup(bot):
    bot.add_cog(PokemonCog(bot))
