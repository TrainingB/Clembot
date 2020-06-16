from .profilemanager import ProfileManager


def setup(bot):
    bot.add_cog(ProfileManager(bot))

