from discord.ext import commands

from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.exts.raid.errors import RSVPNotEnabled, NotARaidChannel, NotARaidReportChannel
from clembot.exts.raid.raid import Raid, RaidParty

def _is_raid_channel(ctx):
    raid = Raid.by_channel.get(ctx.channel.id, None)
    if raid is not None:
        return True

    raise NotARaidChannel


def _is_raid_party_channel(ctx):
    raid = RaidParty.by_channel.get(ctx.channel.id, None)
    if raid is not None:
        return True

    raise NotARaidChannel

def _is_rsvp_enabled(ctx):

    is_raid = Raid.by_channel.get(ctx.channel.id, None)
    is_raid_party = RaidParty.by_channel.get(ctx.channel.id, None)

    if is_raid is None and is_raid_party is None:
        raise RSVPNotEnabled
    return True





def _is_raid_channel(ctx):
    raid = Raid.by_channel.get(ctx.channel.id, None)
    if raid:
        return True

    raise NotARaidChannel



async def _is_raid_report_channel(ctx):
    channel_data = await ChannelMetadata.find(ctx.bot, ctx.channel.id, ctx.guild.id)
    if channel_data and channel_data.get('raid', None):
        return True
    raise NotARaidReportChannel


def raid_channel():
    return commands.check(_is_raid_channel)

def raid_party_channel():
    return commands.check(_is_raid_party_channel)

def rsvp_enabled():
    return commands.check(_is_rsvp_enabled)

def raid_report_enabled():
    return commands.check(_is_raid_report_channel)