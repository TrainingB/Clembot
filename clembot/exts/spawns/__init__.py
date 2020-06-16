from .spawnmanager import SpawnManagerCog


def setup(bot):
    bot.add_cog(SpawnManagerCog(bot))