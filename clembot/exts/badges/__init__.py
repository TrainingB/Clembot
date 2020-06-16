from .badgemanager import BadgeManager


def setup(bot):
    bot.add_cog(BadgeManager(bot))



