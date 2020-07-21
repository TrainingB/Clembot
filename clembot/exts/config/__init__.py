from clembot.exts.config.cogs.config_cog import ConfigCog
from .channelconfigmanager import ChannelConfigCache
from .cogs.feature_management_cog import FeatureManagementCog
from .cogs.master_data_cog import MasterDataCog

def setup(bot):
    bot.add_cog(ChannelConfigCache(bot.dbi, bot))
    bot.add_cog(FeatureManagementCog(bot))
    bot.add_cog(ConfigCog(bot))
    bot.add_cog(MasterDataCog(bot))

