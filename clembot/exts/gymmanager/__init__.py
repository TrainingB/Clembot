from .gym_manager_cog import GymManagerCog


def setup(bot):
    bot.add_cog(GymManagerCog(bot))
