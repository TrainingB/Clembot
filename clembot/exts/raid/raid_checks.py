from discord.ext import commands

from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.exts.raid.errors import RSVPNotEnabled, NotARaidChannel, NotARaidReportChannel
from clembot.exts.raid.raid import Raid, RaidParty


def _is_rsvp_enabled(ctx):
    raid = Raid.by_channel.get(ctx.channel.id, None)
    if raid:
        return True

    raid_party = RaidParty.by_channel.get(ctx.channel.id, None)
    if raid_party:
        return True

    raise RSVPNotEnabled


def _is_raid_channel(ctx):
    raid = Raid.by_channel.get(ctx.channel.id, None)
    if raid:
        return True

    raise NotARaidChannel



async def _is_raid_report_channel(ctx):
    channel_data = await ChannelMetadata.data(ctx.bot, ctx.channel.id)
    if channel_data['raid']:
        return True
    raise NotARaidReportChannel


def raid_channel():
    return commands.check(_is_raid_channel)

def rsvp_enabled():
    return commands.check(_is_rsvp_enabled)

def raid_report_enabled():
    return commands.check(_is_raid_report_channel)