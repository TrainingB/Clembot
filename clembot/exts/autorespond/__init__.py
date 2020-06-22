from .auto_response_cog import AutoResponseCog

def setup(bot):
    bot.add_cog(AutoResponseCog(bot))


