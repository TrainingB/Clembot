from .profile_cog import ProfileCog


def setup(bot):
    bot.add_cog(ProfileCog(bot))

