from .channelconfigmanager import ChannelConfigCache
from .cogs.channel_config_cog import ManagementCog
from clembot.exts.config.cogs.config_cog import ConfigCog


def setup(bot):
    bot.add_cog(ChannelConfigCache(bot.dbi, bot))
    bot.add_cog(ManagementCog(bot))
    bot.add_cog(ConfigCog(bot))

