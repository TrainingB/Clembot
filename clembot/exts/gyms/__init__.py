from clembot.exts.gyms.citymanager import CityManager


def setup(bot):
    bot.add_cog(CityManager(bot))