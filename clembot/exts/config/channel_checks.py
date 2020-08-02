from discord.ext import commands

from clembot.core.errors import NotAWildReportChannel, NotARaidReportChannel, NotANestReportChannel
from clembot.exts.config.channel_metadata import ChannelMetadata


async def _is_wild_report_channel(ctx):
    channel_data = await ChannelMetadata.find(ctx.bot, ctx.channel.id, ctx.guild.id)
    if channel_data and channel_data.get('wild', None):
        return True
    raise NotAWildReportChannel

async def _is_raid_report_channel(ctx):
    channel_data = await ChannelMetadata.find(ctx.bot, ctx.channel.id, ctx.guild.id)
    if channel_data and channel_data.get('raid', None):
        return True
    raise NotARaidReportChannel

async def _is_nest_report_channel(ctx):
    channel_data = await ChannelMetadata.find(ctx.bot, ctx.channel.id, ctx.guild.id)
    if channel_data and channel_data.get('nest', None):
        return True
    raise NotANestReportChannel


def raid_report_enabled():
    return commands.check(_is_raid_report_channel)


def wild_report_enabled():
    return commands.check(_is_wild_report_channel)


def nest_report_enabled():
    return commands.check(_is_nest_report_channel)