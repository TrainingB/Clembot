from .autoresponder import AutoResponder

def setup(bot):
    bot.add_cog(AutoResponder(bot))


