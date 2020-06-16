from .channelconfigmanager import ChannelConfigCache
from .channel_config_cog import ManagementCog
from .guild_config_cog import GuildConfigCog


def setup(bot):
    bot.add_cog(ChannelConfigCache(bot.dbi, bot))
    bot.add_cog(ManagementCog(bot))
    bot.add_cog(GuildConfigCog(bot))

